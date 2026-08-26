`timescale 1ns / 1ps

module sync_debounce #(
    parameter int DEBOUNCE_CYCLES = 50_000
) (
    input logic clk,
    input logic rst_n,
    input logic async_in,
    output logic level,
    output logic rise,
    output logic fall
);
    //decalre stuiff

    //block1 variables
    logic [1:0] sync_ff;
    logic sync_in;
    //block 2 variables
    localparam int CW = $clog2(DEBOUNCE_CYCLES); //ceiling log, which yields 16.. suince log2(50000)=15.61
    logic [CW-1:0] count;
    //block 3 variables
    logic level_q //this is the past value of level, one cycle ago.

    //block2
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            sync_ff <= 2'b00;
        end else begin
            //async_in is the button input, and i have a 2ff syncrhonizer, so i am performaing a bit shift here...
            sync_ff <= {sync_ff[0], async_in};
        end
    end

    assign sync_in = sync_ff[1];
    //

    //block 2
    always_ff @(posedge clk) begin
        //check if actual input is equal to what i think it intends to be,.. chekc. uyes
        if(!rst_n) begin
            level <= 1'b0;
            count <= 0;
        end else if(sync_in == level) begin
            count <= 0; //reset counter for next debounce event>
            
        end else if (count ==  DEBOUNCE_CYCLES-1) begin
            count <= 0;
            level <= sync_in;
        end else begin
            count <= count + 1'b1;
        end

    end
    //

    //block 3
    always_ff @(posedge clk) begin
        if(!rst_n) begin
            level_q <= 1'b0;
        end else begin
            level_q <= level;
        end 
    end

    //block4
    assign rise = level && !level_q;
    assign fall = !level && level_q;

    

endmodule