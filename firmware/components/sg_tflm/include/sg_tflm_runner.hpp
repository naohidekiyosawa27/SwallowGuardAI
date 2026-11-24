#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#if __has_include("tensorflow/lite/micro/schema/schema_generated.h")
#include "tensorflow/lite/micro/schema/schema_generated.h"
#else
#include "tensorflow/lite/schema/schema_generated.h"
#endif
#if __has_include("tensorflow/lite/version.h")
#include "tensorflow/lite/version.h"
#endif

namespace sg {
struct BenchInference {
    bool valid=false;
    float event_probability=0;
    int64_t invoke_us=0;
    size_t arena_used_bytes=0;
    bool clinical_risk_enabled=false;
};

// RESEARCH MODE. Caller must verify the model SHA256/identity against the
// selected artifact manifest before initialization; FlatBuffer verification
// validates structure, not origin. Model bytes and arena must outlive this runner.
// No embedded model, autonomous treatment or patient-risk endpoint is provided.
class ResearchTFLMRunner {
    tflite::MicroMutableOpResolver<5> resolver_;
    bool resolver_ok_=false;
    std::optional<tflite::MicroInterpreter> interpreter_;
    TfLiteTensor* input_=nullptr;
    TfLiteTensor* output_=nullptr;
public:
    ResearchTFLMRunner();
    bool ready() const {return interpreter_.has_value() && input_ && output_;}
    bool initialize(const unsigned char* data,size_t bytes,uint8_t* arena,size_t arena_bytes,
                    size_t expected_input_elements,bool numerical_model_passed,
                    bool artifact_identity_verified);
    BenchInference invoke_int8(const int8_t* values,size_t count,
                               bool physical_quality_valid,bool prequantization_range_valid);
};
} // namespace sg
