#pragma once
#include "esphome.h"
#include "config_embed.h"  // Your generated blob

namespace config_backup {

class ConfigBackup : public esphome::Component {
 public:
  void setup() override {
    if (esphome::web_server::global_web_server != nullptr) {
      esphome::web_server::global_web_server->add_handler("/config.b64", [](AsyncWebServerRequest *request) {
        request->send(200, "text/plain", CONFIG_B64);
      });
    }
  }
};

}  // namespace config_backup
