//Превращает номер состояния в узор светодиодов
module state_to_leds (
    input      [1:0] state,
    output reg [2:0] leds
);
    always @(*) begin
        case (state)
            2'b00:   leds = 3'b111;
            2'b01:   leds = 3'b110;
            2'b10:   leds = 3'b100;
            2'b11:   leds = 3'b000;
            default: leds = 3'b111;
        endcase
    end
endmodule