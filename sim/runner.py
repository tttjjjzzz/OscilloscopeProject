"""Shared cocotb build/run helper.

Uses cocotb's Python runner instead of the classic Makefile flow, because Make
on Windows means MSYS2 plus path-translation headaches. Driven by pytest:

    py -m pytest sim/ -v
    py -m pytest sim/ -k trigger -v

Each testbench file defines a thin pytest function that calls run_sim().
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from cocotb_tools.runner import get_runner  # cocotb >= 2.0
except ImportError:  # pragma: no cover
    from cocotb.runner import get_runner  # cocotb 1.8.x

REPO = Path(__file__).resolve().parent.parent
RTL = REPO / "rtl"

SIM = os.getenv("SIM", "icarus")


def run_sim(
    *,
    sources: list[Path],
    hdl_toplevel: str,
    test_module: str,
    parameters: dict | None = None,
    waves: bool = True,
    build_dir: Path | None = None,
    timescale: tuple[str, str] = ("1ns", "1ps"),
) -> None:
    """Build and run one testbench.

    sources        .sv files, DUT last is fine, order does not matter for icarus
    hdl_toplevel   module name of the DUT
    test_module    python module holding the @cocotb.test() coroutines
    parameters     SV parameter overrides, e.g. {"DEPTH": 64}
    waves          dump a .fst for GTKWave
    """
    runner = get_runner(SIM)

    suffix = ""
    if parameters:
        suffix = "_" + "_".join(f"{k}{v}" for k, v in sorted(parameters.items()))

    build_dir = build_dir or (Path(__file__).parent / "sim_build" / f"{hdl_toplevel}{suffix}")

    build_args = []
    if SIM == "icarus":
        # -g2012 selects the SystemVerilog-2012 subset icarus supports.
        build_args += ["-g2012"]

    runner.build(
        sources=[str(s) for s in sources],
        hdl_toplevel=hdl_toplevel,
        parameters=parameters or {},
        build_args=build_args,
        build_dir=str(build_dir),
        timescale=timescale,
        waves=waves,
        always=True,
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module=test_module,
        build_dir=str(build_dir),
        waves=waves,
    )


def rtl(*parts: str) -> Path:
    """rtl('capture', 'ring_buffer.sv') -> <repo>/rtl/capture/ring_buffer.sv"""
    return RTL.joinpath(*parts)
