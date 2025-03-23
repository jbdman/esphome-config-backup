#pragma once

#include "esphome/core/component.h"
#include "esphome/core/defines.h"
#include "esphome/components/web_server_base/web_server_base.h"
#ifdef ESPHOME_CONFIG_BACKUP_GUI
  #include "config-decrypt.h"
  extern const uint8_t ESPHOME_WEBSERVER_INDEX_HTML[];
  extern const size_t ESPHOME_WEBSERVER_INDEX_HTML_SIZE;
#endif

extern const uint8_t CONFIG_B64[];
extern const size_t CONFIG_B64_SIZE;

namespace esphome {
namespace config_backup {

using namespace web_server_base;

#ifdef ESPHOME_CONFIG_BACKUP_GUI

class InjectMiddlewareHandler : public AsyncWebHandler {
 public:
  bool canHandle(AsyncWebServerRequest *request) override {
    return request->url() == "/" && request->method() == HTTP_GET;
  }

  void handleRequest(AsyncWebServerRequest *request) override {
    // Copy the PROGMEM HTML content into RAM
    std::string html((const char*)ESPHOME_WEBSERVER_INDEX_HTML, ESPHOME_WEBSERVER_INDEX_HTML_SIZE);
  
    // Find the insert point and inject script tag
    std::string script_tag = "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js\"></script>\n<script src=\"/config-decrypt.js\"></script>\n";
    size_t insert_pos = html.find("</body>");
    if (insert_pos != std::string::npos) {
      html.insert(insert_pos, script_tag);
    }
  
    // Send the modified HTML as normal response
    request->send(200, "text/html", html.c_str());
  }


  bool isRequestHandlerTrivial() override { return false; }
};

#endif

class ConfigBackup : public esphome::Component, public AsyncWebHandler {
 public:
  explicit ConfigBackup(WebServerBase *base) : base_(base) {
    if (this->base_ != nullptr) {
      // Order matters: add middleware before this handler
      #ifdef ESPHOME_CONFIG_BACKUP_GUI
        this->base_->add_handler(new InjectMiddlewareHandler());
      #endif
      this->base_->add_handler(this);
    }
  }

  void setup() override {}
  void dump_config() override {}

  void set_encryption(String encryption) {
    this->encryption = encryption;
  }

  bool canHandle(AsyncWebServerRequest *request) override {
    return (request->url() == "/config.b64" 
          #ifdef ESPHOME_CONFIG_BACKUP_GUI
            || request->url() == "/config-decrypt.js"
          #endif
           ) && request->method() == HTTP_GET;
  }

  void handleRequest(AsyncWebServerRequest *request) override {
    if (request->url() == "/config.b64") {
      AsyncWebServerResponse *response = request->beginResponse_P(200, "text/plain", CONFIG_B64, CONFIG_B64_SIZE);
      response->addHeader("X-Encryption-Type", this->encryption);
      request->send(response);
    }
    #ifdef ESPHOME_CONFIG_BACKUP_GUI 
    else if (request->url() == "/config-decrypt.js") {
      request->send(200, "application/javascript", CONFIG_DECRYPT_JS);
    }
    #endif
  }

  bool isRequestHandlerTrivial() override { return true; }

 protected:
  WebServerBase *base_;
  String encryption;
};

}  // namespace config_backup
}  // namespace esphome
