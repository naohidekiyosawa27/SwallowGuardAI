#pragma once
// Optional integration contract, NOT part of the simulator build. Requires an
// approved exported model + esp-tflite-micro + ESP-NN component on the target.
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"
#include <cstdint>

namespace sg {
class TFLMCandidate {
    tflite::MicroMutableOpResolver<6> resolver_;
    tflite::MicroInterpreter* interpreter_=nullptr;
public:
    TFLMCandidate() {
        resolver_.AddReshape();resolver_.AddConv2D();resolver_.AddMean();
        resolver_.AddFullyConnected();resolver_.AddLogistic();resolver_.AddConcatenation();
    }
    // Caller owns interpreter placement/lifetime and an aligned arena. Validate
    // SHA256, flatbuffer and the exported tensor manifest BEFORE GetModel().
    auto& resolver() {return resolver_;}
    bool attach(tflite::MicroInterpreter& interpreter) {
        interpreter_=&interpreter;
        if(interpreter_->AllocateTensors()!=kTfLiteOk) {interpreter_=nullptr;return false;}
        if(interpreter_->inputs_size()!=1 || interpreter_->outputs_size()!=1 ||
           interpreter_->input(0)->type!=kTfLiteInt8 || interpreter_->output(0)->type!=kTfLiteInt8) {
            interpreter_=nullptr;return false;
        }
        return true;
    }
    bool invoke() {return interpreter_ && interpreter_->Invoke()==kTfLiteOk;}
};
} // namespace sg
