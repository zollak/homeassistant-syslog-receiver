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
