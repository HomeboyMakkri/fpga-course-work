module pps_generator
(
    input clk_10MHz,
    input wire [1:0] state,
    output pps_out
);

    reg [23:0] counter = 0;
    reg [23:0] threshold;

    reg        count_value_flag = 1'b0;

    always @( posedge clk_10MHz ) begin
        if ( state == 2'b00 ) begin
            counter <= 0;
            count_value_flag <= 0;
        end
        else begin
            if ( counter <= threshold ) begin
                counter <= counter + 1'b1;
                count_value_flag <= 1'b0; // no flip flag
            end
            else begin
                counter <= 23'b0;
                count_value_flag <= 1'b1;
            end
        end
    end

    always @(*) begin
       case ( state )
            2'b01:   threshold = 24'd4_999_999; // 1 PPS
            2'b10:   threshold = 24'd499_999;   // 10 PPS
            2'b11:   threshold = 24'd49_999;    //100 PPS
            default: threshold = 24'd0;
       endcase
    end

    reg IO_voltage_reg = 1'b0;

    always @(posedge clk_10MHz) begin
        if ( state == 2'b00 ) begin
            IO_voltage_reg <= 1'b0;
        end else begin
            if ( count_value_flag )
                IO_voltage_reg <= ~IO_voltage_reg; // IO voltage flip
            else
                IO_voltage_reg <= IO_voltage_reg;
            end
    end

    assign pps_out = IO_voltage_reg;

endmodule // pps_generator
