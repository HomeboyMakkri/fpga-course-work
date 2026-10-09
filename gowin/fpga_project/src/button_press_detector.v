module button_press_detector
(
    input  Clock,
    input  btn_input, //active - high
    output press_pulse
);
reg previous = 0;
reg now = 0;
reg flag = 0;

always @(posedge Clock) begin
    previous <= now;
    now <= btn_input;
    if ( now == 1 && previous == 0) begin
        flag <= 1;
    end else begin
        flag <= 0;
    end
end

assign press_pulse = flag;

endmodule //button_press_detector
