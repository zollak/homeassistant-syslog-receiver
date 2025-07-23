DOMAIN = "syslog_receiver"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 514
DEFAULT_PROTOCOL = "UDP"
DEFAULT_USE_TLS = False
DEFAULT_ALLOWED_IPS = ""
DEFAULT_MIN_SEVERITY = "info"
DEFAULT_INSTANCE_NAME = "Syslog Receiver"
DEFAULT_CERTFILE = ""
DEFAULT_KEYFILE = ""
MIN_SEVERITY_LEVELS = {
    "emerg": 0,
    "alert": 1,
    "crit": 2,
    "err": 3,
    "warning": 4,
    "notice": 5,
    "info": 6,
    "debug": 7
}
DEFAULT_ENCODING = "utf-8"
COMMON_ENCODINGS = [
    "utf-8",
    "latin1",
    "windows-1252",
    "ascii",
    "utf-16",
    "gbk",
    "big5",
    "Other…"
]