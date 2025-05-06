# TypeTrace

<img src="/data/icons/hicolor/scalable/apps/edu.ost.typetrace.svg" width="100" height="100">

TypeTrace is an open-source application that tracks your keyboard input and
visualizes it through a heatmap and various charts. It provides insights into
typing behaviors, daily keystroke counts, and more. As a privacy-respecting
alternative to [WhatPulse](https://whatpulse.org/), TypeTrace ensures your data
is stored locally and under your control.

## Features

- **Keyboard Tracking**: Logs keystrokes locally with daily timestamps.
- **Visualizations**: Displays data via heatmaps and charts for intuitive analysis.
- **Privacy First**: Stores data in a local SQLite database, making it nearly impossible to reverse-engineer sensitive information like passwords.
- **Open Source**: Fully transparent codebase

## Screenshots

| Heatmap                             | Top Keystrokes                                    | Daily Keystrokes                                 |
| ----------------------------------- | ------------------------------------------------- | ------------------------------------------------ |
| ![Final Survey](images/heatmap.png) | ![Statistics by Date](images/statistics_date.png) | ![Total Statistics](images/statistics_total.png) |

## Installation

TypeTrace can be installed on any Linux distribution using the following command:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/domi413/TypeTrace/main/install.sh | bash
```

Note that:

- The script requires the following dependencies:

  - `curl`
  - `jq`
  - GNOME Shell 48 or later

- The local install requires the following dependencies:

  - `meson`
  - `ninja`
  - `pkg-config`

- Flatpak install requires the following dependencies:

  - `flatpak`
