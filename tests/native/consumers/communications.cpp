#include <modbus/modbus.h>
#include <mqtt/async_client.h>
#include <ZXing/MultiFormatWriter.h>
#include <ZXing/BitMatrix.h>
#include <ZXing/ReadBarcode.h>
#include <ZXing/ImageView.h>
#include <quill/Backend.h>
#include <quill/Frontend.h>
#include <quill/LogMacros.h>
#include <quill/sinks/ConsoleSink.h>
#include <stdexcept>
#include <cstdint>
#include <vector>
int main() {
    modbus_t* ctx=modbus_new_tcp("127.0.0.1",1502); if(!ctx) return 1; modbus_free(ctx);
    mqtt::async_client client("tcp://localhost:1883","sdk-local-test");
    if(client.is_connected()) return 2;
    auto matrix=ZXing::MultiFormatWriter(ZXing::BarcodeFormat::QRCode).encode("C++20 SDK",128,128);
    std::vector<uint8_t> pixels(128*128,255);
    for(int y=0;y<128;++y) for(int x=0;x<128;++x) pixels[y*128+x]=matrix.get(x,y)?0:255;
    auto barcode=ZXing::ReadBarcode(ZXing::ImageView(pixels.data(),128,128,ZXing::ImageFormat::Lum));
    if(!barcode.isValid()) throw std::runtime_error("ZXing round trip");
    quill::Backend::start();
    auto sink=quill::Frontend::create_or_get_sink<quill::ConsoleSink>("sdk-console");
    auto* logger=quill::Frontend::create_or_get_logger("sdk",sink);
    LOG_INFO(logger,"C++20 communications SDK passed"); logger->flush_log(); quill::Backend::stop();
}
