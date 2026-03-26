"""RunPod GraphQL API client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)

GRAPHQL_QUERY = """
query {
  myself {
    id
    hostBalance
    machines {
      id
      name
      gpuTypeId
      location
      listed
      registered
      maintenanceMode
      hidden
      markedForDeletion
      gpuType {
        id
        displayName
        memoryInGb
      }
      gpuTotal
      gpuReserved
      totalGpuAllocated
      vcpuTotal
      vcpuReserved
      memoryReserved
      memoryTotal
      diskTotal
      diskReserved
      diskMBps
      uploadMbps
      downloadMbps
      hostPricePerGpu
      hostMinBidPerGpu
      margin
      uptimePercentListedOneWeek
      uptimePercentListedFourWeek
      uptimePercentListedTwelveWeek
      latestTelemetry {
        time
        cpuUtilization
        memoryUtilization
      }
      machineBalance {
        hostGpuEarnings
        hostDiskEarnings
        hostTotalEarnings
      }
      pods {
        id
        name
        desiredStatus
        costPerHr
        gpuCount
      }
    }
    machineEarnings {
      machineId
      date
      hostTotalEarnings
      hostGpuEarnings
      hostDiskEarnings
    }
  }
}
"""

VALIDATE_QUERY = """
query {
  myself {
    id
  }
}
"""


class RunPodApiError(Exception):
    """General RunPod API error."""


class RunPodAuthError(RunPodApiError):
    """Authentication error."""


class RunPodConnectionError(RunPodApiError):
    """Connection error."""


async def _request(
    session: aiohttp.ClientSession, api_key: str, query: str
) -> dict[str, Any]:
    """Execute a GraphQL request against the RunPod API."""
    try:
        async with session.post(
            API_BASE_URL,
            json={"query": query},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        ) as resp:
            if resp.status in (401, 403):
                raise RunPodAuthError("Invalid or expired API key")
            if resp.status == 400:
                body = await resp.text()
                raise RunPodApiError(f"Bad request (400): {body}")
            resp.raise_for_status()
            result = await resp.json()
    except (RunPodAuthError, RunPodApiError):
        raise
    except aiohttp.ClientError as err:
        raise RunPodConnectionError(
            f"Error communicating with RunPod API: {err}"
        ) from err

    if "errors" in result:
        errors = result["errors"]
        for error in errors:
            msg = error.get("message", "")
            if "auth" in msg.lower() or "unauthorized" in msg.lower():
                raise RunPodAuthError(msg)
        raise RunPodApiError(f"GraphQL errors: {errors}")

    return result.get("data", {})


class RunPodApiClient:
    """Client for the RunPod GraphQL API."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch all machine and pod data."""
        data = await _request(self._session, self._api_key, GRAPHQL_QUERY)
        myself = data.get("myself")
        if myself is None:
            raise RunPodApiError("Unexpected response: missing 'myself' field")
        return myself

    async def async_validate_api_key(self) -> dict[str, Any]:
        """Validate the API key with a lightweight query.

        Returns the user data dict containing at least 'id'.
        """
        data = await _request(self._session, self._api_key, VALIDATE_QUERY)
        myself = data.get("myself")
        if myself is None:
            raise RunPodApiError("Unexpected response: missing 'myself' field")
        return myself
