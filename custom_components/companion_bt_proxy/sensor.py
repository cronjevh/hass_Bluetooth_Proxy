from homeassistant.components import sensor
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.util import dt
from homeassistant.helpers.entity import EntityCategory

from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

RSSI_UNIT = "dBm"

async def async_setup_entry(hass, entry, async_setup_entities):
    scanner = entry.runtime_data
    async_setup_entities([
        _LastUpdate(scanner, entry),
        _WatchRssiSensor(scanner, entry),
        _PhoneRssiSensor(scanner, entry),
    ])

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
        self._attr_extra_state_attributes = {
            "payload_device_count": payloadCount,
            "scanner_status": "alive_no_devices" if payloadCount == 0 else "alive_with_devices",
            "watch_last_seen": scanner.watch_last_seen,
            "phone_last_seen": scanner.phone_last_seen,
            "watch_available": scanner.watch_data is not None,
            "phone_available": scanner.phone_data is not None,
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

class _WatchRssiSensor(sensor.SensorEntity):
    def __init__(self, scanner, entry):
        self._attr_unique_id = "monica_watch_rssi"
        self._attr_name = "Monica Watch RSSI"
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
        if scanner.watch_data:
            self._attr_available = True
            self._attr_native_value = scanner.watch_data["rssi"]
            self._attr_extra_state_attributes = {
                "source_address": scanner.watch_data["source_address"],
                "source_name": scanner.watch_data["source_name"],
                "last_seen": scanner.watch_data["last_seen"],
                "matched_by": scanner.watch_data["matched_by"],
                "scanner_last_webhook": scanner.last_webhook_received,
                "last_payload_device_count": scanner.last_payload_device_count,
            }
        else:
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "last_seen": scanner.watch_last_seen,
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

class _PhoneRssiSensor(sensor.SensorEntity):
    def __init__(self, scanner, entry):
        self._attr_unique_id = "monica_phone_rssi"
        self._attr_name = "Monica Phone RSSI"
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
        if scanner.phone_data:
            self._attr_available = True
            self._attr_native_value = scanner.phone_data["rssi"]
            self._attr_extra_state_attributes = {
                "source_address": scanner.phone_data["source_address"],
                "source_name": scanner.phone_data["source_name"],
                "last_seen": scanner.phone_data["last_seen"],
                "matched_by": scanner.phone_data["matched_by"],
                "scanner_last_webhook": scanner.last_webhook_received,
                "last_payload_device_count": scanner.last_payload_device_count,
            }
        else:
            self._attr_available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "last_seen": scanner.phone_last_seen,
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
