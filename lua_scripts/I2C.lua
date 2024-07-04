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
    if not size then return nil end
    for idx = 1, size do
        bytes[idx - 1] = arduino_i2c:read_registers(idx)
    end
    return bytes
end

-- Function to get string from character buffer
local function get_string(b)
    if type(b) ~= 'table' then return ERROR_STRING end
    if not b[0] then return ERROR_STRING end
    local str = ''
    for x = 0, #b do
        str = str .. string.char(b[x])
    end
    return str
end

-- Function to update and send data
function update()
    -- Read data from both I2C buses
    local data_0 = read_register_data(arduino_i2c_0)
    local data_1 = read_register_data(arduino_i2c_1)

    -- Check if received data is 'Tested' or 'ERROR' and send appropriate messages
    if get_string(data_0) == 'Tested' then
        gcs:send_text(MAV_SEVERITY_INFO, "I2C2: Tested")
    else
        gcs:send_text(MAV_SEVERITY_INFO, "I2C2: ERROR")
    end

    if get_string(data_1) == 'Tested' then
        gcs:send_text(MAV_SEVERITY_INFO, "I2C1: Tested")
    else
        gcs:send_text(MAV_SEVERITY_INFO, "I2C1: ERROR")
    end

    return update, RUN_INTERVAL_MS
end

-- Initialize script
gcs:send_text(MAV_SEVERITY_INFO, 'I2C test script: Active')

return update, RUN_INTERVAL_MS
