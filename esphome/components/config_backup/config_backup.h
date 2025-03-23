#pragma once

#include "esphome/core/component.h"
#include "esphome/components/web_server_base/web_server_base.h"
#include "config_embed.h"
#include "config-decrypt.h"

namespace esphome {
namespace config_backup {

class ConfigBackup : public esphome::Component, public AsyncWebHandler {
 public:
  explicit ConfigBackup(web_server_base::WebServerBase *base) : base_(base) {
    if (this->base_ != nullptr) {
      this->base_->add_handler(this);  // Add ourselves to the web server
    }
  }

  void setup() override {}
  void dump_config() override {}

  bool canHandle(AsyncWebServerRequest *request) override {
    return (request->url() == "/config.b64" || request->url() == "/config-decrypt.js") && request->method() == HTTP_GET;
  }

  void handleRequest(AsyncWebServerRequest *request) override {
    if(request->url() == "/config.b64"){
      request->getResponse()->addHeader("X-Encryption-Type","aes256");
      request->send(200, "text/plain", CONFIG_B64);
    } else if (request->url() == "/config-decrypt.js"){
      request->send(200, "application/javascript", CONFIG_DECRYPT_JS);
    }
  }

  bool isRequestHandlerTrivial() override { return true; }

 protected:
  web_server_base::WebServerBase *base_;
};

}  // namespace config_backup
}  // namespace esphome
