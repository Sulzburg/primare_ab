import socket
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

SP25_IP = "XXX.XXX.XXX.XXX"  """replace with the IP of your SP(A)25"""
SP25_PORT = 50006
END_CHARACTER = "\r\n"

def send_command(command):
    """Sends command to SP(A)25 and returns the answer."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SP25_IP, SP25_PORT))
            s.sendall((command + END_CHARACTER).encode("ascii"))
            response = s.recv(1024).decode("ascii").strip()
            return response
    except Exception as e:
        _LOGGER.error(f"Fehler beim Senden des Befehls: {e}")
        return None

def get_current_volume():
    """Checks the current volume."""
    response = send_command("!1vol.?")
    if response and response.startswith("!1vol."):
        return int(response.split(".")[1])
    return None

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Sets the Number entity in Home Assistant."""
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sp25_volume",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )
    add_entities([SP25VolumeSlider(coordinator)])
    coordinator.async_config_entry_first_refresh()

async def async_update_data():
    """Retrieve the current volume."""
    return {"volume": get_current_volume()}

class SP25VolumeSlider(CoordinatorEntity, NumberEntity):
    """Volume control for SP(A)25"""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "sp25_volume_slider"
        self._attr_name = "SP25 Volume"
        self._attr_icon = "mdi:volume-high"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 99
        self._attr_native_step = 1
    
    @property
    def native_value(self):
        return self.coordinator.data.get("volume")

    def set_native_value(self, value):
        send_command(f"!1vol.{int(value)}")
        self.coordinator.async_request_refresh()
