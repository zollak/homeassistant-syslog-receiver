# Syslog Receiver for Home Assistant

This Home Assistant component listens for incoming syslog messages over UDP or TCP and can trigger automations or expose the messages via sensors.

## Features

- Receive syslog messages over UDP/TCP with optional TLS encryption.
- Filter incoming syslog messages based on the source IP address.
- Filter syslog messages by severity.
- Fire events on the Home Assistant event bus for automations
- Optional sensor entity to expose last received message
- UI-based setup and options flows (no YAML configuration)
- Comprehensive logging and debugging support

## Installation via HACS

1. Install the [HACS](https://hacs.xyz/) integration if you haven't already.
2. Go to the HACS store, click on the "Add Repository" button, and search for "Syslog Receiver".
3. Add the repository URL (`https://github.com/zollak/homeassistant-syslog-receiver`).
4. Install the integration.

## Configuration

1. Navigate to **Settings > Devices & Services > Integrations**.
2. Click **Add Integration**, search for **Syslog Receiver**.
3. Enter the host, port, protocol (UDP/TCP), TLS option, allowed IPs, minimum severity, and sensor toggle.
4. Save and start receiving syslog messages!

## Usage

Once configured, you can listen for `syslog_received` events:

- Listen for events `syslog_receiver_message` in automations:

  ```yaml
  trigger:
    platform: event
    event_type: syslog_receiver_message
  action:
    # use event.data.message, event.data.source_ip, event.data.severity
  ```
- Enable the sensor in the integration options to add `sensor.syslog_receiver_<entry_id>`.

## Logging

Set Home Assistant logger level for `custom_components.syslog_receiver` to `debug` for detailed logs.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.