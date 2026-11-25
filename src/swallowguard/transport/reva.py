"""Proposed Rev-A wire contract. Synthetic/bench only; no serial/register I/O.
Application CRC-32 is not ADS131M02 SPI CRC. Recovery never clears segment fault.
"""
from dataclasses import dataclass
from enum import IntEnum
import struct
import zlib

class Kind(IntEnum):
    ADC_PAIR=1
    OPTICAL=2
    IMU=3

class Origin(IntEnum):
    SYNTHETIC=0
    RESEARCH_REPLAY=1
    LIVE_BENCH=2

HEADER=struct.Struct('<2sBBHIIQIHH')
MAX_SAMPLES=40
MAX_PAYLOAD=240
MAX_FRAME=HEADER.size+MAX_PAYLOAD+4
STRIDE={Kind.ADC_PAIR:6,Kind.OPTICAL:6,Kind.IMU:12}
PERIOD={Kind.ADC_PAIR:125,Kind.OPTICAL:5000,Kind.IMU:5000}
QUALITY_MASK=0x3c

def integer(value,low,high):
    if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high:
        raise ValueError('Invalid integer field')

def int24(value):
    integer(value,-(1<<23),(1<<23)-1)
    return value.to_bytes(3,'little',signed=True)

def read_int24(data):
    if len(data)!=3:raise ValueError('Require exactly three signed ADC bytes')
    return int.from_bytes(data,'little',signed=True)

@dataclass(frozen=True)
class Frame:
    kind:Kind
    origin:Origin
    boot_id:int
    sequence:int
    timestamp_us:int
    count:int
    period_us:int
    payload:bytes
    quality_flags:int=0

    def validate(self):
        if not isinstance(self.kind,Kind) or not isinstance(self.origin,Origin):raise ValueError('Unknown kind/origin')
        for value in [self.boot_id,self.sequence]:integer(value,0,(1<<32)-1)
        integer(self.timestamp_us,0,(1<<64)-1);integer(self.count,1,MAX_SAMPLES)
        integer(self.period_us,1,(1<<32)-1);integer(self.quality_flags,0,QUALITY_MASK)
        if self.quality_flags&~QUALITY_MASK:raise ValueError('Reserved flags')
        if self.period_us!=PERIOD[self.kind] or (self.kind!=Kind.ADC_PAIR and self.count!=1):
            raise ValueError('Unapproved rate/batch profile')
        if not isinstance(self.payload,bytes) or len(self.payload)!=self.count*STRIDE[self.kind]:
            raise ValueError('Payload length/shape mismatch')
        if self.timestamp_us+self.count*self.period_us>(1<<64)-1:raise ValueError('Timestamp interval overflow')

def encode(frame):
    frame.validate()
    flags=int(frame.origin)|frame.quality_flags
    body=HEADER.pack(b'SG',1,int(frame.kind),flags,frame.boot_id,frame.sequence,
                     frame.timestamp_us,frame.period_us,frame.count,len(frame.payload))+frame.payload
    return body+struct.pack('<I',zlib.crc32(body))

def _header(data):
    magic,version,kind,flags,boot,seq,t0,period,count,length=HEADER.unpack(data[:HEADER.size])
    if magic!=b'SG' or version!=1 or flags&~0x3f or flags&3==3:raise ValueError('Invalid header')
    if length>MAX_PAYLOAD:raise ValueError('Oversized payload')
    frame=Frame(Kind(kind),Origin(flags&3),boot,seq,t0,count,period,bytes(length),flags&QUALITY_MASK)
    frame.validate()
    return frame,length

def decode(data):
    if not HEADER.size+4<=len(data)<=MAX_FRAME:raise ValueError('Invalid frame size')
    frame,length=_header(data)
    if len(data)!=HEADER.size+length+4:raise ValueError('Truncated/trailing frame bytes')
    expected=struct.unpack('<I',data[-4:])[0]
    if zlib.crc32(data[:-4])!=expected:raise ValueError('Application CRC-32 failure')
    return Frame(frame.kind,frame.origin,frame.boot_id,frame.sequence,frame.timestamp_us,
                 frame.count,frame.period_us,bytes(data[HEADER.size:-4]),frame.quality_flags)

class StreamDecoder:
    def __init__(self):
        self.buffer=bytearray();self.fault=False;self.errors=0
    def _reject(self):
        self.fault=True;self.errors+=1;del self.buffer[0]
    def expire_partial(self):
        if self.buffer:self.buffer.clear();self.fault=True;self.errors+=1
    def feed(self,data):
        frames=[]
        for value in data:
            self.buffer.append(value)
            while self.buffer:
                if self.buffer[0]!=ord('S') or (len(self.buffer)>1 and self.buffer[1]!=ord('G')):
                    self._reject();continue
                if len(self.buffer)<HEADER.size:break
                try:_,length=_header(self.buffer)
                except ValueError:self._reject();continue
                size=HEADER.size+length+4
                if len(self.buffer)<size:break
                try:frame=decode(bytes(self.buffer[:size]))
                except ValueError:self._reject();continue
                frames.append(frame);del self.buffer[:size]
            if len(self.buffer)>MAX_FRAME:raise RuntimeError('Internal bounded-parser invariant')
        return frames

class SegmentGuard:
    """Per-kind continuity; explicit boot/origin selection; no automatic reset."""
    def __init__(self,boot_id,origin):
        integer(boot_id,0,(1<<32)-1)
        if not isinstance(origin,Origin):raise ValueError('Unknown provenance')
        self.boot_id=boot_id;self.origin=origin;self.seen={};self.fault=False
    def ingest(self,frame,*,parser_fault=False):
        frame.validate()
        if parser_fault or frame.quality_flags or frame.boot_id!=self.boot_id or frame.origin!=self.origin:
            self.fault=True;return False
        previous=self.seen.get(frame.kind)
        if previous is not None and (frame.sequence!=((previous[0]+1)&0xffffffff) or frame.timestamp_us!=previous[1]):
            self.fault=True
        self.seen[frame.kind]=(frame.sequence,frame.timestamp_us+frame.count*frame.period_us)
        return not self.fault
    def healthy(self,now_head_us,*,stale_us=20000):
        integer(now_head_us,0,(1<<64)-1);integer(stale_us,0,(1<<64)-1)
        if self.fault or len(self.seen)!=3:return False
        return all(0<=now_head_us-(end-PERIOD[kind])<=stale_us for kind,(_,end) in self.seen.items())

def link_budget():
    rates={kind:200 for kind in Kind}
    counts={Kind.ADC_PAIR:40,Kind.OPTICAL:1,Kind.IMU:1}
    sizes={k:HEADER.size+counts[k]*STRIDE[k]+4 for k in Kind}
    bytes_per_second=sum(sizes[k]*rates[k] for k in Kind)
    return {'origin':'calculated_not_measured','uart_baud':2000000,'uart_bits_per_byte':10,
            'frame_bytes':{k.name:v for k,v in sizes.items()},'bytes_per_second':bytes_per_second,
            'line_utilization':bytes_per_second*10/2000000,
            'adc_block_interval_us':5000,'largest_frame_bytes':MAX_FRAME,
            'uart_payload_ring_100ms_bytes':bytes_per_second//10,
            'adc_two_second_packed_counts_bytes':8000*2*2*3,
            'clock_sync_control_log_overhead_included':False,'physical_link_verified':False}
