#include "quantization_guard.hpp"
#include <iostream>
#include <vector>

int main() {
    float scale=0;
    int32_t zero_point=0;
    size_t count=0;
    while(std::cin>>scale>>zero_point>>count) {
        if(count>4096) return 2;
        std::vector<float> values(count);
        for(auto& value:values) if(!(std::cin>>value)) return 3;
        const sg::QuantizationRange range{scale,zero_point};
        std::cout<<(range.accepts(values.data(),values.size())?1:0)<<'\n';
    }
}
