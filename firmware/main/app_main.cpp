#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "simulated_hal.hpp"
#include "quantization_guard.hpp"
#include "sg_tflm_runner.hpp"
#include <atomic>
#include <cstdlib>

static QueueHandle_t acquisition_queue;
static QueueHandle_t logging_queue;
static std::atomic<bool> transport_fault{false};
static constexpr char TAG[]="SWALLOWGUARD";

static void acquisition(void*) {
    sg::SimulatedHAL hal;
    uint64_t virtual_us=0;
    TickType_t last=xTaskGetTickCount();
    while(true) {
        // Synthetic virtual timestamps, generated in batches; not hardware timing evidence.
        for(int j=0;j<8;++j,virtual_us+=125) hal.tick(virtual_us,[](const sg::Sample& s) {
            if(xQueueSend(acquisition_queue,&s,0)!=pdTRUE) transport_fault=true;
        });
        vTaskDelayUntil(&last,pdMS_TO_TICKS(1));
    }
}

static void processing(void*) {
    sg::QualityGate quality;
    sg::Sample s{};
    uint64_t last_report=0;
    while(true) {
        if(xQueueReceive(acquisition_queue,&s,pdMS_TO_TICKS(20))!=pdTRUE) {
            quality.invalidate();
            ESP_LOGW(TAG,"RESEARCH MODE | invalid_measurement | acquisition timeout");
            continue;
        }
        quality.ingest(s,sg::allowed_gap_us(s.channel));
        if(transport_fault.load()) quality.invalidate();
        if(xQueueSend(logging_queue,&s,0)!=pdTRUE) {transport_fault=true;quality.invalidate();}
        if(s.t_us-last_report>=1000000) {
            last_report=s.t_us;
            auto d=sg::decide(quality.valid(s.t_us,15000),false);
            ESP_LOGI(TAG,"%s | synthetic virtual clock | %s | model_not_loaded",d.mode,d.status);
        }
        // Window DSP + actual TFLM invocation remain blocked on a verified model.
    }
}

static void logger(void*) {
    sg::Sample s{};
    uint64_t count=0;
    while(true) {
        if(xQueueReceive(logging_queue,&s,portMAX_DELAY)==pdTRUE) ++count;
        if(count && count%10000==0) ESP_LOGI(TAG,"synthetic samples consumed: %llu (SD not configured)",
                                          static_cast<unsigned long long>(count));
    }
}

extern "C" void app_main() {
#if !CONFIG_SWALLOWGUARD_SIMULATED
#error "Live drivers are blocked pending datasheet, schematic and safety review"
#endif
    // Link the audited five-operator TFLM/ESP-NN path. No model/arena is loaded;
    // real-device parity/latency tests require a reviewed bench setup.
    static sg::ResearchTFLMRunner bench_inference;
    if(bench_inference.ready()) std::abort();
    acquisition_queue=xQueueCreate(512,sizeof(sg::Sample));
    logging_queue=xQueueCreate(1024,sizeof(sg::Sample));
    if(!acquisition_queue || !logging_queue) std::abort();
    // Keep task-creation side effects outside assertions (which can be disabled).
    if(xTaskCreate(acquisition,"acquisition",4096,nullptr,8,nullptr)!=pdPASS) std::abort();
    if(xTaskCreate(processing,"processing",4096,nullptr,6,nullptr)!=pdPASS) std::abort();
    if(xTaskCreate(logger,"logger",4096,nullptr,3,nullptr)!=pdPASS) std::abort();
    ESP_LOGI(TAG,"RESEARCH MODE | synthetic | clinical outputs disabled");
}
