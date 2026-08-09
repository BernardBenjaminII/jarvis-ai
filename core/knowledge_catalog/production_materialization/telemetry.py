from __future__ import annotations
import os,time
class PipelineTelemetry:
    def __init__(self,store,runtime_counts,interval=5.0):
        self.store=store; self.runtime_counts=runtime_counts; self.interval=interval
        self.last=0; self.writer_batches=0; self.writer_docs=0; self.writer_seconds=0.; self.backpressure=0
    def record_writer_batch(self,documents,elapsed):
        self.writer_batches+=1; self.writer_docs+=documents; self.writer_seconds+=elapsed
    def maybe_emit(self,in_flight,artifact_q):
        now=time.monotonic()
        if now-self.last < self.interval: return
        self.last=now
        try: load=os.getloadavg()[0]
        except OSError: load=0.
        mem="?"
        try:
            for line in open("/proc/meminfo"):
                if line.startswith("MemAvailable:"):
                    mem=f"{int(line.split()[1])/1024/1024:.1f}GiB"; break
        except Exception: pass
        rate=self.writer_docs/self.writer_seconds if self.writer_seconds else 0.
        print(f"[X-A1.2] in_flight={in_flight} artifact_q={artifact_q} "
              f"writer_batches={self.writer_batches} writer_docs={self.writer_docs} "
              f"writer_rate={rate:.2f}/s backpressure={self.backpressure} "
              f"load1={load:.2f} mem_avail={mem}",flush=True)
