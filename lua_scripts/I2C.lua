-- Define constants
local RUN_INTERVAL_MS    = 2000
local ERROR_STRING       = 'ERROR'
local MAV_SEVERITY_INFO  = 6

-- Create I2C devices for both buses
local arduino_i2c_0 = i2c.get_device(0, 0x09)
local arduino_i2c_1 = i2c.get_device(1, 0x09)

-- Function to read data from Arduino on a specific I2C bus
local function read_register_data(arduino_i2c)
    local bytes = {}
    local size = arduino_i2c:read_registers(0)
    if not size or size == 0 then return nil end
    local data = arduino_i2c:read_registers(1)
    return data
end

-- Function to convert byte to string
local function get_string(byte)
    if not byte then return ERROR_STRING end
    return string.char(byte)
end

-- Function to update and send data
function update()
    -- Read data from both I2C buses
    local data_0 = read_register_data(arduino_i2c_0)
    local data_1 = read_register_data(arduino_i2c_1)

    -- Log data read for debugging purposes
    gcs:send_text(MAV_SEVERITY_INFO, "Data read from I2C0: " .. tostring(get_string(data_0)))
    gcs:send_text(MAV_SEVERITY_INFO, "Data read from I2C1: " .. tostring(get_string(data_1)))

    -- Check if received data matches expected identifiers and send appropriate messages
    if get_string(data_0) == '1' then
        gcs:send_text(MAV_SEVERITY_INFO, "I2C0 GPS2: Tested")
    else
        gcs:send_text(MAV_SEVERITY_INFO, "I2C0 GPS2: ERROR")
    end

    if get_string(data_1) == '1' then
        gcs:send_text(MAV_SEVERITY_INFO, "I2C1 GPS1: Tested")
    else
        gcs:send_text(MAV_SEVERITY_INFO, "I2C1 GPS1: ERROR")
    end

    return update, RUN_INTERVAL_MS
end

-- Initialize script
gcs:send_text(MAV_SEVERITY_INFO, 'I2C test script: Active')

return update, RUN_INTERVAL_MS
