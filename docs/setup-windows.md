# Toolchain setup — Windows workstation

This is the **development machine**: writing code, synthesis, simulation, CAD,
research, git. It is not part of the instrument.

The Pi is the instrument computer and runs everything in `host/`. See
[`pi-setup.md`](pi-setup.md). You write and commit `host/` code here; the Pi
pulls it and runs it.

| Lives on Windows | Lives on the Pi |
|---|---|
| `rtl/` — Quartus synthesis | `host/` — transport, DSP, GUI |
| `sim/` — cocotb testbenches | |
| `fw/` — STM32 build and flash | |
| `hw/` — KiCad | |

---

## Before anything: where the repo lives

```
C:\Users\Tiger\Documents\GitHub\OscilloscopeProject
```

Two constraints, both already satisfied:

- **No spaces in any folder name.** Quartus shells out to internal tools that don't always quote paths, so `Oscilloscope Project` gets split into two arguments and you get "file not found" errors pointing at files that plainly exist. This is the one that actually bites.
- **Not inside OneDrive.** Syncing a Quartus project while Quartus has it open causes file-lock errors and corrupted `db/` state — Quartus generates thousands of small files per compile and sync clients choke.

Documents on Windows 11 is often OneDrive-redirected. Verify once:

```powershell
(Get-Item "$env:USERPROFILE\Documents").Target
```

Empty output means not redirected — you're fine where you are. If it returns a
OneDrive path, move the repo somewhere outside it.

Path length is not a concern at this depth; Quartus nests maybe 60-80 chars
beyond your base and the limit is 260. Enable long path support anyway, it costs
nothing:

```powershell
# elevated PowerShell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
git config --global core.longpaths true
```

---

## 1. Quartus Prime Lite

Free, no license file needed. Get it from Altera/Intel's download page.

- Version: 23.1std or newer
- **Device support: Cyclone V** — it's a separate checkbox in the installer and a separate multi-GB download. Miss it and the DE0-CV won't be selectable.
- Include **Questa Intel Starter FPGA Edition** if offered. Free, and it's your fallback simulator (see §3).
- Include **USB-Blaster II driver**

After install, plug in the DE0-CV and check Device Manager. If it shows as an unknown device, point the driver update at:

```
C:\intelFPGA_lite\<version>\quartus\drivers\usb-blaster-ii
```

**Verify:** Quartus → Tools → Programmer → Hardware Setup should list `DE-SoC` or `USB-BlasterII`.

---

## 2. Python

Install from python.org (not the Microsoft Store version — it sandboxes paths in ways that break tooling). Check "Add to PATH".

```powershell
cd "$env:USERPROFILE\Documents\GitHub\OscilloscopeProject"
py -m venv .venv
.venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

On Windows you invoke Python as `py`, not `python3`.

---

## 3. Simulator

This is the one decision worth thinking about for ten minutes.

### Icarus Verilog — start here

Get the Windows installer from the bleyer.org builds (the standard community Windows distribution of iverilog). Check "Add to PATH" during install.

```powershell
iverilog -V
```

**The catch: Icarus supports only a subset of SystemVerilog.** With `-g2012` you get `logic`, `always_ff` / `always_comb`, `typedef enum`, packed structs, and most of what you'll actually write. You do *not* reliably get interfaces, packages with complex contents, or some parameterization patterns. I'm not going to pretend I know exactly where every boundary sits across versions — **run the example test in `sim/examples/` on day one to find out where yours breaks.**

Practical approach: write in the conservative SV subset. It's better RTL style anyway — interfaces and fancy parameterization tend to obscure what's actually being synthesized, which is the opposite of what you want while learning.

### Questa Intel Starter — the fallback

Bundled with Quartus, free, full SystemVerilog support, and cocotb supports it. Slower to set up and it has a line-count limit on the free edition. Switch to it if Icarus rejects something you actually need.

### Verilator — later, if sims get slow

Much faster, excellent SV support, but it's cycle-based rather than event-driven and needs a C++ toolchain on Windows. Not worth it at M1. Revisit if your SDRAM testbenches start taking minutes.

### GTKWave

Waveform viewer. Windows builds ship alongside the Icarus installer. You'll live in this during M1.

---

## 4. cocotb

```powershell
py -m pip install cocotb pytest
cocotb-config --version
```

**Use the Python runner, not a Makefile.** cocotb's classic flow is Make-based, which on Windows means installing MSYS2 or GnuWin32 make and then fighting path translation. The Python runner API skips all of that and is driven by pytest — see `sim/runner.py`.

The runner module moved between cocotb versions (`cocotb.runner` in 1.8.x, `cocotb_tools.runner` in 2.x). `sim/runner.py` tries both. If it fails, check `cocotb-config --version` first.

**Verify:**

```powershell
py -m pytest sim/examples -v
```

That runs a throwaway counter module. It exists purely to prove the harness works before you write anything real. If it doesn't pass, fix that before M1 — you do not want to be debugging your toolchain and your first trigger FSM simultaneously.

---

## 5. STM32

Two options:

**STM32CubeCLT** (recommended) — command-line toolchain: `arm-none-eabi-gcc`, `STM32_Programmer_CLI`, OpenOCD, GDB. Pairs with VS Code and works in CI later.

**STM32CubeIDE** — full Eclipse IDE. Easier to start, harder to script.

Either way, install **STM32CubeMX** for pin config and clock tree setup. Its generated HAL init code is fine to keep — that's plumbing, not the part you're learning.

Also install **ST-LINK drivers** (bundled with either).

For the host-side unit tests (`fw/test/`), you need a native compiler:

```powershell
winget install BriechleSoftware.MinGW-w64
```

Or use MSVC if you already have Build Tools installed.

**Verify:**

```powershell
arm-none-eabi-gcc --version
STM32_Programmer_CLI --version
```

---

## 6. Git

```powershell
git config --global core.autocrlf true
git config --global init.defaultBranch main
```

`.gitattributes` in this repo overrides autocrlf where it matters (`.py`, `.sh` stay LF for the Pi). Don't skip it — CRLF in a Python file that runs on the Pi produces confusing failures.

---

## 7. FT232H — not your problem

The FT232H plugs into the **Pi**, not this machine. `libftdi` works natively on
Linux with a one-line udev rule.

Worth knowing why that's lucky: on Windows, FTDI chips default to the D2XX/VCP
driver, which claims the device exclusively. `pyftdi` needs libusbK or WinUSB
instead, swapped with Zadig — and afterward that device stops being a COM port,
with a real risk of nuking the driver for a different FTDI adapter you use
daily. Keeping transport on the Pi sidesteps all of it.

Don't install `pyftdi` on Windows. If it's not here, you can't accidentally
start running host code on the wrong machine.

## 8. VS Code

Your editor for everything — `rtl/`, `sim/`, `fw/`, `host/`. Useful extensions:

- **Verilog-HDL/SystemVerilog** for `rtl/`
- **Python** for `sim/` and `host/`
- **Cortex-Debug** if you want in-editor STM32 debugging

**Remote - SSH** is optional and worth adding later. Default workflow is
git: write on Windows, commit, pull on the Pi. Remote-SSH only saves round
trips when you're iterating on `host/` code many times an hour — realistically
around M5, when you're fiddling with GUI layout. See
[`pi-setup.md`](pi-setup.md).

---

## Verification checklist

| Check | Command / action | Expected |
|---|---|---|
| Repo path | `(Get-Item "$env:USERPROFILE\Documents").Target` | empty = not OneDrive-redirected |
| Quartus | Tools → Programmer → Hardware Setup | `USB-BlasterII` listed |
| Cyclone V support | New project wizard, device family list | Cyclone V present |
| Python | `py --version` | 3.11+ |
| Icarus | `iverilog -V` | version prints |
| cocotb | `cocotb-config --version` | version prints |
| **Harness** | `py -m pytest sim/examples -v` | **passes** |
| ARM GCC | `arm-none-eabi-gcc --version` | version prints |
| ST-LINK | `STM32_Programmer_CLI --version` | version prints |
| Board | Quartus Programmer, blink demo | LEDs respond |

Everything green → start M0.

---

## The Pi

Set it up alongside this machine, not later — see [`pi-setup.md`](pi-setup.md).
It first does real work at M2 (UART readout and plotting), and you want the
deploy loop working before there's real data flowing through it.

Don't substitute Windows for the Pi on host code. Running the GUI on Windows
"just to test it" is how you end up with code that only works on Windows and a
Pi that never becomes the instrument.

## The Arch box

`greedIsland` is optional here. Quartus Lite runs on Linux and Icarus/cocotb are
less fussy there, so if Windows tooling starts eating your time, moving
simulation over via SSH is a reasonable escape hatch. Sync through GitHub, not a
shared folder.
