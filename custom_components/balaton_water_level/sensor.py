"""Support for getting the Balaton átlag water level."""
from __future__ import annotations

from typing import Final

import ast
import re
import logging
import aiohttp
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as BASE_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.util import Throttle
from homeassistant.const import CONF_NAME, CONF_ID, UnitOfLength

_LOGGER = logging.getLogger(__name__)

PATH = "https://www.vizugy.hu/"

DEFAULT_NAME = "Balaton átlag"
DEFAULT_VOA = "164961D7-97AB-11D4-BB62-00508BA24287"

PLATFORM_SCHEMA: Final = BASE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_ID, default=DEFAULT_VOA): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config[CONF_NAME]
    voa = config[CONF_ID]
    async_add_entities([BalatonWaterLevel(name, voa)])


class BalatonWaterLevel(SensorEntity):
    """Representation of a sensor."""

    def __init__(self, place, voa) -> None:
        """Initialize a sensor."""
        self.place = place
        self.voa = voa

    @property
    def unique_id(self) -> str | None:
        return f"{self.place}WaterLevel"

    @property
    def name(self) -> str | None:
        return f"{self.place} water level"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.DISTANCE

    @property
    def native_unit_of_measurement(self) -> str | None:
        return UnitOfLength.CENTIMETERS

    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT

    @Throttle(timedelta(minutes=5))
    async def async_update(self):
        """Get the latest data."""
        self._attr_native_value = await self.__async_request()

    async def __async_request(
        self,
        path: str = PATH,
        method: str = aiohttp.hdrs.METH_GET,
    ) -> int:
        """Async request with aiohttp"""
        request_params = {
            "AllomasVOA": f"{self.voa}",
            "mapData": "Idosor",
            "mapModule": "OpGrafikon",
        }

        async with aiohttp.ClientSession() as session:
            response = await session.request(method, path, params=request_params)

            if not response.ok:
                raise Exception(response.status)

            content_raw = await response.read()
            content = content_raw.decode()
            vizallas = re.search(
                r"Vizallas = new Array\(.*?(?=\))\)", content, re.S
            ).group()
            vizallas_array = re.search(r"\(.*\)", vizallas, re.S).group()
            vizallas_list = ast.literal_eval(vizallas_array)
            return vizallas_list[-1]
