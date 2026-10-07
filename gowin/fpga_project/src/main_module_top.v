module main_module_top (
    input Clock,
    input btn_input,
    output led_state
);

    wire press_pulse_wire;

    button_press_detector detector_inst (
        .Clock(Clock),
        .btn_input(btn_input),
        .press_pulse(press_pulse_wire)
    );

    led_toggler toggler_inst (
        .Clock(Clock),
        .toggle_pulse(press_pulse_wire),
        .led_state(led_state)
    );

endmodule //main_module_top
