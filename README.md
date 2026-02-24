# CenoV2 — Power Management

A minimal Linux desktop utility for switching CPU power profiles via a Tkinter GUI.

## What it does

Lets you switch between three power modes — Performance, Balanced, and Power Saver —
and applies the appropriate CPU governor or power profile using whichever backend
is available on the system.

## Backend detection (auto)

- `powerprofilesctl` (power-profiles-daemon) — preferred, Fedora 35+
- `cpupower` with sudo
- Direct sysfs write to `/sys/devices/system/cpu/*/cpufreq/scaling_governor`

## Features

- Switch between Performance / Balanced / Power Saver with one click
- Live battery percentage and AC status in the header
- Current governor shown in the status bar
- Threaded apply — UI stays responsive during changes
- Command log showing exact commands executed and their results
- Animated logo (purely cosmetic)

## Requirements

- Fedora / RPM-based distro
- Python 3 + tkinter
- `power-profiles-daemon` recommended (`sudo dnf install power-profiles-daemon`)

## Install
```bash
git clone https://github.com/ivancukartur6-cyber/cenov2
cd cenov2
bash install.sh
```

The installer handles everything — dependencies, build, and desktop entry.
After install, search **CenoV2** in your app launcher.

## Uninstall
```bash
sudo rm /usr/local/bin/cenov2
sudo rm /usr/share/applications/cenov2.desktop
```
