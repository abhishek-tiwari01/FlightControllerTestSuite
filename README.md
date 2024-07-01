# FlightControllerTestSuite

## Overview
`FlightControllerTestSuite` is a comprehensive testing framework designed to automate the validation and verification of flight controllers. This framework supports various tests, including hardware interfacing through MAVProxy, ADB, GPIO configuration, and serial communication.

The structure includes:
- Firmware loaders and testers.
- Script utilities for automated report generation.
- Test scenarios and configurations that are easy to adapt and extend.

## Features
- **Firmware Loading**: Automates the process of loading firmware onto devices under test.
- **MAVProxy Integration**: Leverages MAVProxy for real-time interaction with flight controllers.
- **Automated Reporting**: Generates detailed test reports in PDF format, facilitating easy documentation and review.
- **Modular Design**: Designed to be modular, allowing testers to add new tests as needed without affecting existing functionality.

## Repository Structure
```
FlightControllerTestSuite/

   ├── firmware/ # Firmware files and scripts
   │ ├── ArducopterTest4.6.0-dev_images/bin/arducopter.apj
   │ ├── ArducopterFinal4.5.2_images/bin/arducopter.apj
   │ └── uploader.py
   ├── scripts/ # Test and report generation scripts
   │ ├── main_test_script.py
   │ ├── generate_reports.py
   │ └── report_template.html
   ├── images/ # Images for reports
   │ └── cube.jpg
   ├── setup.sh # Setup script
   ├── lua_scripts/ # Lua scripts for SD card
   │ ├── rc.lua
   │ ├── psense.lua
   │ ├── I2C.lua
   │ └── Arduino
   │     └── I2C_tests.ino
   └── README.md # Documentation
```

## Installation

### Prerequisites
- Python 3.10
- Git
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10
sudo apt install git
```
### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/abhishek-tiwari01/FlightControllerTestSuite.git
   cd FlightControllerTestSuite
   chmod -R +x .

   ```

2. **Run the Setup Script**:
   This script will install Docker, add the user to the Docker group, and build the Docker image.
   ```
   sudo ./setup.sh
   ```
Also, Install following pip packages:
```
pip3 install PyYAML mavproxy jinja2 weasyprint pyserial colorama pymavlink
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
```

3. **Test Environment Setup**:
**Hardware Connections**
Connect your Cube Orange and Flight Computer to the host machine via USB Cables.
Ensure all necessary peripherals are connected (e.g., FCU Testjig, SPPM Module, Safety Switch).

**SD Card Setup**
Make Sure, Ready SD Card with Lua Scripts loaded is inserted before Running 
Once, the SD Card is prepared with Lua Scripts, it can be used across all the FCUs by swapping.

Preparing the SD Card:
Take SD Card from Cube Orange Plus FCU
Insert an SD card into your computer.
Create the APM/scripts Directory:
Copy Lua Scripts:
Copy the provided Lua scripts provided in the lua_scripts directory in repo (rc.lua, psense.lua, I2C.lua) to the APM/scripts directory in SD Card.
Open MissionPlanner, Establish Connection of MissionPlanner with FCU.
Go to Config >> MAVFtp >> APM >> scripts ( Right Click and Upload all three scripts (rc.lua, psense.lua, I2C.lua))



### 4. Test_procedure

## Initial Setup

1. **Place the New Cube with Add-on board on IFB connected with Add-on board Testjig and LS testjig.**
2. **Ensure the add-on board test jig has a working Arduino Nano loaded with I2C scripts and the IFB board is loaded with Add-on Board Flatbuild image/firmware.**
3. **Connect the following components:**
   - **USB**
   - **Serial1**
   - **CAN1**
   - **CAN2**
   - **PSense**
   - **FrSky**
   - **GPS1 with safety switch**
   - **GPS2**
   - **I2C2**
   - **ADC**
   - **LED relay**
   - **PPM and SBUSo with SPPM Module**
4. **Swap the SD card loaded with Lua script into the Cube.**
5. **Power On the System.**
6. **Connect the IFB with Type-C and the add-on test jig with microUSB to the Host-PC.**
7. **Open Terminal and start the test by running the following command inside the `FlightControllerTestSuite` directory:**
   ```
   python3 scripts/main_test_script.py
   ```

## Menu Options

You will be presented with the following menu:
```
Select an option:
1. Test All Interfaces
2. Load Release Firmware
3. Load Test Firmware
4. Psense Cable Test
Enter your choice (1/2/3/4):
```

## Option 1: Test All Interfaces

1. **Select Option 1: Press 1 and Press Enter.**
   ```
   Enter your choice (1/2/3/4): 1
   Scan QR code on the board: QR
   QR code scanned: QR
   ```

2. **Scan the QR code of the add-on board with the QR code scanner. Ensure the cursor is placed at the QR scanning input in the terminal.**

3. **Test will Autostart: Load Test Firmware.**
   ```
   Loading Test firmware...
   Loaded firmware for 427,0, size: 1835112 bytes, waiting for the bootloader...
   ...
   Test Firmware loaded.
   Vehicle: Copter, Firmware version: dev-4.6.0
   ```

4. **MAVProxy tests (PSense, I2C, and ADC).**
   Ensure the SD card is loaded with the Lua script and hardware connections are proper.
   ```
   Run Psense Tests:
   Psense Voltage: FAIL
   Psense Current: FAIL
   PSENSE Overall: FAIL
   ADC: FAIL
   I2C2: PASS
   I2C1: PASS
   Psense Voltage: PASS
   Psense Current: PASS
   PSENSE Overall: PASS
   ADC: PASS
   ```
   Some tests might initially FAIL but should eventually PASS. If not, close the test and repeat.

6. **Main and Aux out tests.**
    Press Enter twice to proceed. Observe each LED. They will glow one by one. Provide the input (y/n) and press Enter.
   ```
   Press Enter twice to Proceed for MAIN & AUX Out tests:
   Press if MAIN OUT 1-4 LEDs are glowing (y/n): y
   Press if MAIN OUT 5-8 LEDs are glowing (y/n): y
   Press if AUX OUT 1-6 LEDs are glowing (y/n): y
   ```

8. **PPM and SBUS test.**
   Press the safety switch until it starts flashing.
   ```
   Reading MAVProxy output for radio status...
   Hold the safety switch until it Blinks Red, then press Enter.
   Radio Test Completed.
   PPM and SBUSo: PASS
   ```

10. **Serial and CAN test through IFB over ADB.**
   ```
   Starting Serial Tests through Flight Computer...
   Serial 1: PASS
   Serial 2: PASS
   Serial 3: PASS
   Serial 4: PASS
   Serial 5: PASS
   CAN 1: PASS
   CAN 2: PASS
   ```

11. **Load Release Firmware and test Serial 2 Port.**
   ```
   Loading Release firmware...
   Loaded firmware for 427,0, size: 1817396 bytes, waiting for the bootloader...
   ...
   Release Firmware loaded.
   Vehicle: Copter, Firmware version: official-4.5.2
   Serial 2: PASS
   Flight Controller Unit has Completed All the tests and is Ready to use.
   ```

11. **Report Generation:**
   ```
   Generated JSON file with test results at: /home/username/Desktop/Production_Test/<QR>_<date_time>/test_results.json
   Report generation completed successfully.
   ```

## Option 2: Load Release Firmware

1. **Select Option 2: Press 2 and Press Enter.**
   ```
   Enter your choice (1/2/3/4): 2
   ```

2. **Load the release firmware onto the flight controller.**
   ```
   Loading Release firmware...
   ```

3. **Verify firmware and confirm readiness.**
   ```
   Vehicle: <Vehicle_Type>, Firmware version: <Firmware_Version>
   Flight Controller Unit has Completed All the tests and is Ready to use.
   ```

## Option 3: Load Test Firmware

1. **Select Option 3: Press 3 and Press Enter.**
   ```
   Enter your choice (1/2/3/4): 3
   ```

2. **Load the test firmware onto the flight controller.**
   ```
   Loading Test firmware...
   ```

3. **Verify firmware.**
   ```
   Vehicle: <Vehicle_Type>, Firmware version: <Firmware_Version>
   ```

## Option 4: Psense Cable Test

1. **Select Option 4: Press 4 and Press Enter.**
   ```
   Enter your choice (1/2/3/4): 4
   ```

2. **Ensure the test firmware is flashed.**
   If not restart test and chose option 3. Load Test Firmware.
4. **Ensure the battery is charged and connected to the Psense port with the Psense cable.**
5. **Connect to MAVProxy and read the output to evaluate the Psense cable status.**
   ```
   Connecting to MAVProxy...
   Reading MAVProxy output...
   Psense Voltage: PASS
   Psense Current: PASS
   PSENSE Overall: PASS
   Psense Cable Test Completed.
   ```

## Summary of Menu Options

- **Option 1: Test All Interfaces**
  - Comprehensive testing, including firmware loading, Psense tests, PWM tests, radio tests, serial and CAN tests.
  - Generates a detailed test report.

- **Option 2: Load Release Firmware**
  - Loads the release firmware onto the flight controller.
  - Verifies firmware and confirms readiness.

- **Option 3: Load Test Firmware**
  - Loads the test firmware onto the flight controller.
  - Verifies firmware.

- **Option 4: Psense Cable Test**
  - Runs a dedicated test for the Psense cable.
  - Evaluates and confirms the status of the Psense cable.

This documentation provides a clear and detailed guide for setting up and running tests using the `FlightControllerTestSuite`, ensuring that all steps are followed accurately for successful testing and reporting.
```
## Troubleshooting
```
 sudo apt-get remove modemmanager brltty
 ```
