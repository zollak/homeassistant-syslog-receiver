# Syslog Receiver for Home Assistant

This Home Assistant component listens for incoming syslog messages over UDP or TCP and can trigger automations or expose the messages via sensors.

## Features

- Receive syslog messages over UDP or TCP (with optional TLS encryption).
- Filter incoming syslog messages based on the source IP address.
- Filter syslog messages by severity.
- Trigger automations based on received syslog messages.
- Expose received messages as sensors within Home Assistant.

## Installation via HACS

1. Install the [HACS](https://hacs.xyz/) integration if you haven't already.
2. Go to the HACS store, click on the "Add Repository" button, and search for "Syslog Receiver".
3. Add the repository URL (`https://github.com/zollak/homeassistant-syslog-receiver`).
4. Install the integration.

## Configuration

Once the integration is installed, you need to configure it by adding it to your `configuration.yaml` or via the UI.

### YAML Configuration Example

```yaml
syslog_receiver:
  host: "0.0.0.0"  # The IP address of the receiver (use 0.0.0.0 for all interfaces)
  port: 514        # The port to listen on
  tls: true         # Set to true if you want to enable TLS
  allowed_ips:
    - "192.168.1.10"  # IPs allowed to send syslog messages
  severity_level: 3   # Optional: Only process messages of this severity or higher
  create_sensor: true  # Enable sensor creation (warning: could increase database size)
```

#### Sensor Behavior

- If `create_sensor` is `True`, each received syslog message will be stored as a sensor with the entity ID `sensor.syslog_receiver`. This will store the message in Home Assistant's state machine. Be aware that storing many messages in this way may increase the size of the database over time.

- If `create_sensor` is `False`, the syslog message will only trigger events (`syslog_received`), but will not be stored in the state machine or the database.



### TLS Configuration

If you want to enable TLS (encrypted syslog), you can add the `tls` field in the configuration and provide your certificates:

```yaml
tls:
  certificate: "/path/to/cert.pem"
  private_key: "/path/to/private.key"
```

## Usage Example

Once configured, you can listen for `syslog_received` events:

```yaml
automation:
  - alias: "Syslog Message Trigger"
    trigger:
      platform: event
      event_type: "syslog_received"
    action:
      service: notify.notify
      data:
        message: "{{ trigger.event.data.message }}"
```

## Event Data

When a syslog message is received, an event `syslog_received` is fired with the following data:
```json
{
  "message": "Your syslog message content",
  "severity": 3  # Severity level of the syslog message
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.