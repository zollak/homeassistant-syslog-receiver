# Syslog Receiver integration for Home Assisstant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=zollak&repository=homeassistant-syslog-receiver&category=Integration)

This is a custom integration for Home Assistant which listens for incoming syslog messages over UDP, TCP, or TLS and can trigger automations via events or expose the messages via sensors.

## Features

- Receive syslog messages over UDP, TCP, or encrypted TCP (TLS)
- Filter incoming syslog messages based on the source IP address.
- Filter syslog messages by severity.
- Fire events on the Home Assistant event bus for automations
- Optional sensor entity to expose last received message
- UI-based setup and options flows (no YAML configuration)
- Comprehensive logging and debugging support

## Installation via HACS

1. Install the [HACS](https://hacs.xyz/) integration if you haven't already.
2. Go to the HACS store, search for **Syslog Receiver**, or click on the "Add Repository" button and add repository URL `https://github.com/zollak/homeassistant-syslog-receiver`.
3. Download, then **Restart Home Assistant**.

## Configuration

1. Navigate to **Settings > Devices & Services > Integrations**.
2. Click **Add Integration**, search for **Syslog Receiver**.
3. Enter the following fields:
   - **Instance Name**: A friendly name for this listener (entity name)
   - **Host**: IP address to bind (e.g., `0.0.0.0`, which means it binds on all interfaces on Home Assisstant server)
   - **Port**: Port number (e.g., `514`)
   - **Protocol**: `UDP`, `TCP`, or `TCP+TLS`
   - **Use TLS**: Enable encrypted connections
   - **Certfile**: Path to your server certificate (PEM file)
   - **Keyfile**: Path to your private key (PEM file)
   - **Allowed IPs**: Comma-separated list of source IPs to accept (e.g., `10.10.10.2,10.10.10.3,10.10.10.10`)
   - **Minimum Severity**: Syslog priority threshold
   - **Enable Sensors**: Create a sensor entity for last message
4. Save to start the syslog listener.

## Example Use Cases of Configuration

### IPv4 Support

- **UDP Plain Listener**
  - Host: `0.0.0.0`
  - Port: `514`
  - Protocol: `UDP`
  - Use TLS: `False`

- **TCP Plain Listener**
  - Host: `0.0.0.0`
  - Port: `514`
  - Protocol: `TCP`
  - Use TLS: `False`

- **TCP Encrypted (TLS) Listener**
  - Host: `0.0.0.0`
  - Port: `6514` (commonly used for TLS syslog)
  - Protocol: `TCP`
  - Use TLS: `True`
  - Certfile/Keyfile: Your TLS certificate and private key paths

- **Multiple Hosts/Subnets**
  - In **Allowed IPs**, list all source IPs or hosts on your subnet separated by commas:
    ```text
    10.10.10.2, 10.10.10.3, 10.10.10.4
    ```
  - Currently, subnet masks are not supported; enumerate each IP.

### IPv6 Support

This integration now supports binding on IPv6 interfaces in addition to IPv4. You can:

* **Bind to all IPv6 interfaces** using `::` as the Host.
* **Bind to a specific IPv6 address**, like `fe80::1`.
* Use both IPv4 and IPv6 simultaneously by using `::` on systems where dual-stack is enabled (i.e., it also accepts IPv4 on the same port).
* Add **IPv6 source addresses** to the Allowed IPs field (e.g., `fe80::1, 2001:db8::42`).

Make sure your Home Assistant system supports IPv6 binding and the ports used are open in the host firewall.

## TLS Setup

- **Server**: Provide a valid `certfile` and `keyfile` in the integration options. Home Assistant will load them on startup and bind an encrypted listener.
- **Client**: Configure your device to send syslog over TLS to the Home Assistant host and port. Ensure the client trusts the server certificate (install CA or disable validation).

If the cert/key are invalid or missing, the integration will log an error and fail to start.

### DTLS (UDP + TLS) Support

- **Not supported**: Native DTLS over UDP is not available in Python’s standard library. This integration can handle:
  1. **UDP** (plaintext)
  2. **TCP** (plaintext)
  3. **TCP + TLS** (encrypted)
- For **UDP + TLS** (DTLS), a third-party DTLS stack or custom implementation would be required, as the built-in `ssl` module does not provide DTLS.

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

## Storage Considerations

Enabling the sensor for each syslog receiver instance creates a Home Assistant sensor entity that updates its state with every received message. Depending on volume, this can generate large amounts of state history and impact your database size and performance:

- **High-frequency logs** (e.g., dozens per second) will rapidly fill the recorder database with state changes.
- **Retention**: Adjust `recorder:` settings in `configuration.yaml` to limit history retention (e.g., `purge_keep_days`) or exclude the sensor entity entirely.
- **Alternatives**: If you only need event-based actions, consider leaving sensors disabled and using automations triggered on `syslog_receiver_message` events instead.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.