"""Diagnostics support for RunPod integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DOMAIN
from .coordinator import RunPodDataUpdateCoordinator

TO_REDACT = {CONF_API_KEY, "id", "userId", "apiKey", "installCert"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: RunPodDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "config_entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "coordinator_data": async_redact_data(coordinator.data, TO_REDACT),
    }
