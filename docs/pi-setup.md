# Pi 5 — instrument computer

The Pi is not a development machine and not an accessory. It's a component of
the oscilloscope, permanently attached, and it boots into the scope UI.

## Its job

| Milestone | What the Pi does |
|---|---|
| M2 | UART reader, matplotlib timing diagrams |
| M4 | FT232H transport, throughput benchmark |
| M5 | The GUI — pyqtgraph, sinc interpolation, measurements |
| M6 | Zoom/pan through deep memory |
| M8 | Applies calibration constants |
| M9 | Protocol decode overlays |
| M10 | libsigrok backend, SCPI server |

Everything in `host/` targets this machine and only this machine. It is never
run on Windows.

## Hardware

| | |
|---|---|
| Board | Pi 5 (4 GB is enough; 8 GB if you want headroom for deep captures) |
| Storage | NVMe via the M.2 HAT if you have one, else a decent A2 microSD |
| Display | HDMI monitor, or the official 7" DSI touchscreen for a self-contained build |
| Power | The official 27 W USB-C supply. Underpowering a Pi 5 with peripherals attached causes throttling that looks like software bugs. |
| Cooling | Active cooler. Sustained FFT + GUI will thermal throttle a bare board. |

Connected to it: the FT232H (sample data), the STM32 over USB CDC (control),
and its display.

## OS

Raspberry Pi OS 64-bit, current release. 64-bit matters — NumPy and SciPy
wheels are better supported and you want the wider registers for DSP.

```bash
sudo apt update && sudo apt full-upgrade
sudo apt install -y git python3-venv python3-dev build-essential \
                    libftdi1-dev pkg-config
sudo raspi-config          # enable SSH, set hostname to "scope"
```

Setting the hostname to `scope` gets you `ssh tiger@scope.local` from Windows
via mDNS, no IP hunting.

```bash
git clone <your-repo> ~/scope
cd ~/scope
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyftdi          # works natively on Linux, no driver swap
```

## Device permissions

Both of these bite on first run and produce confusing permission errors.

**FT232H** — add a udev rule so you don't need root:

```bash
sudo tee /etc/udev/rules.d/99-ftdi.rules > /dev/null <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0666", GROUP="plugdev"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG plugdev $USER
```

**STM32 USB CDC** — shows up as `/dev/ttyACM0`:

```bash
sudo usermod -aG dialout $USER
```

Log out and back in for group changes to apply. Then verify:

```bash
python3 -c "from pyftdi.ftdi import Ftdi; Ftdi.show_devices()"
ls -l /dev/ttyACM*
```

The device node number moves around if you unplug things. Write a udev rule
giving each a stable symlink (`/dev/scope-ft`, `/dev/scope-mcu`) once you have
both attached — future you will thank present you.

## Standalone boot

Once M5 works, make it boot into the UI so the instrument is usable without a
keyboard.

```ini
# ~/.config/systemd/user/scope-gui.service
[Unit]
Description=Scope GUI
After=graphical-session.target

[Service]
ExecStart=/home/tiger/scope/.venv/bin/python -m gui.main
WorkingDirectory=/home/tiger/scope/host
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
```

```bash
systemctl --user enable --now scope-gui
journalctl --user -u scope-gui -f     # logs, when it misbehaves
```

Enable autologin in `raspi-config` so the graphical session starts unattended.

Pi OS's desktop compositor has changed across releases (X11 → Wayfire → labwc),
so if the service doesn't pick up the display, check which one your release uses
before assuming the unit file is wrong.

## Performance

The Pi 5 is fast enough that pushing DSP into the FPGA is a benchmarking
exercise, not a necessity. A 4096-point NumPy FFT lands comfortably under a
millisecond.

Worth doing once you're chasing update rate:

```bash
# pin to performance governor -- default ondemand adds latency jitter
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

Later, if you want it: `isolcpus` to reserve a core for the acquisition thread,
and a PREEMPT_RT kernel with before/after jitter measurements. That's a good
standalone writeup, but it's parked until the instrument works.

## Getting code onto the Pi

Everything is written and committed on Windows. The Pi just needs the `host/`
code to run.

**Git — the default.** Commit and push on Windows, pull on the Pi:

```bash
cd ~/scope && git pull && python -m gui.main
```

`scripts/deploy.ps1` on the Windows side does the push-pull-restart in one
command so you're not typing it repeatedly.

This is fine for most of the project. `host/` at M2 is a short UART reader you
won't iterate on much, and M4's transport work is mostly debugging on the Pi
side anyway.

**VS Code Remote-SSH — add it only if you need it.** Install the Remote-SSH
extension on Windows and connect to `scope.local`; VS Code opens the Pi's
filesystem directly, so saving *is* deploying. No commits, no pulls.

The only thing this buys you is round-trip time. If you're iterating on GUI
layout thirty times an hour, git-only means thirty commits of "fix typo" and
thirty pulls. That's the point where Remote-SSH pays for itself — probably
around M5. Before that it's unnecessary machinery.

Either way: **don't edit the same file on both machines in one session.** Pick
one and stick with it until you've pushed.

## What stays on Windows

`rtl/`, `sim/`, `fw/`, `hw/` never touch the Pi. FPGA flashing goes over
USB-Blaster from Windows, STM32 flashing over ST-Link from Windows. The Pi only
ever runs `host/`.

Don't install `host/` dependencies on Windows — if pyftdi and pyqtgraph aren't
there, you can't accidentally run host code on the wrong machine and write
something that quietly depends on Windows.

## Verification

| Check | Command | Expected |
|---|---|---|
| Reachable | `ssh tiger@scope.local` | logs in |
| Python | `python3 --version` | 3.11+ |
| NumPy | `python3 -c "import numpy; print(numpy.__version__)"` | prints |
| FT232H visible | `Ftdi.show_devices()` | lists device (after M4) |
| STM32 visible | `ls /dev/ttyACM*` | node present (after M3) |
| Qt display | `python3 -c "import pyqtgraph"` | no error |
