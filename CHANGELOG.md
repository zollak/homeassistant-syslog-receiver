# Changelog

## [1.0.1] - 2025-05-13
### Added
- **`create_sensor` option**: Added a configuration option to allow users to store incoming syslog messages in a Home Assistant sensor (`sensor.syslog_receiver`). This option is useful for keeping the latest syslog message available for automations or UI, but may lead to database bloat if many messages are received.
- **Severity filtering**: Added the ability to filter syslog messages by severity level. The integration will now only process messages with severity levels 0–3 (critical or higher) by default.
- **IP filtering**: Introduced IP filtering for incoming syslog messages. The integration now checks if the sender's IP is allowed (configured via `allowed_ips`), rejecting messages from non-allowed IPs.

### Changed
- **Syslog message handling**: 
  - Syslog messages are now conditionally stored in a sensor if the `create_sensor` option is enabled, otherwise, they are only fired as events.
  - If `create_sensor` is enabled, the syslog messages will be stored as the state of `sensor.syslog_receiver`, which allows the latest message to be accessed for automations or dashboards.
  
### Fixed
- **Graceful server shutdown**: The `stop()` method is retained to ensure the syslog listener server is properly stopped when Home Assistant is unloaded or shut down. This method ensures the server is closed and resources are freed up.

## [1.0.3] - 2025-05-14
### Added
- Initial release of Syslog Receiver integration
- Support for UDP and TCP (with optional TLS) syslog input
- Configurable source IP and severity filters
- Event bus firing on received messages for automation triggers
- Optional sensor entities for last received message
- Full UI-based configuration and options flows
- Debug and error logging for troubleshooting

## [1.0.4] - 2025-05-14

First working version, but for 1 instance

### Fixed
 - all bug fixed that caused error during configuration, reconfiguration, reload service

## [1.0.5] - 2025-05-15

### Added
 - Reworked the integration for multiple instances and per-device naming.

You can now create one integration per device/protocol, name each entry (e.g. “NAS UDP” vs “Firewall TCP-TLS”), and have separate sensors.

## [1.0.6] - 2025-05-15

### Added
- Detailed README for example configuration, storage considerations, etc.

### Fixed
- TLS feature has fixed. Extend with certificate handling.

## [1.0.7] - 2025-05-18

### Added
- Added English translation
- Added validation for HACS
- Added hassfest validation 

## [1.0.8] - 2025-06-08

### Fixed
Fixed hacs.jason with removed country.

## [1.0.9] - 2025-06-09

Same as v1.0.8. 
Frist release in HACS.

## [1.1.0-beta] - 2025-07-01

### Added
- **IPv6**: bind on IPv6/dual‐stack sockets for UDP & TCP

## [1.1.0-beta2] - 2025-07-01

### Fixed
- Fix unload multiple platforms

## [1.1.0-beta3] - 2025-07-01

### Added
- Added protocol check

## [1.1.0-beta4] - 2025-07-01

### Fixed
- Fix protocol check

## [1.1.0-beta5] - 2025-07-02

### Added
- More logs in debug mode
- More usage examples

### Fixed
- Force the listener to bind on all available interfaces (IPv4 + IPv6)
- Syslog receiver instance is only created if a socket was bound successfully — which avoids silent failures and confusion.

## [1.1.0-beta6] - 2025-07-07

### Fixed
- Always use options before config - Thanks for @ivanfmartinez the [#PR2](https://github.com/zollak/homeassistant-syslog-receiver/pull/2)

## [1.1.0] - 2025-07-08

### Added
- IPv6 support

## [1.1.1] - 2025-07-08

### Added
- More error validation which:
  * Checks if `getaddrinfo()` returns empty result list.
  * Fails early with a clear error if no address is returned for binding.
  * Retains all original debug logs and functionality.
  * Makes the system safer against silent misconfiguration (especially in Docker, MacVLAN, or IPv6-only contexts).

## [1.1.2] - 2025-07-08

### Added
- Track Download counts in HACS