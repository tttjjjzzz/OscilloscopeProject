"""Toolchain validation testbench.

Run it before M0:

    py -m pytest sim/examples -v

If this passes, icarus + cocotb + the runner all work. Copy this file's shape
when you write the real testbenches in M1 -- the pytest wrapper at the bottom
is the part that matters.

Written against cocotb 2.x (note `unit=`, not `units=`).
"""

import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runner import run_sim  # noqa: E402

WIDTH = 8


async def reset(dut, cycles: int = 2):
    dut.rst_n.value = 0
    dut.en.value = 0
    await Timer(1, unit="ns")
    for _ in range(cycles):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset_clears_count(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)
    assert int(dut.count.value) == 0, f"count should be 0 after reset, got {int(dut.count.value)}"


@cocotb.test()
async def test_counts_when_enabled(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    dut.en.value = 1
    for expected in range(1, 17):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.count.value) == expected, (
            f"expected {expected}, got {int(dut.count.value)}"
        )


@cocotb.test()
async def test_holds_when_disabled(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    dut.en.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    held = int(dut.count.value)

    dut.en.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert int(dut.count.value) == held, "count moved while en was low"


@cocotb.test()
async def test_tick_on_wrap(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset(dut)

    dut.en.value = 1
    saw_tick = False
    for _ in range(2 ** WIDTH + 2):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.tick.value):
            saw_tick = True
            assert int(dut.count.value) == (2 ** WIDTH) - 1, "tick asserted at wrong count"
    assert saw_tick, "tick never asserted across a full wrap"


# ---- pytest entry point -------------------------------------------------
# This is the piece to copy into every real testbench.

def test_counter_runner():
    here = Path(__file__).resolve().parent
    run_sim(
        sources=[here / "counter.sv"],
        hdl_toplevel="counter",
        test_module="test_counter",
        parameters={"WIDTH": WIDTH},
    )
