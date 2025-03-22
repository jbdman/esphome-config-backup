#include "esphome.h"
#include "web_server/web_server.h"
#include "config_embed.h"

class ConfigBackup : public esphome::Component {
 public:
  void setup() override {
    esphome::web_server::WebServer *web = esphome::web_server::global_web_server;
    if (web) {
      web->add_handler("/config.b64", [](AsyncWebServerRequest *request) {
        request->send(200, "text/plain", CONFIG_B64);
      });
    }
  }
};
