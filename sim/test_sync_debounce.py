#for testting sync_debounce
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, ReadOnly

from runner import run_sim, rtl

DEBOUNCE = 4   # must match the parameter override below
LATENCY = DEBOUNCE + 2 #since we have a 2ff syncronizer, which yields a delay of 2 clock cycles

async def setup(dut):
    """Start clock, apply reset, leave input low."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.async_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

#counts number of rises. it should be 1, whihc indicated debounce worked
async def count_pulses(dut, sig, out):
    while True:
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(sig.value):
            out.append(1)

@cocotb.test()
async def test_smoke(dut):
    await setup(dut)


#test a clean rise
@cocotb.test()
async def test_clean_rise(dut):
    await setup(dut)
    dut.async_in.value = 1

    #advance DEBOUNCE+1 clock cycles, so right before the level change
    await ClockCycles(dut.clk, LATENCY - 1)
    await ReadOnly()
    assert int(dut.level.value) == 0, f"level flipped early, got {int(dut.level.value)}"
    #advence ONE clock cycle after
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.level.value) == 1, f"level did not flip, expected 1 but got {int(dut.level.value)}"


#test a clean fall
@cocotb.test()
async def test_clean_fall(dut):
    await setup(dut)
    dut.async_in.value = 1  #drive async high initally, so we can test a fall

    #check if async_in is high after LATENCY, if so then were good!
    await ClockCycles(dut.clk, LATENCY)
    await ReadOnly()
    assert int(dut.level.value) == 1, f"level did not get driven high, needs to be driven high first1, we got {int(dut.level.value)}"

    #drive async_in low, and check the state one clk cycle before its action...
    await RisingEdge(dut.clk)
    dut.async_in.value = 0 #drive async_in low here, then we chekc for a falling edege
    await ClockCycles(dut.clk, LATENCY - 1)
    await ReadOnly()
    assert int(dut.level.value) == 1, f"level should still be high, we got {int(dut.level.value)}"
    #now we check if after LATENCY clk cycles 
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.level.value) == 0, f"level did not flip, expected 0 but got {int(dut.level.value)}"



#test an unending bounce.
@cocotb.test()
async def test_short_bounce_ignored(dut):
    await setup(dut)

    for _ in range(5):
        dut.async_in.value = 1
        await ClockCycles(dut.clk, 2)
        dut.async_in.value = 0
        await ClockCycles(dut.clk, 2)
        await ReadOnly()
        assert int(dut.level.value) == 0, f"level must be held a 0, verifying that input was not valid. we got {int(dut.level.value)}"                     # ← yours
        await RisingEdge(dut.clk)


#test a bounce, then held steady

@cocotb.test()
async def test_bounce_then_settle(dut):
    await setup(dut)

    hits = []
    cocotb.start_soon(count_pulses(dut, dut.rise, hits))

    # chatter — same pattern as the previous test
    for _ in range(5):
        dut.async_in.value = 1
        await ClockCycles(dut.clk, 2)
        dut.async_in.value = 0
        await ClockCycles(dut.clk, 2)

    # then settle high and hold
    dut.async_in.value = 1
    await ClockCycles(dut.clk, LATENCY + 5)
    await ReadOnly()

    assert int(dut.level.value) == 1, f"level must end at one, but we got {int(dut.level.value)}"
    assert len(hits) == 1, f"length must be 1, which indicates 1 rise, so debounce acutally worked, but we got {len(hits)}"

def test_sync_debounce_runner():
    run_sim(
        sources=[rtl("siggen", "sync_debounce.sv")],
        hdl_toplevel="sync_debounce",
        test_module="test_sync_debounce",
        parameters={"DEBOUNCE_CYCLES": DEBOUNCE},
    )

