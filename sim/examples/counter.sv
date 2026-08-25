// Toolchain validation only. Not part of the scope design.
// If this does not simulate, fix your setup before starting M0.

module counter #(
    parameter int WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             en,
    output logic [WIDTH-1:0] count,
    output logic             tick
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= '0;
        end else if (en) begin
            count <= count + 1'b1;
        end
    end

    assign tick = en && (count == {WIDTH{1'b1}});

endmodule
