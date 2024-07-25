#include <Arduino.h>
#include <I2C_Slave.h>

void setup() {
    Slave.begin(); // Initialize I2C slave with default address 0x09
    
    // Write "1" to virtual registers to indicate the test data
    char data[] = "1";
    Slave.writeRegisters(data);
}

void loop() {
    // No functionality in loop
}
