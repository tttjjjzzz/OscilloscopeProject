# scope

A digital oscilloscope built from an FPGA, an MCU, and a Linux SBC.

> Work in progress. Current milestone in [`docs/STATUS.md`](docs/STATUS.md).

## What it is

| Block | Hardware | Role |
|---|---|---|
| Front end | Custom 4-layer PCB | Protection, ÷1/÷10/÷100 compensated attenuator, buffer, PGA, anti-alias filter |
| ADC | AD9226, 12-bit | 65 MSa/s |
| Acquisition | Terasic DE0-CV, Cyclone V 5CEBA4 | Trigger engine, circular buffer, decimation, SDRAM deep memory |
| Control | STM32 | Instrument state machine, AFE control, calibration, test signal generation |
| Host | Raspberry Pi 5 | Transport, DSP, measurements, GUI, protocol decode |

Samples move FPGA → Pi directly over an FT232H in synchronous FIFO mode. The
STM32 sits on a separate control path and never touches sample data.

## Measured specs

Filled in as milestones close. Empty means not yet measured.

| Parameter | Measured |
|---|---|
| Sample rate | |
| Resolution | |
| Analog bandwidth (−3 dB) | |
| Single-shot usable bandwidth | |
| ENOB | |
| Memory depth | |
| Waveform update rate | |
| Transport throughput | |
| Gain error after calibration | |
| Minimum visible glitch at 100 ms/div | |

⚠ **No mains isolation.** Ground is common with the host. Do not connect to
line-referenced circuits.

## Layout

```
rtl/          SystemVerilog, by block
sim/          cocotb testbenches, pytest-driven
fw/           STM32 firmware
host/         Pi-side transport, DSP, GUI
hw/           KiCad analog front end
docs/         roadmap, status, protocol spec, setup
constraints/  .sdc timing constraints and pin assignments
scripts/      build and report helpers
```

## Building

Setup: [`docs/setup-windows.md`](docs/setup-windows.md)

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt

py -m pytest sim/examples -v    # verify toolchain
py -m pytest sim/ -v            # all testbenches
```

RTL synthesis is done in the Quartus GUI against `constraints/`.

## Milestones

| M | Deliverable | Status |
|---|---|---|
| 0 | FPGA signal generator | |
| 1 | Capture engine, verified in simulation | |
| 2 | 8-channel logic analyzer | |
| 3 | STM32 control plane | |
| 4 | ADC acquisition + FT232H transport | |
| 5 | GUI with sinc interpolation and measurements | |
| 6 | SDRAM deep memory, min/max decimation, advanced triggers | |
| 7 | Analog front end PCB | |
| 8 | Calibration | |
| 9 | Channel 2, protocol decode, VGA standalone mode | |
| 10 | Equivalent-time sampling, libsigrok driver | |

Full detail in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## License

MIT
