#pragma once

/**
 * @file config_backup.h
 * @brief Provides backup and retrieval of ESPHome configuration data, including optional injection
 *        of decryption scripts and middleware for a web-based interface.
 */

#include "esphome/core/component.h"
#include "esphome/core/defines.h"
#include "esphome/components/web_server_base/web_server_base.h"

#ifndef ESPHOME_CONFIG_BACKUP_NOJS
  /**
   * @brief JavaScript (GZipped) used to handle client-side decryption of configuration data.
   */
  extern const uint8_t CONFIG_DECRYPT_JS[];
  extern const size_t CONFIG_DECRYPT_JS_SIZE;
#endif

/**
 * @brief Base64-encoded (potentially GZipped) configuration data.
 */
extern const uint8_t CONFIG_B64[];
extern const size_t CONFIG_B64_SIZE;

namespace esphome {
namespace config_backup {

using namespace web_server_base;


/**
 * @class ConfigBackup
 * @brief Manages retrieval of the configuration data and optional decryption script via web server routes.
 */
class ConfigBackup : public esphome::Component, public AsyncWebHandler {
 public:
  /**
   * @brief Constructor that optionally attaches this handler (and the middleware) to the given web server base.
   * @param base A pointer to the WebServerBase instance. If valid, the handler is attached to it.
   */
  explicit ConfigBackup(WebServerBase *base) : base_(base) {
    if (this->base_ != nullptr) {
      this->base_->add_handler(this);
    }
  }

  /**
   * @brief Called during setup, but no special initialization is needed here.
   */
  void setup() override {}

  /**
   * @brief Prints diagnostic information during the ESPHome dump_config phase.
   */
  void dump_config() override {}

  /**
   * @brief Sets the encryption type (if any) used to secure the config backup.
   * @param encryption String describing the encryption method.
   */
  void set_encryption(String encryption) {
    this->encryption = encryption;
  }

  /**
   * @brief Determines if this handler can manage the incoming request for the config data
   *        (or the decryption script if GUI support is enabled).
   * @param request The incoming request object.
   * @return True if the URL matches the config backup path or the decrypt script path, and method is GET.
   */
  bool canHandle(AsyncWebServerRequest *request) override {
    return (
      request->url() == ESPHOME_CONFIG_BACKUP_CONFIG_PATH
      #ifndef ESPHOME_CONFIG_BACKUP_NOJS
        || request->url() == "/config-decrypt.js"
      #endif
    ) && request->method() == HTTP_GET;
  }

  /**
   * @brief Serves either the Base64-encoded config data or the config-decrypt.js script, depending on URL.
   * @param request The request to be served.
   */
  void handleRequest(AsyncWebServerRequest *request) override {
    // Serve the Base64-encoded config data
    if (request->url() == ESPHOME_CONFIG_BACKUP_CONFIG_PATH) {
      AsyncWebServerResponse *response = request->beginResponse_P(
        200, "text/plain", CONFIG_B64, CONFIG_B64_SIZE
      );

      // Indicate that the response is gzip-compressed
      response->addHeader("Content-Encoding", "gzip");

      // Include encryption metadata
      response->addHeader("X-Encryption-Type", this->encryption);

      //TODO: Change this to a string variable, this is frankly gross
      #ifdef ESPHOME_CONFIG_BACKUP_COMPRESS
        response->addHeader("X-Compression-Type", "gzip");
      #endif

      request->send(response);
    }

    #ifndef ESPHOME_CONFIG_BACKUP_NOJS
    // Serve the decryption script
    else if (request->url() == "/config-decrypt.js") {
      AsyncWebServerResponse *response = request->beginResponse_P(
        200, "application/javascript", CONFIG_DECRYPT_JS, CONFIG_DECRYPT_JS_SIZE
      );

      // Indicate gzip compression of the JavaScript
      response->addHeader("Content-Encoding", "gzip");
      request->send(response);
    }
    #endif
  }

  /**
   * @brief Marks this particular request handler as trivial (no further special handling needed).
   * @return True always.
   */
  bool isRequestHandlerTrivial() override { return true; }

 protected:
  WebServerBase *base_;  ///< Pointer to the main web server base.
  String encryption;      ///< Encryption method used for the config data.
};

}  // namespace config_backup
}  // namespace esphome
