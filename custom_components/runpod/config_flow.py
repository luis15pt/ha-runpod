"""Config flow for RunPod integration."""

from __future__ import annotations

from collections.abc import Mapping
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

    async def _async_validate(
        self, api_key: str, errors: dict[str, str]
    ) -> dict[str, Any] | None:
        """Validate an API key, recording any failure in errors."""
        session = async_get_clientsession(self.hass)
        client = RunPodApiClient(session, api_key)

        try:
            return await client.async_validate_api_key()
        except RunPodAuthError:
            errors["base"] = "invalid_auth"
        except RunPodConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error during RunPod API validation")
            errors["base"] = "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_data = await self._async_validate(user_input[CONF_API_KEY], errors)
            if user_data is not None:
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

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication triggered by ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a fresh API key and update the existing entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_data = await self._async_validate(user_input[CONF_API_KEY], errors)
            if user_data is not None:
                await self.async_set_unique_id(user_data["id"])
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates=user_input
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
