"""Support for getting the Balaton átlag water level."""
from __future__ import annotations

from typing import Final

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
from homeassistant.const import CONF_NAME, UnitOfLength

_LOGGER = logging.getLogger(__name__)

PATH = "https://geoportal.vizugy.hu/arcgis/rest/services/VIR/Vizmercek_vizugyhu/MapServer/60/query"
PARAMS = {
    "f": "json",
    "where": "vFeAllomas_webmerc.TulajdonosSzervezetKod = 4",
    "returnGeometry": "false",
    "outFields": "vFeAllomas_webmerc.Nev,vFeAllomas_webmerc.Torzsszam,vFeAllomas_webmerc.vFeAllomas_VizmerceMederVOANev,vFeAllomas_webmerc.vFeAllomas_VizmerceFkm,vFeAllomas_webmerc.vFeAllomas_VizmerceNullpont,vFeAllomas_webmerc.vFeAllomas_VizmerceLKV,vFeAllomas_webmerc.vFeAllomas_VizmerceLNV,vFeAllomas_webmerc.vFeAllomas_VizmerceKF1,vFeAllomas_webmerc.vFeAllomas_VizmerceKF2,vFeAllomas_webmerc.vFeAllomas_VizmerceKF3,vh.dbo.tArvizKeszultseg.FokozatKod,vh.dbo.AllomasAdatVOP_FE.MaxTime,vh.dbo.AllomasAdatVOP_FE.Vizallas,vh.dbo.AllomasAdatVOP_FE.Vizhozam,vh.dbo.AllomasAdatVOP_FE.Vizho",
}

ATTRIBUTES = "attributes"
FEATURES = "features"
VIZALLAS = "vh.dbo.AllomasAdatVOP_FE.Vizallas"
NEV = "vFeAllomas_webmerc.Nev"
DEFAULT_NAME = "Balaton átlag"

PLATFORM_SCHEMA: Final = BASE_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config[CONF_NAME]
    async_add_entities([BalatonWaterLevel(name)])


class BalatonWaterLevel(SensorEntity):
    """Representation of a sensor."""

    def __init__(self, place) -> None:
        """Initialize a sensor."""
        self.place = place

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

        async with aiohttp.ClientSession() as session:
            response = await session.request(method, path, params=PARAMS)

            if not response.ok:
                raise Exception(response.status)

            content_json = await response.json()

            return [
                feat.get(ATTRIBUTES).get(VIZALLAS)
                for feat in content_json.get(FEATURES)
                if feat.get(ATTRIBUTES).get(NEV) == self.place
            ][0]
