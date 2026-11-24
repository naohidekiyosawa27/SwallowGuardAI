#pragma once
#include "research_core.hpp"

namespace sg {
class SimulatedHAL {
    std::array<uint32_t,static_cast<size_t>(Channel::Count)> sequences_{};
public:
    // Call on a 125-us virtual bench clock. No physiological meaning.
    template<typename Sink> void tick(uint64_t t_us, Sink sink) {
        for(size_t c=0;c<static_cast<size_t>(Channel::Count);++c) {
            auto channel=static_cast<Channel>(c);
            uint64_t period=5000;
            if(channel==Channel::PVDF) period=125;
            if(channel==Channel::EMG) period=500;
            if(channel==Channel::Pressure) period=10000;
            if(t_us%period) continue;
            float value=static_cast<float>(std::sin(6.283185307179586*(1+c)*t_us/1000000.0));
            sink(Sample{t_us,sequences_[c]++,value,channel,Source::Synthetic,true});
        }
    }
};
inline uint64_t allowed_gap_us(Channel c) {
    if(c==Channel::PVDF) return 188;
    if(c==Channel::EMG) return 750;
    if(c==Channel::Pressure) return 15000;
    return 7500;
}
} // namespace sg
