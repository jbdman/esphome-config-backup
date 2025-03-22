#pragma once
#include "esphome/core/component.h"
#include "esphome/components/web_server/web_server.h"
#include "config_embed.h"

namespace esphome {
namespace config_backup {

class ConfigBackup : public Component {
 public:
  void setup() override {
    if (web_server::global_web_server != nullptr) {
      web_server::global_web_server->add_handler("/config.b64", [](AsyncWebServerRequest *request) {
        request->send(200, "text/plain", CONFIG_B64);
      });
    }
  }
};

}  // namespace config_backup
}  // namespace esphome
