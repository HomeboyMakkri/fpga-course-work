module main_module_top (
    input Clock,
    input clk_10MHz,
    input  btn1_input,
    input  btn2_input,
    output [2:0] first_leds,
    output [2:0] second_leds,
    output pps_out_1,
    output pps_out_2
);

    wire press_pulse_wire_1;
    wire press_pulse_wire_2;

    wire [1:0] state_1;
    wire [1:0] state_2;

    wire [2:0] out_bus_led_1;
    wire [2:0] out_bus_led_2;

    button_press_detector detector_inst_1 (
        .Clock(Clock),
        .btn_input(btn1_input),
        .press_pulse(press_pulse_wire_1)
    );

    button_press_detector detector_inst_2 (
        .Clock(Clock),
        .btn_input(btn2_input),
        .press_pulse(press_pulse_wire_2)
    );

    state_counter state_counter_1 (
        .Clock(Clock),
        .press_pulse(press_pulse_wire_1),
        .state(state_1)
    );

    state_counter state_counter_2 (
        .Clock(Clock),
        .press_pulse(press_pulse_wire_2),
        .state(state_2)
    );

    state_to_leds state_to_leds_1 (
        .state(state_1),
        .leds(out_bus_led_1)
    );

    state_to_leds state_to_leds_2 (
        .state(state_2),
        .leds(out_bus_led_2)
    );

    pps_generator generator_1 (
        .clk_10MHz(clk_10MHz),
        .state(state_1),
        .pps_out(pps_out_1)
    );

    pps_generator generator_2 (
        .clk_10MHz(clk_10MHz),
        .state(state_2),
        .pps_out(pps_out_2)
    );

    assign first_leds [2:0] = out_bus_led_1;
    assign second_leds [2:0] = out_bus_led_2;

endmodule //main_module_top
