from __future__ import annotations
import concurrent.futures, queue, signal, threading, time
from dataclasses import dataclass
from .models import MaterializationStage, Result

@dataclass(frozen=True, slots=True)
class PipelineConfig:
    workers:int=6
    max_in_flight:int=24
    artifact_queue_size:int=32
    writer_batch_size:int=20
    progress_interval_seconds:float=5.0
    def validate(self):
        if self.workers < 1: raise ValueError("workers")
        if self.max_in_flight < self.workers: raise ValueError("max_in_flight")
        if self.artifact_queue_size < self.workers: raise ValueError("artifact_queue_size")
        if self.writer_batch_size < 1: raise ValueError("writer_batch_size")
        return self

class HighThroughputPipeline:
    def __init__(self,*,config,extract_one,write_batch,checkpoint_store,telemetry):
        self.config=config.validate()
        self.extract_one=extract_one
        self.write_batch=write_batch
        self.store=checkpoint_store
        self.telemetry=telemetry
        self.stop=threading.Event()
        self.artifacts=queue.Queue(maxsize=self.config.artifact_queue_size)
        self.results=[]
        self.writer_error=None

    def _writer(self):
        batch=[]
        while True:
            try: item=self.artifacts.get(timeout=.5)
            except queue.Empty:
                if self.stop.is_set() and self.artifacts.empty(): item=None
                else: continue
            if item is None:
                if batch: self._flush(batch)
                return
            batch.append(item)
            if len(batch) >= self.config.writer_batch_size:
                self._flush(batch); batch=[]

    def _flush(self,batch):
        started=time.monotonic()
        try: results=self.write_batch(batch)
        except BaseException as exc:
            self.writer_error=exc; self.stop.set()
            for a in batch:
                self.store.set_stage(a.candidate_id,MaterializationStage.VALIDATED,
                    "Writer batch aborted; reset for safe resume.")
            return
        self.telemetry.record_writer_batch(len(batch),time.monotonic()-started)
        self.results.extend(results)

    def run(self,items):
        writer=threading.Thread(target=self._writer,name="jarvis-x-a1-2-writer")
        writer.start()
        iterator=iter(items); futures={}; exhausted=False
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.workers) as ex:
                while not self.stop.is_set():
                    while not exhausted and len(futures) < self.config.max_in_flight:
                        try: item=next(iterator)
                        except StopIteration: exhausted=True; break
                        futures[ex.submit(self.extract_one,item)]=item
                    if not futures:
                        if exhausted: break
                        time.sleep(.05); continue
                    done,_=concurrent.futures.wait(tuple(futures),timeout=.25,
                        return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in done:
                        item=futures.pop(future)
                        try: artifact=future.result()
                        except BaseException as exc:
                            detail=f"{type(exc).__name__}: {exc}"
                            self.store.set_stage(item.candidate_id,MaterializationStage.FAILED,detail)
                            self.results.append(Result(item.candidate_id,item.path,
                                MaterializationStage.FAILED,detail))
                            continue
                        while not self.stop.is_set():
                            try:
                                self.artifacts.put(artifact,timeout=.25); break
                            except queue.Full:
                                self.telemetry.backpressure += 1
                    self.telemetry.maybe_emit(len(futures),self.artifacts.qsize())
        finally:
            self.artifacts.put(None); writer.join()
        if self.writer_error: raise self.writer_error
        return tuple(self.results)
