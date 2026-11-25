#include "reva_link.hpp"
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
int main(int argc,char** argv) {
    using namespace sg::reva;
    if(argc!=2)return 2;
    Frame frame;
    if(std::string(argv[1])=="golden") {
        frame.boot_id=17;frame.sequence=0xffffffffu;frame.timestamp_us=100000;
        if(!put_int24(frame.payload.data(),-8388608) || !put_int24(frame.payload.data()+3,8388607))return 2;
    } else {
        std::string hex=argv[1];if(hex.size()%2 || hex.size()>max_frame*2)return 2;
        if(hex.find_first_not_of("0123456789abcdefABCDEF")!=std::string::npos)return 2;
        std::vector<uint8_t> bytes;
        for(size_t j=0;j<hex.size();j+=2)
            bytes.push_back(static_cast<uint8_t>(std::stoul(hex.substr(j,2),nullptr,16)));
        if(!decode(bytes.data(),bytes.size(),frame))return 2;
    }
    std::array<uint8_t,max_frame> output{};const size_t n=encode(frame,output.data(),output.size());
    if(!n)return 2;
    for(size_t j=0;j<n;++j)std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(output[j]);
    std::cout<<'\n';
}
