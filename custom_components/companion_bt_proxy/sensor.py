from homeassistant.components import sensor
from homeassistant.components.sensor import SensorStateClass
from homeassistant.util import dt
from homeassistant.helpers.entity import EntityCategory

from .constants import DOMAIN, TRACKED_DEVICES

import logging
_LOGGER = logging.getLogger(__name__)

RSSI_UNIT = "dBm"

async def async_setup_entry(hass, entry, async_setup_entities):
    scanner = entry.runtime_data
    entities = [_LastUpdate(scanner, entry)]
    entities.extend(_TrackedRssiSensor(scanner, entry, device) for device in TRACKED_DEVICES)
    async_setup_entities(entities)

class _LastUpdate(sensor.SensorEntity):

    def __init__(self, scanner, entry):

        self._attr_has_entity_name = True
        self._attr_unique_id = f"bt_proxy_{entry.entry_id}_last_update"
        self._attr_name = "Last Update"

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = sensor.SensorDeviceClass.TIMESTAMP

        scanner._sensors.append(self)

        self._attr_native_value = None
        self._entry_id = entry.entry_id
        self._device_name = entry.title

    async def async_on_scanner_update(self, scanner):
        self._attr_native_value = scanner.last_webhook_received or dt.now()
        payloadCount = scanner.last_payload_device_count
        attributes = {
            "payload_device_count": payloadCount,
            "scanner_status": "alive_no_devices" if payloadCount == 0 else "alive_with_devices",
            "canary_last_seen": scanner.canary_last_seen,
            "canary_available": scanner.canary_data is not None,
            "last_scan_status": scanner.last_scan_meta.get("status"),
            "last_scan_status_reason": scanner.last_scan_meta.get("status_reason"),
            "last_scan_started": scanner.last_scan_meta.get("scan_started"),
            "last_scan_finished": scanner.last_scan_meta.get("scan_finished"),
            "last_scan_permissions_granted": scanner.last_scan_meta.get("permissions_granted"),
            "last_scan_bluetooth_enabled": scanner.last_scan_meta.get("bluetooth_enabled"),
            "last_scan_total_devices_seen": scanner.last_scan_meta.get("total_devices_seen"),
            "last_scan_matched_device_count": scanner.last_scan_meta.get("matched_device_count"),
            "last_scan_bonded_device_count": scanner.last_scan_meta.get("bonded_device_count"),
            "last_scan_canary_seen": scanner.last_scan_meta.get("canary_seen"),
            "last_scan_mode": scanner.last_scan_meta.get("scan_mode"),
        }
        for device in TRACKED_DEVICES:
            slug = device["slug"]
            attributes[f"{slug}_last_seen"] = scanner.tracked_last_seen.get(slug)
            attributes[f"{slug}_available"] = scanner.tracked_data.get(slug) is not None
        self._attr_extra_state_attributes = attributes
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self._entry_id),
            },
            "name": self._device_name,
        }

class _TrackedRssiSensor(sensor.SensorEntity):
    def __init__(self, scanner, entry, device):
        self._slug = device["slug"]
        self._attr_unique_id = f"{self._slug}_rssi"
        self._attr_name = f"{device['label']} RSSI"
        self._attr_native_unit_of_measurement = RSSI_UNIT
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_available = False
        self._attr_extra_state_attributes = {}
        self._attr_native_value = None

        self._entry_id = entry.entry_id
        self._device_name = entry.title
        scanner._sensors.append(self)

    async def async_on_scanner_update(self, scanner):
        data = scanner.tracked_data.get(self._slug)
        last_seen = scanner.tracked_last_seen.get(self._slug)
        if data:
            self._attr_available = True
            self._attr_native_value = data["rssi"]
            self._attr_extra_state_attributes = {
                "source_address": data["source_address"],
                "source_name": data["source_name"],
                "last_seen": data["last_seen"],
                "matched_by": data["matched_by"],
                "scanner_last_webhook": scanner.last_webhook_received,
                "last_payload_device_count": scanner.last_payload_device_count,
            }
        else:
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "last_seen": last_seen,
                "scanner_last_webhook": scanner.last_webhook_received,
                "last_payload_device_count": scanner.last_payload_device_count,
            }
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self._entry_id),
            },
            "name": self._device_name,
        }
