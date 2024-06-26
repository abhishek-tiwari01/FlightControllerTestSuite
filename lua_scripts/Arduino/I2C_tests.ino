#include <Arduino.h>
#include <I2C_Slave.h>

bool isI2CBus0 = true; // Flag to indicate the current I2C bus

void setup() {
    Slave.begin();
}

void loop() {
    if (isI2CBus0) {
        char I2C1[] = "I2C1 Tested!";
        Slave.writeRegisters(I2C1);
    } else {
        char I2C2[] = "I2C2 Tested!";
        Slave.writeRegisters(I2C2);
    }
    
    // Toggle the I2C bus flag
    isI2CBus0 = !isI2CBus0;

    delay(2000); // Adjust delay as needed
}
