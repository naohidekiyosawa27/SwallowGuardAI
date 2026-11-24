#pragma once
#include "research_core.hpp"
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace sg {
// Numerical-domain check only. Passing it does NOT validate internal activation
// ranges, physiological quality, model performance or clinical safety.
struct QuantizationRange {
    float scale;
    int32_t zero_point;
    bool configured() const {
        return std::isfinite(scale) && scale>0 && zero_point>=-128 && zero_point<=127;
    }
    bool accepts(const float* values, size_t count) const {
        if(!configured() || !values || !count) return false;
        const double lower=(-128-zero_point)*static_cast<double>(scale);
        const double upper=(127-zero_point)*static_cast<double>(scale);
        for(size_t i=0;i<count;++i)
            if(!std::isfinite(values[i]) || values[i]<lower || values[i]>upper) return false;
        return true;
    }
};
inline ResearchDecision quantized_decision(bool physical_quality_valid,
                                           bool model_passed_validation,
                                           const float* input, size_t count,
                                           const QuantizationRange& range) {
    return decide(physical_quality_valid && range.accepts(input,count),model_passed_validation);
}
} // namespace sg
