# STATUS

Last updated: 2026-08-24

Keep this current. It's the file Claude reads first, and it's how future-you
remembers what present-you already figured out.

## Where I am

**Current milestone:** M0 — FPGA signal generator
**Started:** 2026-08-24
**Blocked on:** nothing
**Next action:** NCO-vs-divider comparison, then `sync_debounce` + its testbench. Quartus installing in background.

M0:
-Finished the Synchronized Debouncer module, and verified 5/5 tests

## Environment

**Workstation — Windows 11.** Code, synthesis, simulation, CAD.

| Thing | Detail |
|---|---|
| Repo path | `C:\Users\Tiger\Documents\GitHub\OscilloscopeProject` |
| Quartus | installing — Prime Lite, Cyclone V device support only |
| Simulator | Icarus Verilog 14.0 (devel) |
| cocotb | 2.0.1 — **2.x API, not 1.x** |
| Python | 3.12.10 in `.venv` (3.14 also installed, unusable for cocotb) |
| STM32 toolchain | not installed yet |
| GitHub remote | https://github.com/tttjjjzzz/OscilloscopeProject |

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
| STM32 board | Nucleo-G474RE |
| ADC | AD9226 module (M4) |
| Transport | FT232H → Pi (M4) |

## Setup checklist

- [x] Repo path settled — no spaces, not OneDrive-redirected
- [ ] Long path support enabled
- [ ] Quartus installed with Cyclone V device support
- [ ] USB-Blaster II driver working, board detected in Programmer
- [x] Python venv + `requirements.txt` installed
- [x] `iverilog -V` works
- [x] `cocotb-config --version` works
- [x] **`python -m pytest sim/examples -v` passes** — 4/4
- [ ] `arm-none-eabi-gcc --version` works
- [ ] ST-LINK detected
- [x] First commit pushed

Pi (needed from M2):

- [ ] Pi OS 64-bit installed, hostname `scope`
- [ ] `ssh tiger@scope.local` works from Windows
- [ ] Repo cloned to `~/scope`, venv + requirements installed
- [ ] `dialout` and `plugdev` group membership set
- [ ] `scripts/deploy.ps1` runs end to end

## Milestone log

| M | Name | Status | Tag | Closed |
|---|---|---|---|---|
| 0 | Signal generator | in progress — `sync_debounce` done (1/5 modules) | — | — |
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
| Python 3.12, not 3.14 | cocotb ships C extensions; wheels lag new CPython releases by months |
| `` `timescale 1ns / 1ps `` at the top of every `.sv` | Without it Icarus defaults to 1 s precision and cocotb clocks round to zero |
| Repo stays at its current path | No spaces, not OneDrive-redirected, well under the path limit. Settled — not revisiting. |
| Nucleo-G474RE as instrument MCU | HRTIM for narrow-pulse generation, FDCAN for M9 decode, buffered DAC for M3 stimulus |

FOR M0
Decision: Every input goes through a 2ff synchronizer + debouncer
Why: clock relationshpi, make sure we line up
Decision: await ReadOnly() before every assert in cocotb
Why: RisingEdge wakes before the NBA queue update pahse, so reads return PRE-EDGE values
Decision: Using a counter divider, not NCO, for siggen_core
Why: Because every output clock period is exactly N clocks, no jitter, which NCO would cause
Decision: from above decision, this leads to a 500Khz ceiling, and this keeps a 1% duty ceiling at every achievable frequency.


## Open questions

- `siggen_core`: NCO vs counter-divider. Roadmap wants 1 Hz–10 MHz *and* 1% duty
  steps; at 10 MHz there are only 5 clocks/period so duty quantizes to 20%
  regardless. Decide which spec bends.
- `DEBOUNCE_CYCLES` for the real board is a guess (50k = 1 ms @ 50 MHz). Measure
  actual DE0-CV KEY/SW bounce with the M2 logic analyzer and set it from data.

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
| 2026-08-24 | `pip install` → "Failed to build 'cocotb' when getting requirements to build wheel" | Python 3.14 — cocotb has C extensions and no wheels that new, so pip fell back to compiling with no MSVC present | Installed 3.12 alongside, rebuilt venv with `py -3.12 -m venv .venv` |
| 2026-08-24 | All 4 cocotb tests fail at 0.00 ns: "Unable to accurately represent 10(ns) with the simulator precision of 1e0" | No `` `timescale `` in the `.sv`, so Icarus defaulted to 1 s precision and the 10 ns clock rounded to zero | Added `` `timescale 1ns / 1ps `` at the top of the `.sv`, plus `timescale=("1ns", "1ps")` in `runner.py`'s build call |
| 2026-08-24 | `iverilog` not recognized after installing | PATH checkbox missed in the installer | `[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\iverilog\bin;C:\iverilog\gtkwave\bin", "User")`, then a new shell |
