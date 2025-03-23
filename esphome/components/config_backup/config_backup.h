#pragma once

#include "esphome/core/component.h"
#include "esphome/components/web_server_base/web_server_base.h"
#include "config_embed.h"
#include "config-decrypt.h"

extern const uint8_t ESPHOME_WEBSERVER_INDEX_HTML[];
extern const size_t ESPHOME_WEBSERVER_INDEX_HTML_SIZE;

namespace esphome {
namespace config_backup {

using namespace web_server_base;

class InjectMiddlewareHandler : public AsyncWebHandler {
 public:
  bool canHandle(AsyncWebServerRequest *request) override {
    return request->url() == "/" && request->method() == HTTP_GET;
  }

  void handleRequest(AsyncWebServerRequest *request) override {
    // Proxy the request to the next handler
    AsyncWebServerResponse *original_response = request->beginResponse_P(200, "text/html", ESPHOME_WEBSERVER_INDEX_HTML, ESPHOME_WEBSERVER_INDEX_HTML_SIZE);
    
    original_response->setContentProcessor([](const String &input) -> String {
      String modified = input;
      int insert_pos = modified.indexOf("</head>");
      if (insert_pos >= 0) {
        modified = modified.substring(0, insert_pos) +
                   "<script src=\"/config-decrypt.js\"></script>\n" +
                   modified.substring(insert_pos);
      }
      return modified;
    });

    request->send(original_response);
  }

  bool isRequestHandlerTrivial() override { return false; }
};

class ConfigBackup : public esphome::Component, public AsyncWebHandler {
 public:
  explicit ConfigBackup(WebServerBase *base) : base_(base) {
    if (this->base_ != nullptr) {
      // Order matters: add middleware before this handler
      this->base_->add_handler(new InjectMiddlewareHandler());
      this->base_->add_handler(this);
    }
  }

  void setup() override {}
  void dump_config() override {}

  void set_encryption(String encryption) {
    this->encryption = encryption;
  }

  bool canHandle(AsyncWebServerRequest *request) override {
    return (request->url() == "/config.b64" || request->url() == "/config-decrypt.js") &&
           request->method() == HTTP_GET;
  }

  void handleRequest(AsyncWebServerRequest *request) override {
    if (request->url() == "/config.b64") {
      AsyncWebServerResponse *response = request->beginResponse(200, "text/plain", CONFIG_B64);
      response->addHeader("X-Encryption-Type", this->encryption);
      request->send(response);
    } else if (request->url() == "/config-decrypt.js") {
      request->send(200, "application/javascript", CONFIG_DECRYPT_JS);
    }
  }

  bool isRequestHandlerTrivial() override { return true; }

 protected:
  WebServerBase *base_;
  String encryption;
};

}  // namespace config_backup
}  // namespace esphome
