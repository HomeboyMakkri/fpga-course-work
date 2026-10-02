module main_module_top 
(
    input Clock,
    output wire [5:0] led_bus
);
//parameter Clock = 27_000_000
parameter count_value = 13_499_000;

reg [23:0] count_value_reg;  //counter
reg        count_value_flag; //flag

always @(posedge Clock) begin
    if ( count_value_reg == count_value ) begin //not count
        count_value_reg <= 0;
        count_value_flag <= 1'b1;
    end
    else begin //Count to 0.5S
        count_value_reg <= count_value_reg + 1'b1;
        count_value_flag <= 1'b0; 
    end
end

reg [5:0] IO_voltage_reg = 6'b000000; //init state

always @(posedge Clock) begin
    if ( count_value_flag ) // FF 
        IO_voltage_reg <= ~IO_voltage_reg;
    else 
        IO_voltage_reg <= IO_voltage_reg;
end

assign led_bus[5:0] = IO_voltage_reg[5:0];

endmodule //main_module_top