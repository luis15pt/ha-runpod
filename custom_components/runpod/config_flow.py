"""Config flow for RunPod integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RunPodApiClient, RunPodAuthError, RunPodConnectionError
from .const import CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


class RunPodConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RunPod."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = RunPodApiClient(session, user_input[CONF_API_KEY])

            try:
                user_data = await client.async_validate_api_key()
            except RunPodAuthError:
                errors["base"] = "invalid_auth"
            except RunPodConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during RunPod API validation")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_data["id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="RunPod",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
