from homeassistant.components import bluetooth
from homeassistant.util import dt
from datetime import datetime, timezone

from .constants import (
    TRACKED_DEVICES,
    CANARY_ADDR,
    CANARY_NAME_FRAGMENT,
)

import logging
import base64

_LOGGER = logging.getLogger(__name__)


class CompanionBLEScanner(bluetooth.BaseHaRemoteScanner):

    def __init__(self, hass, entry):
        self._connector = bluetooth.HaBluetoothConnector(client=None, source=entry.entry_id, can_connect=lambda: False)
        super().__init__(entry.entry_id, entry.title, self._connector, False)
        self._sensors = []
        # Per tracked-device state, keyed by slug: latest record and last-seen timestamp.
        self.tracked_data: dict[str, dict | None] = {d["slug"]: None for d in TRACKED_DEVICES}
        self.tracked_last_seen: dict[str, datetime | None] = {d["slug"]: None for d in TRACKED_DEVICES}
        self.canary_data = None
        self.canary_last_seen = None
        self.last_webhook_received = None
        self.last_payload_device_count = 0
        self.last_scan_meta = {}

    def _parse_meta_timestamp(self, timestamp_ms):
        if timestamp_ms in (None, ""):
            return None
        try:
            return datetime.fromtimestamp(float(timestamp_ms) / 1000.0, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

    def async_begin_webhook(self, device_count: int, scan_meta=None):
        self.last_webhook_received = dt.now()
        self.last_payload_device_count = device_count
        scan_meta = scan_meta or {}
        self.last_scan_meta = {
            "status": scan_meta.get("status"),
            "status_reason": scan_meta.get("status_reason"),
            "permissions_granted": scan_meta.get("permissions_granted"),
            "bluetooth_enabled": scan_meta.get("bluetooth_enabled"),
            "scan_started": self._parse_meta_timestamp(scan_meta.get("scan_started_timestamp")),
            "scan_finished": self._parse_meta_timestamp(scan_meta.get("scan_finished_timestamp")),
            "total_devices_seen": scan_meta.get("total_devices_seen"),
            "matched_device_count": scan_meta.get("matched_device_count"),
            "bonded_device_count": scan_meta.get("bonded_device_count"),
            "canary_seen": scan_meta.get("canary_seen"),
            "scan_mode": scan_meta.get("scan_mode"),
        }
        # Each webhook payload is treated as the full current snapshot.
        # Devices omitted from the payload are out of range and become unavailable.
        for slug in self.tracked_data:
            self.tracked_data[slug] = None
        self.canary_data = None

    async def async_process_json(self, data: dict):
        address = data["address"]
        name = data.get("name")

        for device in TRACKED_DEVICES:
            slug = device["slug"]
            matched_by = None
            if address == device["address"]:
                matched_by = "address"
            elif device["name_fragment"] and name and device["name_fragment"] in name:
                matched_by = "name"
            if not matched_by:
                continue
            seen_at = dt.now()
            self.tracked_data[slug] = {
                "rssi": data.get("rssi"),
                "source_address": address,
                "source_name": name,
                "last_seen": seen_at,
                "matched_by": matched_by,
            }
            self.tracked_last_seen[slug] = seen_at

        canary_name = (name or "").upper()
        if address == CANARY_ADDR or CANARY_NAME_FRAGMENT.upper() in canary_name:
            seen_at = dt.now()
            matched_by = "address" if address == CANARY_ADDR else "name"
            self.canary_data = {
                "rssi": data.get("rssi"),
                "source_address": address,
                "source_name": name,
                "last_seen": seen_at,
                "matched_by": matched_by,
            }
            self.canary_last_seen = seen_at

        service_data = {key: base64.b64decode(value) for (key, value) in data.get("service_data", {}).items()}
        m_data = {int(key, 10): base64.b64decode(value) for (key, value) in data.get("manufacturer_data", {}).items()}
        _LOGGER.debug(f"async_process_json: {data}, {service_data}, {m_data}")
        self._async_on_advertisement(
            address=data["address"],
            rssi=data.get("rssi", 0),
            local_name=data.get("name"),
            service_uuids=data.get("service_uuids", []),
            service_data=service_data,
            manufacturer_data=m_data,
            tx_power=data.get("tx_power", 0),
            details=dict(),
            advertisement_monotonic_time=data.get("timestamp", 0) / 1000, # Milliseconds to fractional seconds
        )

    async def async_update_sensors(self):
        for s in self._sensors:
            await s.async_on_scanner_update(self)

    async def async_load(self, hass):
        self._unload_callback = bluetooth.async_register_scanner(hass, self, False)

    async def async_unload(self, hass):
        self._unload_callback()
        self._sensors = []
