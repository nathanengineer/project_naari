# N.A.A.R.I  (Nathan’s Ambient Assistant Room Interface)

⚠️ Status: **Beta Testing**

N.A.A.R.I is now available as a deployable Docker container, but is still considered in **beta**. Features are functional and the core system is stable, but active testing is ongoing.  
You may encounter bugs, unfinished features, or behavior subject to change.    
User discretion advised, N.A.A.R.I has warned you. 🤖
<br><br>

## Why N.A.A.R.I?

Managing multiple WLED devices normally requires adjusting each one individually or enabling WLED Sync. Neither option provides a true one stop solution. WLED Sync forces all devices to follow the same command, the same preset, brightness, or color, with no room for variety. You cannot dim one device without dimming them all, or set different presets across the room. Once you add three or more devices, it quickly becomes a pain to change each one manually every time you want to match a theme or mood.

I designed and built Project **N.A.A.R.I**, a Python-based Dash application that funnels multiple WLED devices into a single, simplified control panel. It provides a global view, individual device flexibility, and a foundation that can scale beyond WLED in the future.
<br><br>


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

- Device info panel for real-time status of active devices (maybe)

- Preset creation directly inside the Dash cards

- Voice commands (long-term goal)

- Generative AI assistant responses (long-term goal)
<br><br>


## Usage

- Access the web UI to manage multiple WLED devices from one panel

- Current workflows include:

  - Selecting global themes OR individual device presets

  - Adjusting brightness and power state

  - Reading and editing config values

📖 A Wiki Manual is in progress to document the full UI, features, buttons, and expectations. In it will include screenshots and explanations. 


### Main Page Example:
<img width="1148" height="837" alt="Image" src="https://github.com/user-attachments/assets/054da935-2850-4d9b-b05e-62f0e07d03eb" />

### Configuration WIndow:
<img width="1148" height="1158" alt="Image" src="https://github.com/user-attachments/assets/825ff140-cc72-4bdb-ae9c-8ae9b923810c" />
<br><br>


## Requirements

Core: Python and Dash

Environment: Dash currently runs in development mode, server deployment coming soon

Devices: Any WLED-compatible controller including MAGWLED, QuinLED, GLEDOPTO ESP32, or DIY ESP32 builds

Compatibility: Works with WLED v0.15.1 and expected to support future versions that maintain JSON API commands
<br><br>


## Installation and Setup

### For Non Server Deployment (Window / macOS)
**Python Version:** Recommended 3.12 or greater (may work on 3.10 and 3.11 but not tested)

Clone this repo and run the setup script:

```bash
git clone https://github.com/nathanengineer/project_naari.git NAARI
cd NAARI
setup.cmd
```
This installs dependencies from requirements.txt.

📝 Don’t forget to create and configure a .env file from .env_example.
See the .ENV Configuration section below for details.

Launch app: dev_naari_launcher.cmd
Open your prowser at http://127.0.0.1:{.env PORT}


### For Server Deployment (Docker on Raspberry Pi or Local Server)
> This app is designed to run locally via Docker. It is intended to stay on your local LAN and can optionally be assigned a static IP using macvlan.

**Prerequisites:**
- Docker and Docker Compose installed
- Git installed
- Root or sudo access

> Note: For Raspberry Pi, tested on Pi 5; should also work on Pi 4

<br><br>

**1. Create Docker macvlan Network (for assigning a static LAN IP))**

```bash
sudo docker network create -d macvlan \
  --subnet=192.168.100.0/24 \
  --gateway=192.168.100.1 \
  -o parent=eth0 \
  --ip-range=192.168.1.200/30 \
  custom-macnet
```
> Important: Replace subnet, gateway, and ip-range with values matching your own LAN setup. Do not copy blindly.
---

**2. Clone Repository**
```bash
git clone https://github.com/nathanengineer/project_naari.git naari
cd naari
```
---

**3. Create and Edit .env File**
```bash
cp .env_example .env
sudo nano .env
```
Refer to the .ENV Configuration section below for required fields

---

**4. Build and Run Docker APP**
Use the provided script to build and run the containerized app:
```bash
./build-and-run.sh
```
---

### .ENV Configuration
Environmental variable reference for local development and Docker deployment:
- HOST — Binds the app to the specified IP. Use 0.0.0.0 to expose it to the entire device network (e.g. when running in a container).
- PORT — (Dev Optional) Port to access the app (e.g. http://localhost:8000).
- DEBUG — (Dev Optional) Set to 1 to enable debug mode (detailed error logs, hot reload, etc). Set to 0 for production use.
- RELOADER — (Dev Optional) Set to 1 to auto-reload the app when files change.
- TESTRUN — (Optional) Set to 1 to trigger app-specific test logic (if implemented).
- MAX_FILE_SIZE — (Required) Max size (in MB) of a log file before rotation occurs (e.g. 25).
- LOGGING — (Required) If 1, enables file logging via the internal LogManager. Set to 0 to log only to stdout.
- USE_MACVLAN — (Linux/Docker Optional) If 1, assigns a static IP to the container via a macvlan network.
- DOCKER_NET_NAME — (Required if using macvlan) Name of your macvlan Docker network (e.g. pi-macnet).
- CONTAINER_IP — (Required if using macvlan) Static IP to assign to the container on your LAN (e.g. 192.168.1.201).
<br><br>

## Contribution Guidelines

Contributions are welcome, but please open an issue or discussion first. Just reach out first 
I am open to new ideas and visions, but N.A.A.R.I has a clear vision in mind and contributions should align with it.
<br><br>


## License

This project is dual-licensed:

MIT License → Free for personal, educational, and open-source use

Commercial License → Required for any commercial use (including sale of products, services, or applications using N.A.A.R.I)

📩 For commercial licensing inquiries, for now, please open a ticket at:
NAARI GitHub Issues
