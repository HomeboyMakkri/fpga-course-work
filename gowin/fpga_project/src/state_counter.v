//	Хранит номер состояния (0..3) и увеличивает его по импульсу
module state_counter
(
    input            Clock,
    input            press_pulse,
    output reg [1:0] state = 2'b00
);

    always @(posedge Clock) begin
        if ( press_pulse ) begin
            state <= state + 1'b1;
        end
    end
endmodule //state_counter