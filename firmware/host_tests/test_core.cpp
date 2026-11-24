#include "research_core.hpp"
#include "simulated_hal.hpp"
#include "quantization_guard.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>

int main() {
    sg::RingBuffer<int,2> r;
    int v=0;
    assert(!r.pop(v));assert(r.push(1));assert(r.push(2));assert(!r.push(3));
    assert(r.pop(v)&&v==1);assert(r.push(3));assert(r.pop(v)&&v==2);assert(r.pop(v)&&v==3);
    sg::QualityGate gate;
    assert(!gate.valid(0,15000));
    sg::SimulatedHAL hal;
    std::array<size_t,static_cast<size_t>(sg::Channel::Count)> counts{};
    for(uint64_t t=0;t<1000000;t+=125) hal.tick(t,[&](const sg::Sample& s) {
        ++counts[static_cast<size_t>(s.channel)];
        gate.ingest(s,sg::allowed_gap_us(s.channel));
    });
    assert(counts[static_cast<size_t>(sg::Channel::PVDF)]==8000);
    assert(counts[static_cast<size_t>(sg::Channel::EMG)]==2000);
    assert(counts[static_cast<size_t>(sg::Channel::Pressure)]==100);
    assert(counts[static_cast<size_t>(sg::Channel::OpticalX)]==200);
    assert(gate.valid(1000000,15000));assert(!gate.valid(2000000,15000));
    auto d=sg::decide(true,false);
    assert(std::strcmp(d.status,"invalid_measurement")==0);
    assert(!d.clinical_risk_enabled && !d.swallowing_safety_clearance);
    sg::Sample bad{1000000,999,0,sg::Channel::PVDF,sg::Source::Synthetic,true};
    gate.ingest(bad,188);assert(!gate.valid(1000000,15000));
    sg::QualityGate nonfinite;
    bad.value=std::numeric_limits<float>::quiet_NaN();nonfinite.ingest(bad,188);
    assert(!nonfinite.valid(1000000,15000));
    const sg::QuantizationRange range{0.5f,-10};
    const float good[]={-59.f,0.f,68.5f};
    const float overflow[]={-59.01f};
    const float nan[]={std::numeric_limits<float>::quiet_NaN()};
    assert(range.accepts(good,3));assert(!range.accepts(overflow,1));assert(!range.accepts(nan,1));
    assert(!range.accepts(nullptr,3));assert(!range.accepts(good,0));
    const sg::QuantizationRange invalid{0.f,0};assert(!invalid.accepts(good,3));
    const sg::QuantizationRange invalid_zero{1.f,128};assert(!invalid_zero.accepts(good,3));
    assert(std::strcmp(sg::quantized_decision(true,false,good,3,range).status,"invalid_measurement")==0);
    assert(std::strcmp(sg::quantized_decision(false,true,good,3,range).status,"invalid_measurement")==0);
    assert(std::strcmp(sg::quantized_decision(true,true,overflow,1,range).status,"invalid_measurement")==0);
    assert(std::strcmp(sg::quantized_decision(true,true,good,3,range).status,"research_event_only")==0);
    std::cout << "PASS: ring overflow/order, simulated rates, transport faults, numerical range/model validation guards, disabled clinical output\n";
}
