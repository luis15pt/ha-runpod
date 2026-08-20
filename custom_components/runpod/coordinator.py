"""DataUpdateCoordinator for RunPod."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RunPodApiClient, RunPodApiError, RunPodAuthError, RunPodConnectionError
from .const import AUTH_FAILURE_THRESHOLD, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class RunPodDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching RunPod data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: RunPodApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self._known_machine_ids: set[str] | None = None
        self._auth_failures = 0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_get_data()
        except RunPodAuthError as err:
            # RunPod occasionally answers 401 during an outage. Retry a few
            # times first -- ConfigEntryAuthFailed stops this coordinator for
            # good, so escalating on the first failure silently kills the
            # integration until someone reloads it by hand.
            self._auth_failures += 1
            if self._auth_failures < AUTH_FAILURE_THRESHOLD:
                raise UpdateFailed(
                    f"RunPod authentication error "
                    f"({self._auth_failures}/{AUTH_FAILURE_THRESHOLD}): {err}"
                ) from err
            raise ConfigEntryAuthFailed(
                "API key is invalid or expired"
            ) from err
        except RunPodConnectionError as err:
            raise UpdateFailed(
                f"Error communicating with RunPod API: {err}"
            ) from err
        except RunPodApiError as err:
            raise UpdateFailed(f"RunPod API error: {err}") from err

        self._auth_failures = 0

        # Reload if machines are added or removed
        new_ids = {m["id"] for m in (data.get("machines") or [])}
        if self._known_machine_ids is not None and new_ids != self._known_machine_ids:
            _LOGGER.info("RunPod machine list changed, reloading config entry")
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.config_entry.entry_id)
            )
        self._known_machine_ids = new_ids

        return data
