-- This script scans for a specific device on the I2C bus

---@diagnostic disable: need-check-nil

local target_address = 0x74
local found = false

local i2c_bus = i2c:get_device(0,0)
i2c_bus:set_retries(10)

-- Function to check if a device is present at a given address
local function check_device(i2c_bus, address)
    i2c_bus:set_address(address)
    return i2c_bus:read_registers(0)
end

-- Function to send a message through GCS
local function send_gcs_message(level, message)
    gcs:send_text(level, message)
end

-- Function to scan for the target device on the I2C bus
local function scan_i2c_bus()
    if check_device(i2c_bus, target_address) then
        send_gcs_message(0, "I2C2 PORT:Device 0x74 found")
        send_gcs_message(0, "I2C2 PORT: Tested")
        found = true
    else
        send_gcs_message(0, "I2C2 PORT:Device 0x74 not found")
        send_gcs_message(0, "I2C2 PORT: ERROR")
    end
end

-- Main update function that runs periodically
local function update()
    scan_i2c_bus()
    return update, 2000 -- Reschedule the loop
end

-- Run the update function immediately before starting to reschedule
return update()
