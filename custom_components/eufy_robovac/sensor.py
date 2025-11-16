from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN
from .coordinators import EufyTuyaDataUpdateCoordinator
from .mixins import CoordinatorTuyaDeviceUniqueIDMixin


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    discovered_devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DISCOVERED_DEVICES]

    devices = []

    for device_id, props in discovered_devices.items():
        coordinator = props[CONF_COORDINATOR]
        
        # Always add battery sensor (S1 Pro uses DPS 8)
        devices.append(BatteryPercentageSensor(coordinator=coordinator))
        
        # Add cleaning mode sensor - now uses DPS 154 and 10 instead of DPS 5
        devices.append(CleaningModeSensor(coordinator=coordinator))
        
        # Add fan speed sensor (DPS 9)
        devices.append(
            FanSpeedSensor(
                name="Fan Speed",
                icon="mdi:fan",
                dps_id="9",
                coordinator=coordinator,
            )
        )
        
        # Add running status sensor (DPS 2)
        devices.append(
            RunningStatusSensor(
                name="Running Status",
                icon="mdi:play-pause",
                dps_id="2",
                coordinator=coordinator,
            )
        )

    if devices:
        return async_add_devices(devices)


class BaseDPSensorEntity(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, SensorEntity):
    
    def __init__(
        self,
        *args,
        name: str,
        icon: str | None,
        dps_id: str,
        coordinator: EufyTuyaDataUpdateCoordinator,
        **kwargs,
    ):
        self._attr_name = name
        self._attr_icon = icon
        self.dps_id = dps_id
        super().__init__(*args, coordinator=coordinator, **kwargs)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and self.dps_id in self.coordinator.data

    @property
    def native_value(self):
        if self.coordinator.data:
            value = self.coordinator.data.get(self.dps_id)
            if converter := getattr(self, "parse_value", None):
                try:
                    return converter(value)
                except Exception:
                    return value
            return value
        return None


class BatteryPercentageSensor(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Battery"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and ("8" in self.coordinator.data or "163" in self.coordinator.data)

    @property
    def icon(self) -> str:
        # Check if charging based on DPS 5 (mode)
        mode = (self.coordinator.data or {}).get("5", "")
        charging = mode in ["charge", "docked", "Charging"]
        
        return icon_for_battery_level(self.native_value, charging=charging)

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data:
            # S1 Pro uses DPS 8 for battery
            value = self.coordinator.data.get("8")
            if value is not None:
                try:
                    battery = int(value)
                    if 0 <= battery <= 100:
                        return battery
                except (ValueError, TypeError):
                    pass
            
            # Fallback to DPS 163
            value = self.coordinator.data.get("163")
            if value is not None:
                try:
                    battery = int(value)
                    if 0 <= battery <= 100:
                        return battery
                except (ValueError, TypeError):
                    pass
        return None


class CleaningModeSensor(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, SensorEntity):
    """Sensor that shows current cleaning mode based on DPS 154 and 10."""
    
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Cleaning Mode"
    _attr_icon = "mdi:broom"
    
    # Cleaning mode definitions matching select.py
    CLEANING_MODES = {
        "vacuum": {
            "name": "Vacuum Only",
            "dps154": "FAoKCgASABoAIgIIAhIGCAEQASAB",
            "dps10": None
        },
        "mop_low": {
            "name": "Vacuum and Mop (Water Level: Low)",
            "dps154": "FAoKCgIIAhIAGgAiABIGCAEQASAB",
            "dps10": "low"
        },
        "mop_middle": {
            "name": "Vacuum and Mop (Water Level: Medium)",
            "dps154": "FgoMCgIIAhIAGgAiAggBEgYIARABIAE=",
            "dps10": "middle"
        },
        "mop_high": {
            "name": "Vacuum and Mop (Water Level: High)",
            "dps154": "FgoMCgIIAhIAGgAiAggCEgYIARABIAE=",
            "dps10": "high"
        }
    }
    
    # Map DPS values to mode names
    DPS_TO_MODE_MAP = {
        ("FAoKCgASABoAIgIIAhIGCAEQASAB", None): "vacuum",
        ("FAoKCgIIAhIAGgAiABIGCAEQASAB", "low"): "mop_low",
        ("FgoMCgIIAhIAGgAiAggBEgYIARABIAE=", "middle"): "mop_middle",
        ("FgoMCgIIAhIAGgAiAggCEgYIARABIAE=", "high"): "mop_high",
    }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if we have the coordinator data and at least DPS 154
        return self.coordinator.data is not None and "154" in self.coordinator.data

    @property
    def native_value(self) -> str:
        """Return the current cleaning mode based on DPS 154 and 10."""
        if not self.coordinator.data:
            return "Unknown"
        
        dps154 = self.coordinator.data.get("154", "")
        dps10 = self.coordinator.data.get("10", None)
        
        # Check if DPS 10 is a string (water level)
        if isinstance(dps10, str) and dps10 in ["low", "middle", "high"]:
            water_level = dps10
        else:
            water_level = None
        
        # Try to find matching mode
        mode_key = (dps154, water_level)
        if mode_key in self.DPS_TO_MODE_MAP:
            mode = self.DPS_TO_MODE_MAP[mode_key]
            if mode in self.CLEANING_MODES:
                return self.CLEANING_MODES[mode]["name"]
        
        # Try without water level (vacuum mode)
        if dps154 == self.CLEANING_MODES["vacuum"]["dps154"]:
            return self.CLEANING_MODES["vacuum"]["name"]
        
        # Fallback to DPS 5 if available (legacy)
        dps5_value = self.coordinator.data.get("5", "")
        if dps5_value:
            return str(dps5_value).replace("_", " ").title()
        
        return "Unknown"


class FanSpeedSensor(BaseDPSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def parse_value(self, value):
        """Convert fan speed to readable format"""
        if value:
            return str(value).replace("_", " ").title()
        return "Unknown"


class RunningStatusSensor(BaseDPSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def parse_value(self, value):
        """Convert boolean to readable status"""
        if value is True:
            return "Running"
        elif value is False:
            return "Stopped"
        return "Unknown"
