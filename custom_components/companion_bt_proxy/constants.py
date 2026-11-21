DOMAIN = "companion_bt_proxy"
PLATFORMS = ["sensor"]

# Tracked devices, one entry per device.
#   slug:    stable key -> entity unique_id is "<slug>_rssi"
#   label:   entity friendly name prefix
#   address: Bluetooth address as seen by the Android scanner
#   name_fragment: optional advertised-name fallback (case-insensitive)
TRACKED_DEVICES = [
    {
        "slug": "cronje_phone",
        "label": "Cronje Phone",
        "address": "C4:16:8F:A0:0A:14",
        "name_fragment": None,
    },
    {
        "slug": "monica_phone",
        "label": "Monica Phone",
        "address": "29:17:5D:AB:4D:28",
        "name_fragment": None,
    },
]

CANARY_ADDR = "FC:E2:EC:43:74:43"
CANARY_NAME_FRAGMENT = "CHR68437443"
