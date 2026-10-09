module led_toggler
(
    input  Clock,
    input  toggle_pulse,
    output led_state
);

reg flag = 1; //init state

always @(posedge Clock) begin
    if ( toggle_pulse ) begin
        flag <= ~flag;
    end
end

assign led_state = flag;

endmodule //led_toggler