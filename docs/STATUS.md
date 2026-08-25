# STATUS

Last updated: 2026-08-24

Keep this current. It's the file Claude reads first, and it's how future-you
remembers what present-you already figured out.

## Where I am

**Current milestone:** M0 — FPGA signal generator
**Started:** —
**Blocked on:** nothing yet
**Next action:** finish toolchain setup, get `py -m pytest sim/examples -v` passing

## Environment

**Workstation — Windows 11.** Code, synthesis, simulation, CAD.

| Thing | Detail |
|---|---|
| Repo path | `C:\dev\scope` |
| Quartus | Prime Lite ___ |
| Simulator | Icarus ___ / Questa Intel Starter ___ |
| cocotb | ___ |
| Python | ___ |
| STM32 toolchain | ___ |
| GitHub remote | ___ |

**Instrument computer — Pi 5.** Runs `host/`. Permanently part of the scope.

| Thing | Detail |
|---|---|
| Model / RAM | Pi 5, ___ GB |
| OS | ___ |
| Hostname | `scope.local` |
| Repo path | `~/scope` |
| Display | ___ |
| Storage | ___ |

**Instrument hardware**

| Thing | Detail |
|---|---|
| FPGA board | Terasic DE0-CV, Cyclone V 5CEBA4F23C7N |
| STM32 board | ___ |
| ADC | AD9226 module (M4) |
| Transport | FT232H → Pi (M4) |

## Setup checklist

- [ ] Repo at a short path, not in OneDrive
- [ ] Long path support enabled
- [ ] Quartus installed with Cyclone V device support
- [ ] USB-Blaster II driver working, board detected in Programmer
- [ ] Python venv + `requirements.txt` installed
- [ ] `iverilog -V` works
- [ ] `cocotb-config --version` works
- [ ] **`py -m pytest sim/examples -v` passes**
- [ ] `arm-none-eabi-gcc --version` works
- [ ] ST-LINK detected
- [ ] First commit pushed

Pi (needed from M2):

- [ ] Pi OS 64-bit installed, hostname `scope`
- [ ] `ssh tiger@scope.local` works from Windows
- [ ] Repo cloned to `~/scope`, venv + requirements installed
- [ ] `dialout` and `plugdev` group membership set
- [ ] `scripts/deploy.ps1` runs end to end

## Milestone log

| M | Name | Status | Tag | Closed |
|---|---|---|---|---|
| 0 | Signal generator | in progress | — | — |
| 1 | Capture engine (sim) | not started | — | — |
| 2 | Logic analyzer | not started | — | — |
| 3 | STM32 control plane | not started | — | — |
| 4 | ADC + FT232H | not started | — | — |
| 5 | GUI | not started | — | — |
| 6 | Deep memory + triggers | not started | — | — |
| 7 | AFE PCB | not started | — | — |
| 8 | Calibration | not started | — | — |
| 9 | Ch2 + decode + VGA | not started | — | — |
| 10 | ETS + sigrok | not started | — | — |

## Measured numbers

| Metric | Value | Milestone | Date |
|---|---|---|---|
| LEs / registers / M10K / DSP | | | |
| Fmax, worst setup slack | | | |
| Transport throughput | | | |
| SNR / ENOB, pre-AFE baseline | | | |
| SNR / ENOB, post-AFE | | | |
| Waveform update rate | | | |
| Capture depth | | | |
| Min visible glitch @ 100 ms/div | | | |
| −3 dB BW per range | | | |
| Gain error, pre/post cal | | | |
| ETS effective sample rate | | | |

## Decisions made

Settled. Don't relitigate without a reason.

| Decision | Why |
|---|---|
| FPGA → Pi direct over FT232H; STM32 on a separate control path | STM32 USB FS caps near 1 MB/s, which would bottleneck the whole instrument |
| cocotb Python runner instead of Makefiles | Avoids MSYS2/make path translation on Windows |
| Buy a reference scope before M7 | Compensated attenuator trimmers cannot be tuned blind |
| Conservative SystemVerilog subset | Icarus SV support is partial; also better RTL style while learning |
| | |

## Open questions

-

## Parked

Deliberately not doing yet. Revisit only when the current milestone is closed.

- HMCAD1511 (8-bit, 1 GSa/s LVDS) as a v2 front end
- FPGA FFT — M10, benchmarking exercise only
- PREEMPT_RT kernel on the Pi with jitter measurements
- Kernel-space driver replacing the libftdi userspace path
-

## Scars

Things that broke and what fixed them. This table pays for itself.

| Date | Symptom | Cause | Fix |
|---|---|---|---|
| | | | |
