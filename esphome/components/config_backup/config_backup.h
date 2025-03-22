#pragma once

#include "esphome/core/component.h"
#include "esphome/components/web_server_base/web_server_base.h"
#include "config_embed.h"

namespace esphome {
namespace config_backup {

class ConfigDumpHandler : public AsyncWebHandler {
 public:
  bool canHandle(AsyncWebServerRequest *request) override {
    return request->url() == "/config.b64" && request->method() == HTTP_GET;
  }

  void handleRequest(AsyncWebServerRequest *request) override {
    request->send(200, "text/plain", CONFIG_B64);
  }

  bool isRequestHandlerTrivial() override { return true; }
};

class ConfigBackup : public Component {
 public:
  void setup() override {
    auto *server = web_server_base::get_web_server_base();
    if (server != nullptr) {
      server->add_handler(new ConfigDumpHandler());
    }
  }
};

}  // namespace config_backup
}  // namespace esphome
