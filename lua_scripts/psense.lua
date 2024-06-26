local loop_time = 4000

local function send_voltage_current_and_distance()
    local voltage1 = battery:voltage(0) -- Get battery voltage (index 0)
    local current1 = battery:current_amps(0) -- Get battery current (index 0)
    local voltage2 = battery:voltage(1) -- Get battery voltage (index 0)
    local current2 = battery:current_amps(1) -- Get battery current (index 0)
    local distance = 0
    local rangefinder_instance = 0  -- Assuming rangefinder instance 0
    local rf_backend = rangefinder:get_backend(rangefinder_instance)
    if rf_backend then
        distance = rf_backend:distance()  -- Retrieve distance from rangefinder
    else
        gcs:send_text(7, "Rangefinder backend not available")
    end

    -- Display the data on separate lines in the message log
    gcs:send_text(7, string.format("Psense Voltage: %.2f V", voltage1 or 0))
    gcs:send_text(7, string.format("Psense Current: %.2f A", current1 or 0))
    gcs:send_text(7, string.format("Psense AuxVoltage: %.2f V", voltage2 or 0))
    gcs:send_text(7, string.format("Psense AuxCurrent: %.2f A", current2 or 0))
    gcs:send_text(7, string.format("Rangefinder Distance: %.2f cm", distance or 0))

end

function update()
    send_voltage_current_and_distance()
    return update, loop_time
end

return update()