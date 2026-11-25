#pragma once
// Proposed Rev-A framing only. No UART/GPIO/register initialization or model.
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace sg::reva {
constexpr size_t header_bytes=30,max_payload=240,max_frame=274;
enum class Kind:uint8_t {AdcPair=1,Optical=2,Imu=3};
enum class Origin:uint8_t {Synthetic=0,ResearchReplay=1,LiveBench=2};
struct Frame {
    Kind kind=Kind::AdcPair;
    Origin origin=Origin::Synthetic;
    uint16_t quality_flags=0;
    uint32_t boot_id=0,sequence=0;
    uint64_t timestamp_us=0;
    uint32_t period_us=125;
    uint16_t count=1,payload_bytes=6;
    std::array<uint8_t,max_payload> payload{};
};
inline uint32_t period(Kind k) {return k==Kind::AdcPair?125:5000;}
inline size_t stride(Kind k) {return k==Kind::Imu?12:6;}
inline uint64_t get_le(const uint8_t* p,size_t n) {
    uint64_t value=0;for(size_t j=0;j<n;++j)value|=uint64_t(p[j])<<(8*j);return value;
}
inline void put_le(uint8_t* p,uint64_t value,size_t n) {
    for(size_t j=0;j<n;++j)p[j]=static_cast<uint8_t>(value>>(8*j));
}
inline int32_t read_int24(const uint8_t* p) {
    const auto value=static_cast<uint32_t>(get_le(p,3));
    return static_cast<int32_t>(value&0x800000u?int64_t(value)-0x1000000:int64_t(value));
}
inline bool put_int24(uint8_t* p,int32_t value) {
    if(!p || value<-8388608 || value>8388607)return false;
    put_le(p,static_cast<uint32_t>(value),3);return true;
}
inline uint32_t crc32(const uint8_t* p,size_t n) {
    uint32_t value=0xffffffffu;
    for(size_t j=0;j<n;++j) {
        value^=p[j];for(unsigned bit=0;bit<8;++bit)value=(value>>1)^((value&1)?0xedb88320u:0u);
    }
    return value^0xffffffffu;
}
inline bool valid(const Frame& f) {
    const auto k=static_cast<unsigned>(f.kind),o=static_cast<unsigned>(f.origin);
    return k>=1 && k<=3 && o<=2 && !(f.quality_flags&~0x3cu) &&
        f.count>=1 && f.count<=40 && (f.kind==Kind::AdcPair || f.count==1) &&
        f.period_us==period(f.kind) && f.payload_bytes==f.count*stride(f.kind) &&
        f.payload_bytes<=max_payload &&
        f.timestamp_us<=std::numeric_limits<uint64_t>::max()-uint64_t(f.count)*f.period_us;
}
inline bool parse_header(const uint8_t* data,size_t bytes,Frame& f) {
    if(!data || bytes<header_bytes || data[0]!='S' || data[1]!='G' || data[2]!=1)return false;
    const uint16_t flags=static_cast<uint16_t>(get_le(data+4,2));
    if((flags&~0x3fu) || (flags&3)==3)return false;
    f.kind=static_cast<Kind>(data[3]);f.origin=static_cast<Origin>(flags&3);
    f.quality_flags=flags&0x3c;f.boot_id=static_cast<uint32_t>(get_le(data+6,4));
    f.sequence=static_cast<uint32_t>(get_le(data+10,4));f.timestamp_us=get_le(data+14,8);
    f.period_us=static_cast<uint32_t>(get_le(data+22,4));
    f.count=static_cast<uint16_t>(get_le(data+26,2));f.payload_bytes=static_cast<uint16_t>(get_le(data+28,2));
    return valid(f);
}
inline size_t encode(const Frame& f,uint8_t* data,size_t capacity) {
    const size_t size=header_bytes+f.payload_bytes+4;
    if(!valid(f) || !data || capacity<size)return 0;
    data[0]='S';data[1]='G';data[2]=1;data[3]=static_cast<uint8_t>(f.kind);
    put_le(data+4,static_cast<uint16_t>(f.origin)|f.quality_flags,2);
    put_le(data+6,f.boot_id,4);put_le(data+10,f.sequence,4);put_le(data+14,f.timestamp_us,8);
    put_le(data+22,f.period_us,4);put_le(data+26,f.count,2);put_le(data+28,f.payload_bytes,2);
    std::memcpy(data+header_bytes,f.payload.data(),f.payload_bytes);
    put_le(data+size-4,crc32(data,size-4),4);return size;
}
inline bool decode(const uint8_t* data,size_t bytes,Frame& f) {
    if(bytes>max_frame || bytes<header_bytes+4 || !parse_header(data,bytes,f))return false;
    if(bytes!=header_bytes+f.payload_bytes+4 || crc32(data,bytes-4)!=get_le(data+bytes-4,4))return false;
    std::memcpy(f.payload.data(),data+header_bytes,f.payload_bytes);return true;
}
class StreamDecoder {
    std::array<uint8_t,max_frame> buffer_{};
    size_t size_=0;
    bool fault_=false;
    uint64_t errors_=0;
    void drop(size_t n) {std::memmove(buffer_.data(),buffer_.data()+n,size_-n);size_-=n;}
    void reject() {fault_=true;++errors_;drop(1);}
public:
    bool fault() const {return fault_;}
    size_t buffered() const {return size_;}
    uint64_t errors() const {return errors_;}
    void expire_partial() {if(size_){size_=0;fault_=true;++errors_;}}
    template<typename Sink> void feed(const uint8_t* data,size_t bytes,Sink sink) {
        if(!data && bytes){fault_=true;++errors_;return;}
        for(size_t j=0;j<bytes;++j) {
            if(size_==max_frame){fault_=true;++errors_;size_=0;}
            buffer_[size_++]=data[j];
            while(size_) {
                if(buffer_[0]!='S' || (size_>1 && buffer_[1]!='G')){reject();continue;}
                if(size_<header_bytes)break;
                Frame f;
                if(!parse_header(buffer_.data(),size_,f)){reject();continue;}
                const size_t expected=header_bytes+f.payload_bytes+4;
                if(size_<expected)break;
                if(!decode(buffer_.data(),expected,f)){reject();continue;}
                sink(f);drop(expected);
            }
        }
    }
};
class SegmentGuard {
    uint32_t boot_;
    Origin origin_;
    bool fault_=false;
    std::array<bool,3> seen_{};
    std::array<uint32_t,3> seq_{};
    std::array<uint64_t,3> end_{};
public:
    SegmentGuard(uint32_t boot,Origin origin):boot_(boot),origin_(origin) {
        if(static_cast<unsigned>(origin)>2)fault_=true;
    }
    bool ingest(const Frame& f,bool parser_fault=false) {
        if(!valid(f) || parser_fault || f.quality_flags || f.boot_id!=boot_ || f.origin!=origin_) {
            fault_=true;return false;
        }
        const size_t k=static_cast<size_t>(f.kind)-1;
        if(seen_[k] && (f.sequence!=static_cast<uint32_t>(seq_[k]+1) || f.timestamp_us!=end_[k]))fault_=true;
        seen_[k]=true;seq_[k]=f.sequence;end_[k]=f.timestamp_us+uint64_t(f.count)*f.period_us;
        return !fault_;
    }
    bool healthy(uint64_t now,uint64_t stale=20000) const {
        if(fault_)return false;
        for(size_t k=0;k<3;++k) {
            if(!seen_[k])return false;
            const uint64_t last=end_[k]-period(static_cast<Kind>(k+1));
            if(now<last || now-last>stale)return false;
        }
        return true;
    }
};
inline bool synthetic_contract_selfcheck() {
    Frame frame;frame.boot_id=17;
    std::array<uint8_t,max_frame> bytes{};
    const size_t size=encode(frame,bytes.data(),bytes.size());
    StreamDecoder decoder;size_t seen=0;
    decoder.feed(bytes.data(),size,[&](const Frame& value){
        if(value.origin==Origin::Synthetic && value.boot_id==17 && value.count==1)++seen;
    });
    return size==40 && seen==1 && !decoder.fault() && !decoder.buffered();
}
} // namespace sg::reva
