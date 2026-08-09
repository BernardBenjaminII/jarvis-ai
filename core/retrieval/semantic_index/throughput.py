from __future__ import annotations
import os,time

def mem_available_gib():
    try:
        with open("/proc/meminfo","r",encoding="utf-8") as f:
            data={}
            for line in f:
                k,v=line.split(":",1)
                data[k]=v.strip()
        kb=int(data["MemAvailable"].split()[0])
        return kb/1024/1024
    except Exception:
        return None

def load1():
    try:
        return os.getloadavg()[0]
    except Exception:
        return None

def should_backpressure(*,max_load1=4.0,min_mem_gib=4.0):
    l=load1(); m=mem_available_gib()
    reasons=[]
    if l is not None and l>max_load1: reasons.append(f"load1>{max_load1}")
    if m is not None and m<min_mem_gib: reasons.append(f"mem<{min_mem_gib}GiB")
    return bool(reasons),reasons,{"load1":l,"mem_available_gib":m}

def sleep_backpressure(seconds=1.0):
    time.sleep(max(0.05,float(seconds)))
