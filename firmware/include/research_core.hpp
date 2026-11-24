#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <cmath>

namespace sg {
enum class Source : uint8_t { Synthetic, ResearchReplay, LiveBench };
enum class Channel : uint8_t { OpticalX, OpticalY, PVDF, EMG, Pressure,
                               Ax, Ay, Az, Gx, Gy, Gz, Count };
struct Sample {
    uint64_t t_us;
    uint32_t sequence;
    float value;
    Channel channel;
    Source source;
    bool valid;
};

// Single-thread ring. External mutex/critical section required across tasks.
template<typename T, size_t N> class RingBuffer {
    static_assert(N > 0, "Positive capacity required");
    std::array<T,N> data_{};
    size_t read_=0, write_=0, count_=0;
public:
    bool push(const T& v) {
        if (count_==N) return false; // reject overflow; never silently overwrite
        data_[write_]=v;write_=(write_+1)%N;++count_;return true;
    }
    bool pop(T& v) {
        if (!count_) return false;
        v=data_[read_];read_=(read_+1)%N;--count_;return true;
    }
    size_t size() const { return count_; }
};

class QualityGate {
    static constexpr size_t kChannels=static_cast<size_t>(Channel::Count);
    std::array<uint64_t,kChannels> last_{};
    std::array<uint32_t,kChannels> sequence_{};
    std::array<bool,kChannels> seen_{};
    bool fault_=false;
public:
    void ingest(const Sample& s, uint64_t max_gap_us) {
        auto c=static_cast<size_t>(s.channel);
        if(c>=kChannels || !s.valid || !std::isfinite(s.value)) {fault_=true;return;}
        if(seen_[c] && (s.t_us<=last_[c] || s.t_us-last_[c]>max_gap_us ||
                       s.sequence!=sequence_[c]+1)) fault_=true;
        last_[c]=s.t_us;sequence_[c]=s.sequence;seen_[c]=true;
    }
    bool valid(uint64_t now, uint64_t stale_us) const {
        if(fault_) return false;
        for(size_t c=0;c<kChannels;++c)
            if(!seen_[c] || now<last_[c] || now-last_[c]>stale_us) return false;
        return true;
    }
    void invalidate() {fault_=true;}
    // A fault requires a new acquisition segment and buffer reset by the caller.
};

struct ResearchDecision {
    const char* mode="RESEARCH MODE";
    const char* status="invalid_measurement";
    bool clinical_risk_enabled=false;
    bool swallowing_safety_clearance=false;
};
inline ResearchDecision decide(bool quality_valid, bool model_ready) {
    ResearchDecision d;
    if(quality_valid && model_ready) d.status="research_event_only";
    return d;
}
} // namespace sg
