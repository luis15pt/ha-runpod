"""Constants for the RunPod integration."""

from typing import Final

DOMAIN: Final = "runpod"

CONF_API_KEY: Final = "api_key"

API_BASE_URL: Final = "https://api.runpod.io/graphql"

DEFAULT_SCAN_INTERVAL: Final = 60  # seconds

# Consecutive 401s required before we give up and ask the user to
# re-authenticate. ConfigEntryAuthFailed permanently stops the
# coordinator, so a single blip must not trigger it.
AUTH_FAILURE_THRESHOLD: Final = 3

ATTRIBUTION: Final = "Data provided by RunPod"
