`timescale 1ns / 1ps

module siggen_core #(
    parameter int CLK_FREQUENCY = 50000000,
    parameter int WIDTH = $clog2(CLK_FREQUENCY)
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             enable,
    input  logic [WIDTH-1:0] duty_count,     // clocks high within the period
    input  logic [WIDTH-1:0] period_count,   // clocks per output period
    output logic             out_level       //this is the output waveform.
);

    //block 1 variables
    logic [WIDTH-1:0] count;


    //Block 1, counter
    always_ff @(posedge clk) begin
        if (!rst_n || !enable || count == period_count-1) begin
            count <= 0;
        end else begin
            count <= count + 1;
        end
    end

    //block 2, assign the output signal
    assign out_level = enable && (count < duty_count);

endmodule