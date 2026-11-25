#include "reva_link.hpp"
#include "model_input_contract.hpp"
#include <cassert>
#include <iostream>
#include <string>
int main() {
    using namespace sg::reva;
    assert(synthetic_contract_selfcheck());
    const std::string standard="123456789";
    assert(crc32(reinterpret_cast<const uint8_t*>(standard.data()),standard.size())==0xcbf43926u);
    Frame f;f.boot_id=17;f.count=40;f.payload_bytes=240;f.timestamp_us=100000;
    assert(put_int24(f.payload.data(),-8388608));assert(put_int24(f.payload.data()+3,8388607));
    assert(!put_int24(f.payload.data()+6,8388608));
    assert(read_int24(f.payload.data())==-8388608 && read_int24(f.payload.data()+3)==8388607);
    std::array<uint8_t,max_frame> bytes{};const size_t n=encode(f,bytes.data(),bytes.size());assert(n==274);
    assert(!encode(f,bytes.data(),100));Frame copy;assert(decode(bytes.data(),n,copy));
    StreamDecoder stream;size_t emitted=0;
    for(size_t j=0;j<n;++j)stream.feed(bytes.data()+j,1,[&](const Frame& got){assert(got.count==40);++emitted;});
    assert(emitted==1 && !stream.fault() && !stream.buffered());
    bytes[45]^=1;stream.feed(bytes.data(),n,[&](const Frame&){++emitted;});
    assert(stream.fault() && emitted==1);
    bytes[45]^=1;stream.feed(bytes.data(),n,[&](const Frame&){++emitted;});assert(emitted==2 && stream.fault());
    StreamDecoder truncated;truncated.feed(bytes.data(),10,[](const Frame&){});truncated.expire_partial();
    assert(truncated.fault() && !truncated.buffered());
    StreamDecoder garbage;
    const uint8_t x='X';for(unsigned j=0;j<10000;++j)garbage.feed(&x,1,[](const Frame&){});
    assert(garbage.fault() && !garbage.buffered());
    SegmentGuard guard(17,Origin::Synthetic);assert(guard.ingest(f));assert(!guard.healthy(105000));
    for(Kind k:{Kind::Optical,Kind::Imu}) {
        Frame other;other.kind=k;other.boot_id=17;other.timestamp_us=100000;other.period_us=5000;
        other.payload_bytes=static_cast<uint16_t>(stride(k));assert(guard.ingest(other));
    }
    assert(guard.healthy(105000));assert(!guard.healthy(99999));assert(!guard.healthy(125001));
    assert(!guard.ingest(f));assert(!guard.healthy(105000));
    SegmentGuard wrap(17,Origin::Synthetic);f.sequence=0xffffffffu;assert(wrap.ingest(f));
    f.sequence=0;f.timestamp_us+=5000;assert(wrap.ingest(f));
    SegmentGuard changed(17,Origin::Synthetic);f.boot_id=18;assert(!changed.ingest(f));
    Frame overflow;overflow.timestamp_us=std::numeric_limits<uint64_t>::max()-1;assert(!valid(overflow));
    assert(!sg::model_input_matches(sg::reva_raw_contract(),sg::d4_r3_contract()));
    assert(sg::model_input_matches(sg::d4_r3_contract(),sg::d4_r3_contract()));
    std::cout<<"PASS: Rev-A framing/CRC/resync/bounds/session/rate/clock/contract guards (synthetic only)\n";
}
