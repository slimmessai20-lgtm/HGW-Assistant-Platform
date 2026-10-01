import os

DEFAULT_TELNET_CONFIG = {
    "host":     os.environ.get("HGW_HOST",     "192.168.2.254"),
    "port":     int(os.environ.get("HGW_PORT",     "23")),
    "user":     os.environ.get("HGW_USER",     "root"),
    "password": os.environ.get("HGW_PASSWORD", "sah"),
}
