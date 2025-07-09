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

## ℹ️ Notes for Docker & Container Users

If you run Home Assistant in Docker or similar containerized environments, especially with **MacVLAN**, there are a few important considerations:

- Setting **`Host` to `0.0.0.0`** means "bind on all available interfaces". On most systems this works, but in **MacVLAN or strict Docker networks**, `0.0.0.0` may **not resolve to usable interfaces** inside the container.
- If the syslog receiver does not appear to start or bind (nothing shows on `netstat -anu`), try:
  1. Setting the **container's actual IP address** in the Host field (e.g., `10.0.0.7`).
  2. Verifying that the port (e.g., `5514`) is **not used by another container** or service.
  3. Enabling **debug logging** for the integration to check bind failures.

```yaml
logger:
  logs:
    custom_components.syslog_receiver: debug
````

* You can find the container’s IP address using:

  ```bash
  docker exec -it homeassistant ip a
  ```
* Binding to `::` (for IPv6) may also work if your container is dual-stack enabled.

If the integration log shows:

```text
Could not bind UDP ('0.0.0.0', 5514): [Errno 99] Cannot assign requested address
```

…it means the bind failed. Use a valid, reachable IP instead.

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

---

### ✅ 1. Automation example: notify on critical syslog errors

```yaml
trigger:
  platform: event
  event_type: syslog_receiver_message
condition:
  condition: template
  value_template: "{{ trigger.event.data.severity <= 2 }}"
action:
  service: notify.mobile_app
  data:
    title: "[SYSLOG ERROR] {{ trigger.event.data.source_ip }}"
    message: "{{ trigger.event.data.message }}"
```
---

### ✅ 2. Log all messages from a specific device to file

```yaml
alias: "Log NAS syslog to file"
trigger:
  platform: event
  event_type: syslog_receiver_message
condition:
  condition: template
  value_template: "{{ trigger.event.data.source_ip == '10.10.10.50' }}"
action:
  - service: system_log.write
    data:
      level: info
      message: "NAS syslog: {{ trigger.event.data.message }}"
```

---

### ✅ 3. Send a persistent notification for login attempts

```yaml
alias: "Notify on SSH login attempt"
trigger:
  platform: event
  event_type: syslog_receiver_message
condition:
  - condition: template
    value_template: >-
      "sshd" in trigger.event.data.message and (
      "Accepted password" in trigger.event.data.message or
      "Accepted publickey" in trigger.event.data.message)
action:
  - service: persistent_notification.create
    data:
      title: "SSH Login Detected"
      message: >-
        From {{ trigger.event.data.source_ip }}:
        {{ trigger.event.data.message }}
```

---

### ✅ 4. Create a scene trigger for router firewall rule changes

```yaml
alias: "Firewall Rule Changed"
trigger:
  platform: event
  event_type: syslog_receiver_message
condition:
  condition: template
  value_template: >
    "filter rule changed" in trigger.event.data.message
action:
  - service: script.turn_on
    target:
      entity_id: script.notify_admin_change
```

---

### ✅ 5. Turn on a light if a physical door sensor logs a state

```yaml
alias: "Trigger light on syslog motion"
trigger:
  platform: event
  event_type: syslog_receiver_message
condition:
  condition: template
  value_template: >
    "Motion detected" in trigger.event.data.message
    and trigger.event.data.source_ip == "192.168.1.99"
action:
  - service: light.turn_on
    target:
      entity_id: light.garden_spotlight
```

---

### ✅ 6. Exclude debug messages from database (via sensor)

If you're using the optional sensor, you may want to exclude low-severity updates in `recorder:` config:

```yaml
recorder:
  exclude:
    entity_globs:
      - sensor.syslog_receiver_*
  # or keep it but purge quickly:
  purge_keep_days: 3
```

---

### ✅ 7. Enable the sensor in the integration options to add `sensor.syslog_receiver_<entry_id>`.

---

## Logging

Set Home Assistant logger level for `custom_components.syslog_receiver` to `debug` for detailed logs.

## Storage Considerations

Enabling the sensor for each syslog receiver instance creates a Home Assistant sensor entity that updates its state with every received message. Depending on volume, this can generate large amounts of state history and impact your database size and performance:

- **High-frequency logs** (e.g., dozens per second) will rapidly fill the recorder database with state changes.
- **Retention**: Adjust `recorder:` settings in `configuration.yaml` to limit history retention (e.g., `purge_keep_days`) or exclude the sensor entity entirely.
- **Alternatives**: If you only need event-based actions, consider leaving sensors disabled and using automations triggered on `syslog_receiver_message` events instead.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.