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
   ├── Production_Test
   | └──Specific_Test_Folders
   ├── firmware/ # Firmware files and scripts
   │ ├── ArducopterTest4.6.0-dev_images/arducopter.apj
   │ ├── ArducopterFinal4.5.2_images/arducopter.apj
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
   | ├── I2C2.lua
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
   git clone git@vault.mistralsolutions.com:qrb5165_flight_kit/ifb_prd_test_scripts.git
   cd ifb_prd_test_scripts/FlightControllerTestSuite
   chmod -R +x .
   ```

2. **Run the Setup Script**:
   This script will install Docker, add the user to the Docker group, and build the Docker image.
   ```
   sudo ./setup.sh
   ```
   Also, install the following pip packages:
   ```
   pip3 install PyYAML mavproxy jinja2 weasyprint pyserial colorama pymavlink
   echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
   ```

3. **Test Environment Setup**:
   **Hardware Connections**
   Connect your Cube Orange and Flight Computer to the host machine via USB cables. Ensure all necessary peripherals are connected (e.g., FCU Testjig, SPPM Module, Safety Switch).

## Test Procedure

### Initial Setup

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
4. **Power On the System.**
5. **Connect the IFB with Type-C and the add-on test jig with microUSB to the Host-PC.**
6. **Open Terminal and start the test by running the following command inside the `FlightControllerTestSuite` directory:**

   ```bash
   cd ~/Desktop/FlightControllerTestSuite
   python3 scripts/main_test_script.py
   ```

### Menu Options

You will be presented with the following menu:
```
Select an option:
1. Test All Interfaces
2. Reboot Flight Controller
3. Load Release Firmware
4. Load Test Firmware
5. Psense Cable Test
Enter your choice (1/2/3/4/5):
```

### Option 1: Test All Interfaces

This option performs comprehensive flashing, testing, and report generation for the Flight Add-On Board with Cube Orange Plus.

**Firmware Check and Flashing:**
  - Verifies if the Test Firmware is already flashed on the Cube.
  - If not, it loads the Test Firmware before proceeding with interface testing.

**Interface Testing:**
- AUX and MAIN Out Test: User observes LEDs on the test jig and inputs 'y' for PASS (glowing) or 'n' for FAIL (not glowing).
- PPM and SBUSo Test: User presses the safety switch and Enter. A PASS status indicates a successful connection.
- Automatic Tests: The script then automatically performs Serial, CAN, PSENSE, ADC, and I2C tests.

**Error Handling:**
- If any test fails, it indicates the failed test, generates a report, and closes the script.
Release Firmware Loading:
- If all tests pass, the script loads the Release Firmware.
- Performs a final Serial 2 test to ensure connectivity with the Eagle Board.

**Report Generation:**
- Generates test results, saved in the `~/Desktop/FlightControllerTestSuite/Production_Test` folder.

**Select Option 1: Press 1 and Press Enter.**
Now, 
This option will First ask you to scan the QR Code. So, scan the QR Code placed on Add On Board, make sure cursor is at the terminal.
   ```
   Enter your choice (1/2/3/4/5): 1
   Please Ensure SD Card with Lua Scripts Loaded in FCU.
   Scan QR code on the board: 0123456789
   QR code scanned: 0123456789
   Searching for Firmware...
   ```
   It will first search for any Loaded Firmware on the cube if, test firmware is not found to be flashed then, Test Firmware will be loaded First.

**Loading TEST Firmware:**
   
   ```
   Vehicle: Copter, Firmware version: official-4.5.2
   Loading Test firmware...
   Loaded firmware for 427,0, size: 1835112 bytes, waiting for the bootloader...
   If the board does not respond within 1-2 seconds, unplug and re-plug the USB connector.
   
   Erase  : [====================] 100.0% (timeout: 7 seconds) 
   Program: [====================] 100.0%
   Verify : [====================] 100.0%
   Rebooting.
   
   Test Firmware loaded.
   Searching for Firmware...
   Vehicle: Copter, Firmware version: dev-4.6.0
   ```
   Once, Test Firmware is Loaded, it’ll will proceed for Further Testing.
   
2. **AUX and MAIN Out Tests, Observe LEDs on Testjig...**
   ```
   Press if AUX OUT 1-6 LEDs are glowing (y/n): y
   Press if MAIN OUT 1-4 LEDs are glowing (y/n): y
   Press if MAIN OUT 5-8 LEDs are glowing (y/n): y
   AUX OUT 1-6: PASS
   MAIN OUT 1-4: PASS
   MAIN OUT 5-8: PASS
   ```
   Above test will be confirmed by Visually Observing LEDs on TESTJig, 
Press ‘y’ if they are glowing and ‘n’ if not glowing, and then Press ‘enter’.
Results will be displayed as status and stored: PASS for success and FAIL for failure.



3. **Testing PPM and SBUSo...**

Initially, Safety Switch will we glowing as Solid Red.
Press safety switch until it starts flashing Red and press Enter.


   ```
   Hold the safety switch until it Blinks Red, then press Enter.
   PPM and SBUSo: PASS
   ```

4. **Starting Serial Tests through Flight Computer...**
   ```
   Serial 1: PASS
   Serial 2: PASS
   Serial 3: PASS
   Serial 4: PASS
   Serial 5: PASS
   ```

5. **Starting CAN Tests through Flight Computer...**
   ```
   CAN 1: PASS
   CAN 2: PASS
   ```

6. **Testing PSENSE**
   ```
   Psense Voltage: PASS
   Psense Current: PASS
   PSENSE Overall: PASS
   ```

7. **Testing ADC**
   ```
   ADC: PASS
   ```

8. **Testing I2C**
   ```
   I2C1: PASS
   I2C2: PASS
   ```
   **If any, Fail condition(s) occurs then;** it will tell which test is failed, Generate Report and close the test.
In that case, please Debug the Issue, Reboot and Rerun the Test.
In case, if Test Script Crashes or Does Not Respond or any Error Occurs Please Close the Test by Pressing (ctrl+c) and rerun the test.
   
9. **Loading Release firmware...**
   ```
   Loaded firmware for 427,0, size: 1817396 bytes, waiting for the bootloader...
   If the board does not respond within 1-2 seconds, unplug and re-plug the USB connector.
   
   Erase  : [====================] 100.0% (timeout: 5 seconds) 
   Program: [====================] 100.0%
   Verify : [====================] 100.0%
   Rebooting.
   
   Release Firmware loaded.
   Searching for Firmware...
   Vehicle: Copter, Firmware version: official-4.5.2
   Flight Controller Unit has Completed All the tests and is Ready to use.
   Generated JSON file with test results at: /home/maheshhg/Desktop/Production_Test/0123456789_2024-07-12_15-19-11/test_results.json
   Report generation completed successfully.
   Report generation script executed successfully.
   ```
   Once Release Firmware is loaded it will proceed for Serial 2 Test to ensure connectivity with Eagle Board.
Then, It Will Generate the Test Results, which can be found in
 ~/Desktop/FlightControllerTestSuite/Production_Test Folder.

**Generated Reports:**

**Production_Test Folder:** All generated report folders will be inside Production_Test Folder, in Desktop.

**Specific Test Folder:** Each run of `Option 1: run_all_tests` creates a folder named `{QR_Code}_{Timestamp}` inside the `Production_Test` folder on the desktop. The timestamp ensures uniqueness. 

**Example:** If you run the `Option 1: run_all_tests` function with a QR code `test123` at `2023-10-05_12-00-00`, the Specific Test Folder. Would be: ‘test123_2023-10-05_12-00-00`

And Specific Test Folder will consist of following files.

**summary_log.txt, mavproxy_adc_logs.txt, mavproxy_i2c_logs.txt, mavproxy_psense_logs.txt** (these log files contain connection data that was received during tests)

**test_results.json:** consist status of each results, required for creating test result pdf.

**Test_Report_test123.pdf:** This PDF file will consist of final test results along with, Scanned QR code, date, timestamp, loaded firmware version, Test Information and Status.

### Option 2: Psense Cable Test
- Runs a dedicated test for the Psense cable.

1. **Select Option 5: Press 5 and Press Enter.**
   ```
   Enter your choice (1/2/3/4/5): 5
   Please Ensure Test Firmware and SD Card with Lua Scripts Loaded in FCU
   ```
   
2. **Testing PSENSE**
   ```
   Psense Voltage: PASS
   Psense Current: PASS
   PSENSE Overall: PASS
   ```

### Option 3: Load Release Firmware
- Loads the release firmware onto the flight controller.
- Verifies firmware and confirms readiness.
1. **Select Option 3: Press 3 and Press Enter.**
   ```
   Enter your choice (1/2/3/4/5): 3
   Loading Release firmware...
   Loaded firmware for 427,0, size: 1817396 bytes, waiting for the bootloader...
   If the board does not respond within 1-2 seconds, unplug and re-plug the USB connector.
   
   Erase  : [====================] 100.0% (timeout: 7 seconds) 
   Program: [====================] 100.0%
   Verify : [====================] 100.0%
   Rebooting.
   
   Release Firmware loaded.
   Searching for Firmware...
   Vehicle: Copter, Firmware version: official-4.5.2
   Flight Controller Unit is Ready to use.
   ```

### Option 4: Load Test Firmware
- Loads and verifies the test firmware onto the flight controller.
1. **Select Option 4: Press 4 and Press Enter.**
   ```
   Enter your choice (1/2/3/4/5): 4
   Loading Test firmware...
   Loaded firmware for 427,0, size: 1835112 bytes, waiting for the bootloader...
   If the board does not respond within 1-2 seconds, unplug and re-plug the USB connector.
   
   Erase  : [====================] 100.0% (timeout: 7 seconds) 
   Program: [====================] 100.0%
   Verify : [====================] 100.0%
   Rebooting.
   
   Test Firmware loaded.
   Searching for Firmware...
   Vehicle: Copter, Firmware version: dev-4.6.0
   ```

### Option 5: Reboot Flight Controller
- Sends Reboot Command to the Flight Controller.

1. **Select Option 2: Press 2 and Press Enter.**
   ```
   Enter your choice (1/2/3/4/5): 2
   Heartbeat received from the flight controller.
   Reboot command sent to the flight controller.
   ```
## Summary of Menu Options

- **Option 1: Test All Interfaces**
  - Comprehensive testing, including firmware loading, Psense tests, PWM tests, radio tests, serial and CAN tests.
  - Generates a detailed test report.

- **Option 2: Psense Cable Test**
  - Runs a dedicated test for the Psense cable.
  - Evaluates and confirms the status of the Psense cable.

- **Option 3: Load Release Firmware**
  - Loads the release firmware onto the flight controller.
  - Verifies firmware and confirms readiness.

- **Option 4: Load Test Firmware**
  - Loads the test firmware onto the flight controller.
  - Verifies firmware.

- **Option 5: Reboot Flight Controller**
  - Sends a reboot command to the flight controller.
  
This documentation provides a clear and detailed guide for setting up and running tests using the `FlightControllerTestSuite`, ensuring that all steps are followed accurately for successful testing and reporting.

## Generated Reports:
**Production Test Folder:** This is created on the desktop inside FlightControllerTestSuite folder and is named Production_Test.

**Specific Test Folder:** Each run of run_all_tests creates a folder named {qr_code}_{timestamp} inside the Production_Test folder on the desktop. The timestamp ensures uniqueness.

**

Log Directory:** The LOG_DIR is by default set to ~/Desktop/Production_Test/Specific_Test_Folder, but can be customized by setting the LOG_DIR environment variable.

**Example:**
If you run the run_all_tests function with a QR code test123 at 2023-10-05_12-00-00, the specific log file paths would be:

**General MAVProxy logs:** ~/Desktop/Production_Test/test123_2023-10-05_12-00-00/mavproxy_logs.txt

**PSENSE Test logs:** ~/Desktop/Production_Test/test123_2023-10-05_12-00-00/mavproxy_psense_logs.txt

**ADC Test logs:** ~/Desktop/Production_Test/test123_2023-10-05_12-00-00/mavproxy_adc_logs.txt

**I2C Test logs:** ~/Desktop/Production_Test/test123_2023-10-05_12-00-00/mavproxy_i2c_logs.txt
You can modify these paths if needed by changing the relevant lines in the script. For instance, to change the LOG_DIR to /var/log/flight_tests, you can set it in the environment variables or modify the script directly:
```
LOG_DIR = os.getenv('LOG_DIR', '/var/log/flight_tests')
```

## Troubleshooting

```
sudo apt-get remove modemmanager brltty
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

## Troubleshooting and Known Issues

### USB Device Detection Issues

During the installation and setup of the CubePilot CubeOrange+ device, we encountered some issues related to USB device detection. Below are the steps taken to identify and resolve the issues:

1. **Identifying the USB Device**:
    - Run
      ```
      lsusb
      ```
       to list all connected USB devices. Look for the CubePilot CubeOrange+ device in the output. The relevant entry should look like this:
       Bus 001 Device 009: ID 2dae:1058 CubePilot CubeOrange+-BL
       - Note, here the idVendor (2dae) and idProduct (1058) values.

2. **Verifying Device Connection**:
    - Use dmesg to verify the device connection. The relevant entries should show the USB device being recognized:
```
    [  193.930246] usb 1-1: New USB device found, idVendor=2dae, idProduct=1058, bcdDevice= 2.00
    [  193.930271] usb 1-1: Product: CubeOrange+
    [  193.930277] usb 1-1: Manufacturer: CubePilot
    [  193.930282] usb 1-1: SerialNumber: 2D0036000851323138363132
```
3. **Creating a udev Rule**:
    - To ensure the device is always recognized with the correct permissions, create a udev rule:
        1. Create a new file for the udev rule using a text editor:
           
           ```
           sudo nano /etc/udev/rules.d/99-cubepilot.rules
           ```
        2. Add the following line to the file:
           ```
           SUBSYSTEM=="usb", ATTR{idVendor}=="2dae", ATTR{idProduct}=="1058", MODE="0666"
            ```
           This rule sets the permissions (MODE="0666") to allow read and write access to the device for all users.
            
        4. Save the file and exit the text editor.

        5. Apply the new udev rule by reloading udev rules:
           ```
           sudo udevadm control --reload-rules
           ```
        6. Disconnect and reconnect the CubePilot CubeOrange+ device to apply the new udev rule.

4. **Common Errors and Resolutions**:
    - **Command Not Found**: If you encounter an error such as sudo: demsg: command not found, ensure you are typing the correct command sudo dmesg.
    - **Device Not Recognized**: If the device is not recognized, try reconnecting the USB cable or using a different USB port. Ensure the device is powered on and functioning properly.

5. **Further Debugging**:
    - If issues persist, use dmesg | tail -20 to view the latest system messages and identify potential problems.

By following these steps, we were able to successfully identify and resolve the USB device detection issues with the CubePilot CubeOrange+ during installation.
