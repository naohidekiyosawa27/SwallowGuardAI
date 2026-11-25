from dataclasses import replace
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
import zlib
from swallowguard.transport.reva import Frame,Kind,Origin,encode,decode,int24,read_int24,StreamDecoder,SegmentGuard,link_budget,MAX_FRAME,HEADER
from swallowguard.transport.model_contract import D4_R3,REVA_RAW,mismatch_reasons,require_compatible

def adc(**kwargs):
    args=dict(kind=Kind.ADC_PAIR,origin=Origin.SYNTHETIC,boot_id=17,sequence=0,
              timestamp_us=100000,count=40,period_us=125,
              payload=b''.join(int24(x)+int24(-x) for x in range(40)))
    args.update(kwargs);return Frame(**args)

class WireContract(unittest.TestCase):
    def test_signed24_extremes_and_overflow(self):
        for x in [-8388608,-1,0,1,8388607]:self.assertEqual(read_int24(int24(x)),x)
        for x in [-8388609,8388608,True,1.5]:
            with self.assertRaises(ValueError):int24(x)
        with self.assertRaises(ValueError):read_int24(b'xx')
    def test_canonical_crc_and_roundtrip(self):
        self.assertEqual(zlib.crc32(b'123456789'),0xcbf43926)
        f=adc();self.assertEqual(len(encode(f)),274);self.assertEqual(decode(encode(f)),f)
    def test_fragmentation_and_multiple_frames(self):
        frames=[adc(),adc(sequence=1,timestamp_us=105000)]
        stream=encode(frames[0])+encode(frames[1]);d=StreamDecoder();out=[]
        for byte in stream:out+=d.feed(bytes([byte]));self.assertLessEqual(len(d.buffer),MAX_FRAME)
        self.assertEqual(out,frames);self.assertFalse(d.fault)
    def test_corruption_resync_latches_invalidity(self):
        bad=bytearray(encode(adc()));bad[40]^=1
        d=StreamDecoder();out=d.feed(bytes(bad)+encode(adc(sequence=1,timestamp_us=105000)))
        self.assertEqual(len(out),1);self.assertTrue(d.fault)
        self.assertFalse(SegmentGuard(17,Origin.SYNTHETIC).ingest(out[0],parser_fault=d.fault))
    def test_garbage_bounded_and_recovers(self):
        d=StreamDecoder();self.assertEqual(d.feed(b'X'*10000+encode(adc())),[adc()])
        self.assertTrue(d.fault);self.assertEqual(len(d.buffer),0)
    def test_oversized_header_rejected_without_large_allocation(self):
        bad=bytearray(encode(adc()));bad[28:30]=b'\xff\xff'
        d=StreamDecoder();d.feed(bad[:HEADER.size]);self.assertTrue(d.fault)
        self.assertLessEqual(len(d.buffer),MAX_FRAME)
    def test_reserved_flags_and_version(self):
        for index,value in [(2,2),(4,3),(5,128)]:
            data=bytearray(encode(adc()));data[index]=value
            with self.assertRaises(ValueError):decode(bytes(data))
    def test_partial_timeout_latched(self):
        d=StreamDecoder();d.feed(encode(adc())[:10]);d.expire_partial()
        self.assertTrue(d.fault);self.assertEqual(d.buffer,b'')
    def test_duplicate_gap_and_backwards_time(self):
        for next_frame in [adc(),adc(sequence=2,timestamp_us=105000),adc(sequence=1,timestamp_us=104999)]:
            g=SegmentGuard(17,Origin.SYNTHETIC);self.assertTrue(g.ingest(adc()))
            self.assertFalse(g.ingest(next_frame));self.assertFalse(g.ingest(adc(sequence=1,timestamp_us=105000)))
    def test_wrap_is_valid_but_reset_origin_faults(self):
        g=SegmentGuard(17,Origin.SYNTHETIC);self.assertTrue(g.ingest(adc(sequence=0xffffffff)))
        self.assertTrue(g.ingest(adc(sequence=0,timestamp_us=105000)))
        for value in [adc(boot_id=18),adc(origin=Origin.LIVE_BENCH),adc(quality_flags=4)]:
            self.assertFalse(SegmentGuard(17,Origin.SYNTHETIC).ingest(value))
    def test_timestamp_overflow_and_wrong_rate_rejected(self):
        for value in [adc(timestamp_us=(1<<64)-2),adc(period_us=500),adc(payload=b'')]:
            with self.assertRaises(ValueError):encode(value)
    def test_all_streams_freshness_required(self):
        g=SegmentGuard(17,Origin.SYNTHETIC);g.ingest(adc());self.assertFalse(g.healthy(105000))
        for kind,size in [(Kind.OPTICAL,6),(Kind.IMU,12)]:
            g.ingest(Frame(kind,Origin.SYNTHETIC,17,0,100000,1,5000,bytes(size)))
        self.assertTrue(g.healthy(105000));self.assertFalse(g.healthy(99999));self.assertFalse(g.healthy(125001))
    def test_budget_counts_framing_and_uart_bits(self):
        r=link_budget();self.assertEqual(r['bytes_per_second'],72000)
        self.assertEqual(r['line_utilization'],.36);self.assertEqual(r['adc_two_second_packed_counts_bytes'],96000)
    def test_model_rejects_missing_or_duplicated_channels(self):
        self.assertEqual(len(mismatch_reasons(REVA_RAW)),5)
        with self.assertRaises(ValueError):require_compatible(REVA_RAW)
        with self.assertRaises(ValueError):require_compatible(replace(D4_R3,channels=('throat_sound','upper_emg','upper_emg')))
        with self.assertRaises(ValueError):require_compatible(replace(D4_R3,domain='prototype_RevA'))
        self.assertTrue(require_compatible(D4_R3))

class CppWireParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.exe=Path(cls.tmp.name)/'link_cli'
        root=Path(__file__).resolve().parents[1]
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pedantic','-fsanitize=undefined',
                        '-I',str(root/'firmware/include'),str(root/'firmware/host_tests/reva_link_cli.cpp'),'-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_cpp_generated_extreme_frame_decoded_in_python(self):
        raw=bytes.fromhex(subprocess.check_output([str(self.exe),'golden'],text=True).strip())
        value=decode(raw);self.assertEqual(value.boot_id,17);self.assertEqual(value.sequence,0xffffffff)
        self.assertEqual([read_int24(value.payload[j:j+3]) for j in range(0,6,3)],[-8388608,8388607])
    def test_python_random_frames_cpp_roundtrip_and_crc_rejection(self):
        rng=random.Random(2026)
        for index in range(30):
            count=rng.randrange(1,41)
            value=adc(sequence=index,count=count,payload=b''.join(int24(rng.randrange(-8388608,8388608)) for _ in range(count*2)))
            raw=encode(value)
            observed=subprocess.check_output([str(self.exe),raw.hex()],text=True).strip()
            self.assertEqual(observed,raw.hex())
        bad=bytearray(encode(adc()));bad[-1]^=1
        result=subprocess.run([str(self.exe),bytes(bad).hex()],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)

if __name__=='__main__':unittest.main()
