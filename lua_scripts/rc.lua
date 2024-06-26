-- Define message severity level
local MAV_SEVERITY_INFO = 6
local initial_delay = 5000 -- Delay in milliseconds (5 seconds)
local last_check_time = 0
local initial_check_done = false

-- This function checks if the radio controller is connected
local function check_rc_connection()
    if rc:has_valid_input() then
        gcs:send_text(MAV_SEVERITY_INFO, "Radio Disonnected")
    else
        gcs:send_text(MAV_SEVERITY_INFO, "Radio Connected")
    end
end

-- Initial state as Radio Disconnected
gcs:send_text(MAV_SEVERITY_INFO, "Radio Disconnected")

-- Main loop function with initial delay
function update()
    local now = millis()

    if not initial_check_done then
        if now > initial_delay then
            check_rc_connection()
            initial_check_done = true
            last_check_time = now
        end
    else
        if now - last_check_time > 1000 then -- Checks the RC connection status every 1000 milliseconds (1 second)
            check_rc_connection()
            last_check_time = now
        end
    end

    return update, 100 -- Schedule the next update call in 100 milliseconds
end

return update()
