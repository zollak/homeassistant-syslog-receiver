# Syslog Receiver for Home Assistant

This Home Assistant component listens for incoming syslog messages and can trigger automations or expose the messages via sensors.

## Features

- Receive syslog messages from a specified host and port.
- Trigger automations based on received syslog messages.
- Optionally support TLS for encrypted syslog.
- Expose received messages as sensors within Home Assistant.

## Installation via HACS

1. Install the [HACS](https://hacs.xyz/) integration if you haven't already.
2. Go to the HACS store, and click on the "Add Repository" button.
3. Search for "Syslog Receiver" and add the repository URL (`https://github.com/yourusername/homeassistant-syslog-receiver`).
4. Install the integration.

## Configuration

Once the integration is installed, you need to configure it by adding it to your `configuration.yaml` or via the UI.

### YAML Configuration

```yaml
syslog_receiver:
  host: "0.0.0.0"  # The IP address of the receiver (use 0.0.0.0 for all interfaces)
  port: 514        # The port to listen on
  tls: true         # Set to true if you want to enable TLS
  username: "user"  # Optional: Provide a username
  password: "pass"  # Optional: Provide a password
```

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
  "message": "Your syslog message content"
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.