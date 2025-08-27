# N.A.A.R.I  (Nathan’s Ambient Assistant Room Interface)

⚠️ Status: **Active Development**

N.A.A.R.I is not yet a fully deployable standalone web application. It currently runs in Dash development mode. Features are functional but under testing, and bugs are still being worked out.  
User discretion advised, N.A.A.R.I has warned you. 🤖

## Why N.A.A.R.I?

Managing multiple WLED devices normally requires adjusting each one individually or enabling WLED Sync. Neither option provides a true one stop solution. WLED Sync forces all devices to follow the same command, the same preset, brightness, or color, with no room for variety. You cannot dim one device without dimming them all, or set different presets across the room. Once you add three or more devices, it quickly becomes a pain to change each one manually every time you want to match a theme or mood.

I designed and built Project **N.A.A.R.I**, a Python-based Dash application that funnels multiple WLED devices into a single, simplified control panel. It provides a global view, individual device flexibility, and a foundation that can scale beyond WLED in the future.

## Features

### ✅ Current (Working / Testing)

- Global theme selection

- Theme preset creation

- Individual device indicators through interval polling

- Preset selection (pulled from device memory)

- On and Off control

- Brightness control

- Config reader and editor

> Note: Presets are currently pulled from each WLED device. Preset creation must still be done on the device itself. Creation features will roll out in N.A.A.R.I over time but may not replace WLED’s built-in system completely.

### 🚧 Current Planned / Roadmap

- Internal logging and log manager

- Server deployment for homelabs, Raspberry Pi, or similar setups

- Device info panel for real-time status of active devices (maybe)

- Preset creation directly inside the Dash cards

- Voice commands (long-term goal)

- Generative AI assistant responses (long-term goal)

## Usage

- Access the web UI to manage multiple WLED devices from one panel

- Current workflows include:

  - Selecting global themes

  - Adjusting brightness and power state

  - Reading and editing config values

📖 A Wiki Manual is in progress to document the full UI, features, buttons, and expectations. In it will include screenshots and explanations. 


## Requirements

Core: Python and Dash

Environment: Dash currently runs in development mode, server deployment coming soon

Devices: Any WLED-compatible controller including MAGWLED, QuinLED, GLEDOPTO ESP32, or DIY ESP32 builds

Compatibility: Works with WLED v0.15.1 and expected to support future versions that maintain JSON API commands


## Installation and Setup

Python Version: Recommended 3.12 or greater (may work on 3.10 and 3.11 but not tested)

Clone this repo and run the setup script:

```bash
git clone https://github.com/nathanengineer/NAARI.git
cd NAARI
setup.cmd
```
This installs dependencies from requirements.txt.

Remember to configure an .env file from .env_example.

Launch app: dev_naari_launcher.cmd
Open your prowser at http://127.0.0.1:{.env PORT}


## Contribution Guidelines

Contributions are welcome, but please open an issue or discussion first. Just reach out first 
I am open to new ideas and visions, but N.A.A.R.I has a clear vision in mind and contributions should align with it.

## License

This project is dual-licensed:

MIT License → Free for personal, educational, and open-source use

Commercial License → Required for any commercial use (including sale of products, services, or applications using N.A.A.R.I)

📩 For commercial licensing inquiries, for now, please open a ticket at:
NAARI GitHub Issues