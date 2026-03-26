# RunPod Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/release/luis15pt/ha-runpod.svg)](https://github.com/luis15pt/ha-runpod/releases)

Monitor your [RunPod](https://www.runpod.io/) GPU hosting machines from Home Assistant.

## Features

- Real-time GPU rental status per machine
- Today's earnings (GPU + disk), host balance, yesterday's earnings
- Pod monitoring (running, stopped, total) with per-pod details
- Resource allocation tracking (vCPUs, RAM, disk reserved vs total)
- Machine health (status, uptime, CPU/RAM utilization)
- Account-level fleet overview (total GPUs, rented, available)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the 3 dots in the top right > **Custom repositories**
3. Add `https://github.com/luis15pt/ha-runpod` with category **Integration**
4. Search for "RunPod" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/runpod/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **RunPod**
3. Enter your RunPod API key (found at [RunPod Settings](https://www.runpod.io/console/user/settings))

## Entities

### Account Level

| Sensor | Description |
|--------|-------------|
| Total Machines | Number of host machines |
| Total GPUs | Total GPUs across all machines |
| Total GPUs Rented | GPUs currently rented |
| Total GPUs Available | GPUs available for rent |
| Total Pods Running | Running pods across all machines |
| Earnings Today | Today's total earnings (resets daily) |
| Earnings Yesterday | Yesterday's settled earnings |
| Host Balance | Pending payout balance |

### Per Machine

| Sensor | Description |
|--------|-------------|
| Rented GPUs | GPUs currently reserved by customers |
| Pods Running / Stopped / Total | Pod counts by status |
| Rental Revenue Per Hour | Current hourly revenue from running pods |
| Earnings Today | Today's machine earnings (resets daily) |
| GPU/Disk Earnings Today | Breakdown by GPU and disk |
| CPU/RAM Utilization | Machine-level utilization |

### Diagnostics (per machine)

| Sensor | Description |
|--------|-------------|
| Status | Listed, unlisted, maintenance, hidden |
| GPU Type / VRAM | GPU model and memory |
| Total GPUs / Allocated | Hardware vs allocated count |
| vCPUs Total / Reserved | vCPU allocation |
| Total RAM / Reserved | RAM allocation |
| Total Disk / Reserved | Disk allocation |
| Uptime (1/4/12 week) | Uptime percentages |
| Host Price / Min Bid | Pricing configuration |
| RunPod Fee | RunPod commission percentage |

## Polling Interval

Data is refreshed every 60 seconds.

## License

MIT
