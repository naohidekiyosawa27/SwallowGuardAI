#pragma once
#include <array>
#include <cstdint>
namespace sg {
enum class SignalIdentity:uint8_t {Missing,ThroatSound,UpperEMG,LowerEMG,PVDF,SingleEMG};
enum class InputDomain:uint8_t {D4v2,RevA};
enum class PreprocessingIdentity:uint8_t {D4R3Bounded,RawUncalibrated};
struct ModelInputContract {
    std::array<SignalIdentity,3> signals{};
    uint32_t sample_hz=0,window_samples=0;
    InputDomain domain=InputDomain::RevA;
    PreprocessingIdentity preprocessing=PreprocessingIdentity::RawUncalibrated;
};
inline ModelInputContract d4_r3_contract() {
    return {{{SignalIdentity::ThroatSound,SignalIdentity::UpperEMG,SignalIdentity::LowerEMG}},
            2000,4000,InputDomain::D4v2,PreprocessingIdentity::D4R3Bounded};
}
inline ModelInputContract reva_raw_contract() {
    return {{{SignalIdentity::PVDF,SignalIdentity::SingleEMG,SignalIdentity::Missing}},
            8000,16000,InputDomain::RevA,PreprocessingIdentity::RawUncalibrated};
}
inline bool model_input_matches(const ModelInputContract& actual,const ModelInputContract& required) {
    return actual.signals==required.signals && actual.sample_hz==required.sample_hz &&
        actual.window_samples==required.window_samples && actual.domain==required.domain &&
        actual.preprocessing==required.preprocessing;
}
// Metadata compatibility is necessary only, never clinical or physical-quality acceptance.
} // namespace sg
