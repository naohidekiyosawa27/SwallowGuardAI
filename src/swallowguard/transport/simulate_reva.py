"""Deterministic memory transport experiment. No serial, patient data or hardware."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from swallowguard.transport.reva import Frame,Kind,Origin,encode,int24,StreamDecoder,SegmentGuard,link_budget
from swallowguard.transport.model_contract import REVA_RAW,mismatch_reasons

def experiment(seconds=10):
    if not isinstance(seconds,int) or not 1<=seconds<=120:raise ValueError('1..120 simulated seconds required')
    decoder=StreamDecoder();guard=SegmentGuard(17,Origin.SYNTHETIC)
    counts={k.name:0 for k in Kind};wire_bytes=0;frames=0;high_water=0
    last=None
    for tick in range(seconds*200):
        for kind,count,payload in [
            (Kind.ADC_PAIR,40,b''.join(int24((j+tick)%1000)+int24(-((j+tick)%1000)) for j in range(40))),
            (Kind.OPTICAL,1,bytes(6)),(Kind.IMU,1,bytes(12))]:
            frame=Frame(kind,Origin.SYNTHETIC,17,tick,tick*5000,count,125 if kind==Kind.ADC_PAIR else 5000,payload)
            raw=encode(frame);wire_bytes+=len(raw);last=frame
            for start in range(0,len(raw),17):
                received=decoder.feed(raw[start:start+17]);high_water=max(high_water,len(decoder.buffer))
                for got in received:
                    if not guard.ingest(got,parser_fault=decoder.fault):raise RuntimeError('Unexpected synthetic integrity failure')
                    counts[got.kind.name]+=got.count;frames+=1
    assert wire_bytes==link_budget()['bytes_per_second']*seconds
    assert guard.healthy(seconds*1000000)
    corrupted=bytearray(encode(last));corrupted[-1]^=1
    bad=StreamDecoder();received=bad.feed(corrupted+encode(replace(last,sequence=last.sequence+1,timestamp_us=last.timestamp_us+5000)))
    blocked=SegmentGuard(17,Origin.SYNTHETIC)
    fault_rejected=bool(bad.fault and len(received)==1 and not blocked.ingest(received[0],parser_fault=bad.fault))
    if not fault_rejected:raise RuntimeError('CRC fault did not remain blocked')
    return {'origin':'synthetic_memory_experiment','simulated_seconds':seconds,'frames_decoded':frames,
            'wire_bytes':wire_bytes,'sample_counts':counts,'parser_observed_high_water_bytes':high_water,
            'parser_declared_capacity_bytes':274,'healthy_complete_segment':True,
            'corruption_resync_retains_block':fault_rejected,'reva_to_d4_model_mismatches':list(mismatch_reasons(REVA_RAW)),
            'physical_uart_executed':False,'sensor_acquisition_executed':False,'clinical_outputs_enabled':False,
            'hardware_latency_ms':None,'link_budget':link_budget()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--seconds',type=int,default=10);a=p.parse_args()
    report=experiment(a.seconds);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
