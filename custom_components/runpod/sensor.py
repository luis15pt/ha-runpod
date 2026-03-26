"""Sensor platform for RunPod integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import RunPodDataUpdateCoordinator


def _to_pct(value: float | None) -> float | None:
    """Convert a 0-1 fraction to a 0-100 percentage."""
    return round(value * 100, 2) if value is not None else None



def _yesterday_earnings(data: dict[str, Any], machine_id: str | None = None) -> float:
    """Get yesterday's total earnings from machineEarnings history."""
    from datetime import date, timedelta

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    total = 0.0
    for entry in data.get("machineEarnings") or []:
        if machine_id is not None and entry.get("machineId") != machine_id:
            continue
        if (entry.get("date") or "")[:10] == yesterday:
            total += entry.get("hostTotalEarnings") or 0
    return total


@dataclass(frozen=True, kw_only=True)
class RunPodSensorEntityDescription(SensorEntityDescription):
    """Describe a RunPod sensor."""

    value_fn: Callable[[dict[str, Any]], StateType | None]


# ---------------------------------------------------------------------------
# Machine-level sensor descriptions
# ---------------------------------------------------------------------------

def _machine_status(m: dict[str, Any]) -> str | None:
    """Derive a single machine status from boolean flags."""
    if m.get("maintenanceMode"):
        return "maintenance"
    if m.get("hidden"):
        return "hidden"
    if m.get("listed"):
        return "listed"
    if m.get("registered"):
        return "unlisted"
    return "unregistered"


MACHINE_STATUS_OPTIONS = ["listed", "unlisted", "maintenance", "hidden", "unregistered"]

MACHINE_SENSOR_DESCRIPTIONS: tuple[RunPodSensorEntityDescription, ...] = (
    RunPodSensorEntityDescription(
        key="machine_status",
        translation_key="machine_status",
        icon="mdi:list-status",
        device_class=SensorDeviceClass.ENUM,
        options=MACHINE_STATUS_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_machine_status,
    ),
    RunPodSensorEntityDescription(
        key="gpu_type",
        translation_key="gpu_type",
        icon="mdi:expansion-card-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: (m.get("gpuType") or {}).get("displayName"),
    ),
    RunPodSensorEntityDescription(
        key="gpu_count_total",
        translation_key="gpu_count_total",
        icon="mdi:expansion-card-variant",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("gpuTotal"),
    ),
    RunPodSensorEntityDescription(
        key="gpu_count_rented",
        translation_key="gpu_count_rented",
        icon="mdi:card-account-details",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.get("gpuReserved"),
    ),
    RunPodSensorEntityDescription(
        key="host_price_per_gpu",
        translation_key="host_price_per_gpu",
        icon="mdi:tag-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD/h",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=4,
        value_fn=lambda m: m.get("hostPricePerGpu"),
    ),
    RunPodSensorEntityDescription(
        key="host_min_bid_per_gpu",
        translation_key="host_min_bid_per_gpu",
        icon="mdi:tag-minus-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD/h",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=4,
        value_fn=lambda m: m.get("hostMinBidPerGpu"),
    ),
    RunPodSensorEntityDescription(
        key="total_earnings",
        translation_key="total_earnings",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="USD",
        suggested_display_precision=4,
        value_fn=lambda m: (m.get("machineBalance") or {}).get("hostTotalEarnings"),
    ),
    RunPodSensorEntityDescription(
        key="gpu_earnings",
        translation_key="gpu_earnings",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="USD",
        suggested_display_precision=4,
        value_fn=lambda m: (m.get("machineBalance") or {}).get("hostGpuEarnings"),
    ),
    RunPodSensorEntityDescription(
        key="disk_earnings",
        translation_key="disk_earnings",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="USD",
        suggested_display_precision=4,
        value_fn=lambda m: (m.get("machineBalance") or {}).get("hostDiskEarnings"),
    ),
    RunPodSensorEntityDescription(
        key="uptime_1_week",
        translation_key="uptime_1_week",
        icon="mdi:clock-check-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda m: _to_pct(m.get("uptimePercentListedOneWeek")),
    ),
    RunPodSensorEntityDescription(
        key="uptime_4_week",
        translation_key="uptime_4_week",
        icon="mdi:clock-check-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda m: _to_pct(m.get("uptimePercentListedFourWeek")),
    ),
    RunPodSensorEntityDescription(
        key="uptime_12_week",
        translation_key="uptime_12_week",
        icon="mdi:clock-check-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda m: _to_pct(m.get("uptimePercentListedTwelveWeek")),
    ),
    RunPodSensorEntityDescription(
        key="cpu_utilization",
        translation_key="cpu_utilization",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        value_fn=lambda m: (m.get("latestTelemetry") or {}).get("cpuUtilization"),
    ),
    RunPodSensorEntityDescription(
        key="ram_utilization",
        translation_key="ram_utilization",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        value_fn=lambda m: (m.get("latestTelemetry") or {}).get("memoryUtilization"),
    ),
    RunPodSensorEntityDescription(
        key="vcpu_total",
        translation_key="vcpu_total",
        icon="mdi:cpu-64-bit",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("vcpuTotal"),
    ),
    RunPodSensorEntityDescription(
        key="ram_total",
        translation_key="ram_total",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("memoryTotal"),
    ),
    RunPodSensorEntityDescription(
        key="disk_total",
        translation_key="disk_total",
        icon="mdi:harddisk",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("diskTotal"),
    ),
    RunPodSensorEntityDescription(
        key="pods_running",
        translation_key="pods_running",
        icon="mdi:cube-send",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: sum(
            1
            for p in (m.get("pods") or [])
            if (p.get("desiredStatus") or "").upper() == "RUNNING"
        ),
    ),
    RunPodSensorEntityDescription(
        key="pods_stopped",
        translation_key="pods_stopped",
        icon="mdi:cube-off-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: sum(
            1
            for p in (m.get("pods") or [])
            if (p.get("desiredStatus") or "").upper() != "RUNNING"
        ),
    ),
    RunPodSensorEntityDescription(
        key="pods_total",
        translation_key="pods_total",
        icon="mdi:cube-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: len(m.get("pods") or []),
    ),
    RunPodSensorEntityDescription(
        key="rental_revenue_per_hr",
        translation_key="rental_revenue_per_hr",
        icon="mdi:cash-clock",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD/h",
        suggested_display_precision=4,
        value_fn=lambda m: sum(
            p.get("costPerHr") or 0
            for p in (m.get("pods") or [])
            if (p.get("desiredStatus") or "").upper() == "RUNNING"
        ),
    ),
    RunPodSensorEntityDescription(
        key="gpu_vram",
        translation_key="gpu_vram",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: (m.get("gpuType") or {}).get("memoryInGb"),
    ),
    RunPodSensorEntityDescription(
        key="gpu_allocated",
        translation_key="gpu_allocated",
        icon="mdi:expansion-card-variant",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("totalGpuAllocated"),
    ),
    RunPodSensorEntityDescription(
        key="disk_reserved",
        translation_key="disk_reserved",
        icon="mdi:harddisk",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("diskReserved"),
    ),
    RunPodSensorEntityDescription(
        key="runpod_fee",
        translation_key="runpod_fee",
        icon="mdi:percent-outline",
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda m: _to_pct(m.get("margin")),
    ),
    RunPodSensorEntityDescription(
        key="vcpu_reserved",
        translation_key="vcpu_reserved",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("vcpuReserved"),
    ),
    RunPodSensorEntityDescription(
        key="ram_reserved",
        translation_key="ram_reserved",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("memoryReserved"),
    ),
)

# ---------------------------------------------------------------------------
# Account-level sensor descriptions
# ---------------------------------------------------------------------------

ACCOUNT_SENSOR_DESCRIPTIONS: tuple[RunPodSensorEntityDescription, ...] = (
    RunPodSensorEntityDescription(
        key="total_machines",
        translation_key="total_machines",
        icon="mdi:server-network",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: len(d.get("machines") or []),
    ),
    RunPodSensorEntityDescription(
        key="total_gpus",
        translation_key="total_gpus",
        icon="mdi:expansion-card-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: sum(
            m.get("gpuTotal") or 0 for m in (d.get("machines") or [])
        ),
    ),
    RunPodSensorEntityDescription(
        key="total_gpus_rented",
        translation_key="total_gpus_rented",
        icon="mdi:card-account-details",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: sum(
            m.get("gpuReserved") or 0 for m in (d.get("machines") or [])
        ),
    ),
    RunPodSensorEntityDescription(
        key="total_gpus_available",
        translation_key="total_gpus_available",
        icon="mdi:expansion-card-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: sum(
            (m.get("gpuTotal") or 0) - (m.get("gpuReserved") or 0)
            for m in (d.get("machines") or [])
        ),
    ),
    RunPodSensorEntityDescription(
        key="total_pods_running",
        translation_key="total_pods_running",
        icon="mdi:cube-send",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: sum(
            1
            for m in (d.get("machines") or [])
            for p in (m.get("pods") or [])
            if (p.get("desiredStatus") or "").upper() == "RUNNING"
        ),
    ),
    RunPodSensorEntityDescription(
        key="account_total_earnings",
        translation_key="account_total_earnings",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="USD",
        suggested_display_precision=4,
        value_fn=lambda d: sum(
            (m.get("machineBalance") or {}).get("hostTotalEarnings") or 0
            for m in (d.get("machines") or [])
        ),
    ),
    RunPodSensorEntityDescription(
        key="account_gpu_earnings",
        translation_key="account_gpu_earnings",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="USD",
        suggested_display_precision=4,
        value_fn=lambda d: sum(
            (m.get("machineBalance") or {}).get("hostGpuEarnings") or 0
            for m in (d.get("machines") or [])
        ),
    ),
    RunPodSensorEntityDescription(
        key="account_disk_earnings",
        translation_key="account_disk_earnings",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="USD",
        suggested_display_precision=4,
        value_fn=lambda d: sum(
            (m.get("machineBalance") or {}).get("hostDiskEarnings") or 0
            for m in (d.get("machines") or [])
        ),
    ),
    RunPodSensorEntityDescription(
        key="host_balance",
        translation_key="host_balance",
        icon="mdi:wallet-outline",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        suggested_display_precision=2,
        value_fn=lambda d: d.get("hostBalance"),
    ),
    RunPodSensorEntityDescription(
        key="yesterday_earnings",
        translation_key="yesterday_earnings",
        icon="mdi:cash-register",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        suggested_display_precision=2,
        value_fn=lambda d: _yesterday_earnings(d),
    ),
    RunPodSensorEntityDescription(
        key="today_earnings",
        translation_key="today_earnings",
        icon="mdi:cash-clock",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        suggested_display_precision=2,
        value_fn=lambda d: sum(
            (m.get("machineBalance") or {}).get("hostTotalEarnings") or 0
            for m in (d.get("machines") or [])
        ),
    ),
)


# ---------------------------------------------------------------------------
# Helper: build device info
# ---------------------------------------------------------------------------


def _account_device_info(user_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{user_id}")},
        name="RunPod Account",
        manufacturer="RunPod",
        entry_type=DeviceEntryType.SERVICE,
    )


def _machine_device_info(machine: dict[str, Any], user_id: str) -> DeviceInfo:
    gpu_type = machine.get("gpuType") or {}
    return DeviceInfo(
        identifiers={(DOMAIN, f"machine_{machine['id']}")},
        name=machine.get("name") or machine["id"],
        manufacturer="RunPod",
        model=gpu_type.get("displayName"),
        via_device=(DOMAIN, f"account_{user_id}"),
    )


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------


class RunPodAccountSensorEntity(
    CoordinatorEntity[RunPodDataUpdateCoordinator], SensorEntity
):
    """Account-level aggregate sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    entity_description: RunPodSensorEntityDescription

    def __init__(
        self,
        coordinator: RunPodDataUpdateCoordinator,
        user_id: str,
        description: RunPodSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._user_id = user_id
        self._attr_unique_id = f"{user_id}_{description.key}"
        self._attr_device_info = _account_device_info(user_id)

    @property
    def native_value(self) -> StateType | None:
        return self.entity_description.value_fn(self.coordinator.data)


class RunPodMachineSensorEntity(
    CoordinatorEntity[RunPodDataUpdateCoordinator], SensorEntity
):
    """Per-machine sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    entity_description: RunPodSensorEntityDescription

    def __init__(
        self,
        coordinator: RunPodDataUpdateCoordinator,
        user_id: str,
        machine_id: str,
        description: RunPodSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._machine_id = machine_id
        self._attr_unique_id = f"{machine_id}_{description.key}"
        self._attr_device_info = _machine_device_info(
            self._get_machine_data() or {"id": machine_id}, user_id
        )

    def _get_machine_data(self) -> dict[str, Any] | None:
        for machine in self.coordinator.data.get("machines") or []:
            if machine["id"] == self._machine_id:
                return machine
        return None

    @property
    def native_value(self) -> StateType | None:
        machine = self._get_machine_data()
        if machine is None:
            return None
        return self.entity_description.value_fn(machine)


class RunPodMachinePodsSensorEntity(
    CoordinatorEntity[RunPodDataUpdateCoordinator], SensorEntity
):
    """Sensor showing pod details on a machine as extra attributes."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_translation_key = "pods_detail"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: RunPodDataUpdateCoordinator,
        user_id: str,
        machine_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._machine_id = machine_id
        self._attr_unique_id = f"{machine_id}_pods_detail"
        self._attr_device_info = _machine_device_info(
            self._get_machine_data() or {"id": machine_id}, user_id
        )

    def _get_machine_data(self) -> dict[str, Any] | None:
        for machine in self.coordinator.data.get("machines") or []:
            if machine["id"] == self._machine_id:
                return machine
        return None

    @property
    def native_value(self) -> StateType | None:
        machine = self._get_machine_data()
        if machine is None:
            return None
        return len(machine.get("pods") or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        machine = self._get_machine_data()
        if machine is None:
            return None
        pods = machine.get("pods") or []
        attrs: dict[str, Any] = {}
        for pod in pods:
            name = pod.get("name") or pod["id"]
            status = (pod.get("desiredStatus") or "unknown").lower()
            cost = pod.get("costPerHr")
            gpus = pod.get("gpuCount")
            attrs[name] = {
                "status": status,
                "cost_per_hr": cost,
                "gpu_count": gpus,
            }
        return attrs


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RunPod sensor entities."""
    coordinator: RunPodDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    user_id = coordinator.data["id"]

    # Account-level sensors
    for desc in ACCOUNT_SENSOR_DESCRIPTIONS:
        entities.append(RunPodAccountSensorEntity(coordinator, user_id, desc))

    # Machine-level sensors
    for machine in coordinator.data.get("machines") or []:
        machine_id = machine["id"]
        for desc in MACHINE_SENSOR_DESCRIPTIONS:
            entities.append(
                RunPodMachineSensorEntity(coordinator, user_id, machine_id, desc)
            )
        # Pods detail sensor with attributes
        entities.append(
            RunPodMachinePodsSensorEntity(coordinator, user_id, machine_id)
        )

    async_add_entities(entities)
