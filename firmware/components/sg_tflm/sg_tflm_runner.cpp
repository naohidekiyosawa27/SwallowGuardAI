#include "sg_tflm_runner.hpp"
#include "esp_timer.h"
#include "flatbuffers/verifier.h"
#include <cmath>
#include <cstring>

namespace sg {
ResearchTFLMRunner::ResearchTFLMRunner() {
    resolver_ok_=resolver_.AddReshape()==kTfLiteOk && resolver_.AddConv2D()==kTfLiteOk &&
        resolver_.AddMean()==kTfLiteOk && resolver_.AddFullyConnected()==kTfLiteOk &&
        resolver_.AddLogistic()==kTfLiteOk;
}

bool ResearchTFLMRunner::initialize(const unsigned char* data,size_t bytes,uint8_t* arena,
                                  size_t arena_bytes,size_t expected_input_elements,
                                  bool numerical_model_passed,bool artifact_identity_verified) {
    input_=nullptr;output_=nullptr;interpreter_.reset();
    if(!resolver_ok_ || !numerical_model_passed || !artifact_identity_verified || !data ||
       !arena || bytes<8 || bytes>=100000 || !arena_bytes || !expected_input_elements ||
       reinterpret_cast<uintptr_t>(arena)%16) return false;
    flatbuffers::Verifier verifier(data,bytes);
    if(!tflite::VerifyModelBuffer(verifier)) return false;
    const auto* model=tflite::GetModel(data);
    if(model->version()!=TFLITE_SCHEMA_VERSION) return false;
    interpreter_.emplace(model,resolver_,arena,arena_bytes);
    if(interpreter_->AllocateTensors()!=kTfLiteOk || interpreter_->inputs_size()!=1 ||
       interpreter_->outputs_size()!=1) {interpreter_.reset();return false;}
    input_=interpreter_->input(0);output_=interpreter_->output(0);
    if(!input_ || !output_ || input_->type!=kTfLiteInt8 || output_->type!=kTfLiteInt8 ||
       input_->bytes!=expected_input_elements || output_->bytes!=1 ||
       !std::isfinite(input_->params.scale) || input_->params.scale<=0 ||
       !std::isfinite(output_->params.scale) || output_->params.scale<=0 ||
       input_->params.zero_point<-128 || input_->params.zero_point>127 ||
       output_->params.zero_point<-128 || output_->params.zero_point>127) {
        input_=nullptr;output_=nullptr;interpreter_.reset();return false;
    }
    return true;
}

BenchInference ResearchTFLMRunner::invoke_int8(const int8_t* values,size_t count,
                                            bool physical_quality_valid,bool prequantization_range_valid) {
    BenchInference result;
    if(!ready() || !values || count!=input_->bytes || !physical_quality_valid ||
       !prequantization_range_valid) return result;
    std::memcpy(input_->data.int8,values,count);
    const auto start=esp_timer_get_time();
    if(interpreter_->Invoke()!=kTfLiteOk) return result;
    result.invoke_us=esp_timer_get_time()-start;
    const float probability=(output_->data.int8[0]-output_->params.zero_point)*output_->params.scale;
    if(!std::isfinite(probability) || probability<0 || probability>1) return BenchInference{};
    result.event_probability=probability;result.valid=true;
    result.arena_used_bytes=interpreter_->arena_used_bytes();
    return result;
}
} // namespace sg
