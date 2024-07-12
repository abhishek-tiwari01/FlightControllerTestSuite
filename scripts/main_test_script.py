import subprocess
import threading
import serial.tools.list_ports
import os
import datetime
import time
import json
import re
import select
from colorama import init, Fore, Style
from pymavlink import mavutil
from pynput.keyboard import Controller

# Initialize colorama
init(autoreset=True)

# Define paths
USER_HOME = os.path.expanduser('~')
DESKTOP_PATH = os.path.join(USER_HOME, 'Desktop')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMWARE_DIR = os.path.join(BASE_DIR, 'firmware')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
REPORT_SCRIPT_PATH = os.path.join(SCRIPTS_DIR, 'generate_reports.py')
CUBE_IMAGE_PATH = os.path.join(IMAGES_DIR, 'cube.jpg')
PRODUCTION_TEST_FOLDER = os.path.join(DESKTOP_PATH, "Production_Test")
os.makedirs(PRODUCTION_TEST_FOLDER, exist_ok=True)

FIRMWARE_TEST_PATH = os.path.join(FIRMWARE_DIR, "ArducopterTest4.6.0-dev_images/bin/arducopter.apj")
FIRMWARE_FINAL_PATH = os.path.join(FIRMWARE_DIR, "ArducopterFinal4.5.2_images/bin/arducopter.apj")
UPLOADER_SCRIPT_PATH = os.path.join(FIRMWARE_DIR, "uploader.py")

def find_cube_orange_port():
    ports = serial.tools.list_ports.comports()
    for port in sorted(ports):
        if "ttyUSB" in port.device or "ttyACM" in port.device:
            return port.device
    return None

def reboot_flight_controller():
    port = find_cube_orange_port()
    if port is None:
        print(f"{Fore.RED}Cube Orange Plus not found. Please check the connection.{Style.RESET_ALL}")
        return False
    
    try:
        mavlink_connection = mavutil.mavlink_connection(port, baud=115200)
        mavlink_connection.wait_heartbeat()
        print("Heartbeat received from the flight controller.")
        
        mavlink_connection.mav.command_long_send(
            mavlink_connection.target_system, 
            mavlink_connection.target_component,
            mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
            0,  # Confirmation
            1,  # Param1 (1 for reboot, 0 for shutdown)
            0, 0, 0, 0, 0, 0
        )
        print("Reboot command sent to the flight controller.")
        mavlink_connection.close()
        time.sleep(15)  # Wait for reboot to complete
        return True
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        return False

# Existing functions

def load_firmware(firmware_path, firmware_type):
    try:
        print(f"{Fore.YELLOW}Loading {firmware_type} firmware...{Style.RESET_ALL}")
        subprocess.run([UPLOADER_SCRIPT_PATH, "--force", firmware_path], check=True, cwd=FIRMWARE_DIR)
        time.sleep(12)
        print(f"{Fore.GREEN}{firmware_type} Firmware loaded.{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error loading firmware: {e}{Style.RESET_ALL}")

def get_firmware_version():
    port = find_cube_orange_port()
    if not port:
        return f"{Fore.RED}Cube Orange Plus not found. Please check the connection.{Style.RESET_ALL}"

    try:
        master = mavutil.mavlink_connection(port, baud=115200)
        print(f"{Fore.CYAN}Searching for Firmware...{Style.RESET_ALL}")
        master.wait_heartbeat(timeout= 5)

        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
            0,
            mavutil.mavlink.MAVLINK_MSG_ID_AUTOPILOT_VERSION,
            0, 0, 0, 0, 0, 0
        )

        message = master.recv_match(type='AUTOPILOT_VERSION', blocking=True, timeout=10)
        if message:
            firmware_version = decode_flight_sw_version(message.flight_sw_version)
            vehicle_type = get_vehicle_type(master)
            return f"Vehicle: {vehicle_type}, Firmware version: {firmware_version}"
        else:
            return f"{Fore.CYAN}Firmware not found Flashed, \nFlashing...{Style.RESET_ALL}"
    except Exception as e:
        return f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}"

def decode_flight_sw_version(flight_sw_version):
    major = (flight_sw_version >> 24) & 0xFF
    minor = (flight_sw_version >> 16) & 0xFF
    patch = (flight_sw_version >> 8) & 0xFF
    fw_type_id = flight_sw_version & 0xFF

    fw_type_dict = {
        0: 'dev',
        64: 'alpha',
        128: 'beta',
        192: 'rc',
        255: 'official',
    }
    fw_type = fw_type_dict.get(fw_type_id, "undefined")

    return f"{fw_type}-{major}.{minor}.{patch}"

def get_vehicle_type(master):
    master.wait_heartbeat()
    vehicle_type = master.messages['HEARTBEAT'].type
    vehicle_dict = {
        mavutil.mavlink.MAV_TYPE_FIXED_WING: "Plane",
        mavutil.mavlink.MAV_TYPE_QUADROTOR: "Copter",
        mavutil.mavlink.MAV_TYPE_GROUND_ROVER: "Rover",
        mavutil.mavlink.MAV_TYPE_SUBMARINE: "Sub",
        mavutil.mavlink.MAV_TYPE_SURFACE_BOAT: "Boat",
    }
    return vehicle_dict.get(vehicle_type, "Unknown")

def connect_mavproxy(port):
    mavproxy_command = f"mavproxy.py --master={port} --baudrate=921600 --aircraft MyCopter"
    mavproxy_process = subprocess.Popen(mavproxy_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
    return mavproxy_process

def read_output(process, component_status, log_file_path, finished_event, parse_function, timeout=10):
    try:
        with open(log_file_path, 'w') as log_file:
            start_time = time.time()
            while time.time() - start_time < timeout:
                line = process.stdout.readline()
                if not line:
                    break

                log_file.write(line)
                log_file.flush()
                parse_function(line.strip(), component_status)
    except Exception as e:
        print(f"{Fore.RED}Error reading output: {e}{Style.RESET_ALL}")
    finally:
        finished_event.set()

def parse_i2c_output(line, component_status):
    if "AP: I2C1:" in line:
        status = "FAIL" if "ERROR" in line else "PASS"
        update_status("I2C1", status, component_status)
    elif "AP: I2C2:" in line:
        status = "FAIL" if "ERROR" in line else "PASS"
        update_status("I2C2", status, component_status)

def parse_psense_output(line, component_status):
    if "AP: Psense Voltage:" in line:
        value = float(line.split()[-2])
        status = "PASS" if value > 5.0 else "FAIL"
        update_status("Psense Voltage", status, component_status)
    elif "AP: Psense Current:" in line:
        value = float(line.split()[-2])
        status = "PASS" if value > 2.0 else "FAIL"
        update_status("Psense Current", status, component_status)
    evaluate_psense_overall(component_status)

def parse_adc_output(line, component_status):
    if "AP: Rangefinder Distance:" in line:
        value = float(line.split()[-2])
        status = "PASS" if value > 11.5 else "FAIL"
        update_status("ADC", status, component_status)

def update_status(component, status, component_status):
    if component_status.get(component) != status or component not in component_status:
        component_status[component] = status
        if "PSENSE" in component or "Voltage" in component or "Current" in component:
            evaluate_psense_overall(component_status)

def evaluate_psense_overall(component_status):
    components = ["Psense Voltage", "Psense Current"]
    if all(c in component_status for c in components):
        overall = "PASS" if all(component_status[c] == "PASS" for c in components) else "FAIL"
        if component_status.get("PSENSE Overall") != overall:
            component_status["PSENSE Overall"] = overall

def print_status(status_dict):
    for component, condition in status_dict.items():
        color = Fore.GREEN if condition == "PASS" else Fore.RED
        status = "PASS" if condition == "PASS" else "FAIL"
        print(f"{color}{component}: {status}{Style.RESET_ALL}")

def adb_connection():
    retries = 3
    for _ in range(retries):
        subprocess.run(['adb', 'start-server'], capture_output=True, text=True)
        adb_root = subprocess.run(['adb', 'root'], capture_output=True, text=True)
        if adb_root.returncode == 0 and 'cannot run as root' not in adb_root.stderr.lower() and 'no devices/emulators found' not in adb_root.stderr.lower():
            adb_shell = subprocess.Popen(['adb', 'shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            adb_shell.stdin.write("su\n")
            adb_shell.stdin.flush()
            time.sleep(1)
            return adb_shell
        time.sleep(5)
    print(f"{Fore.RED}Couldn't Establish adb connection, please check.{Style.RESET_ALL}")
    return None

def configure_gpio(adb_shell, gpio, value):
    try:
        if adb_shell.poll() is not None:
            raise BrokenPipeError("adb shell process is not running.")
        
        # Check if the GPIO is already exported
        check_export_cmd = f"[ -d /sys/class/gpio/gpio{gpio} ] || echo {gpio} > /sys/class/gpio/export\n"
        adb_shell.stdin.write(check_export_cmd)
        adb_shell.stdin.flush()
        
        direction_cmd = f"echo out > /sys/class/gpio/gpio{gpio}/direction; echo {value} > /sys/class/gpio/gpio{gpio}/value\n"
        adb_shell.stdin.write(direction_cmd)
        adb_shell.stdin.flush()
    except Exception as e:
        print(f"{Fore.RED}An error occurred while configuring GPIO {gpio}: {e}{Style.RESET_ALL}")

def test_serial_2():
    try:
        adb_shell = adb_connection()
        if not adb_shell:
            return "FAIL"

        mav_command = "mavproxy.py --master=/dev/ttyHS1 --baudrate=921600 --aircraft MyCopter\n"
        adb_shell.stdin.write(mav_command)
        adb_shell.stdin.flush()

        while True:
            output = adb_shell.stdout.readline()
            if "Detected vehicle" in output:
                adb_shell.terminate()
                return "PASS"
            elif "link 1 down" in output or not output:
                adb_shell.terminate()
                return "FAIL"

    except subprocess.SubprocessError as e:
        print(f"{Fore.RED}An error occurred during the Serial 2 test: {e}{Style.RESET_ALL}")
        return "FAIL"

def integrate_serial_2_test(component_status):
    status = test_serial_2()
    component_status["Serial 2"] = status

def test_serial_line(adb_shell, gpio1, gpio2, serial_number):
    configure_gpio(adb_shell, 442, gpio1)
    configure_gpio(adb_shell, 464, gpio2)
    
    mav_command = "mavproxy.py --master=/dev/ttyHS2 --baudrate=921600 --aircraft MyCopter\n"
    adb_shell.stdin.write(mav_command)
    adb_shell.stdin.flush()

    start_time = time.time()
    while time.time() - start_time < 10:
        output = adb_shell.stdout.readline()
        if "Detected vehicle" in output:
            return "PASS"
        elif "link 1 down" in output or not output:
            return "FAIL"

    return "FAIL"

def integrate_serial_test(component_status, line_number, line_config):
    adb_shell = adb_connection()
    if adb_shell:
        status = test_serial_line(adb_shell, line_config[0], line_config[1], line_number)
        component_status[f"Serial {line_number}"] = status
        adb_shell.terminate()
    else:
        component_status[f"Serial {line_number}"] = "FAIL"

def setup_can_interface(adb_shell):
    setup_cmds = "ifconfig can0 down; ip link set can0 type can bitrate 1000000; ifconfig can0 up; ifconfig can0 txqueuelen 1000;\n"
    adb_shell.stdin.write(setup_cmds)
    adb_shell.stdin.flush()

def configure_can_gpio(adb_shell, gpio_a, gpio_b):
    try:
        if adb_shell.poll() is not None:
            raise BrokenPipeError("adb shell process is not running.")
        
        for gpio in [370, 371]:
            check_export_cmd = f"[ -d /sys/class/gpio/gpio{gpio} ] || echo {gpio} > /sys/class/gpio/export\n"
            adb_shell.stdin.write(check_export_cmd)
            adb_shell.stdin.flush()
            
            adb_shell.stdin.write(f"echo out > /sys/class/gpio/gpio{gpio}/direction; echo {gpio_a} > /sys/class/gpio/gpio{gpio}/value\n")
            adb_shell.stdin.write(f"echo out > /sys/class/gpio/gpio{gpio}/direction; echo {gpio_b} > /sys/class/gpio/gpio{gpio}/value\n")
            adb_shell.stdin.flush()
    except Exception as e:
        print(f"{Fore.RED}An error occurred while configuring CAN GPIO {gpio}: {e}{Style.RESET_ALL}")

def test_can_line(adb_shell, can_number, gpio_a, gpio_b):
    configure_can_gpio(adb_shell, gpio_a, gpio_b)
    adb_shell.stdin.write("candump can0\n")
    adb_shell.stdin.flush()

    start_time = time.time()
    timeout = 5
    pattern = re.compile(r"can0\s+[0-9A-F]{3}[0-9A-F]{5}\s+\[\d\]\s+([0-9A-F]{2}\s+){1,8}")

    valid_packets = []

    while time.time() - start_time < timeout:
        ready = select.select([adb_shell.stdout], [], [], 0.1)
        if ready[0]:
            line = adb_shell.stdout.readline()
            if pattern.match(line.strip()):
                valid_packets.append(line.strip())
                return "PASS"

    return "FAIL"

def integrate_can_test(component_status, can_number, gpio_a, gpio_b):
    adb_shell = adb_connection()
    if adb_shell:
        setup_can_interface(adb_shell)
        status = test_can_line(adb_shell, can_number, gpio_a, gpio_b)
        component_status[f"CAN {can_number}"] = status
        adb_shell.terminate()
    else:
        component_status[f"CAN {can_number}"] = "FAIL"

def generate_test_result_json(component_status, qr_code, logs_dir, final_firmware_version):
    test_results = {"qr_code": qr_code, "final_firmware_version": final_firmware_version, "test_results": []}
    for component, status in component_status.items():
        test_results["test_results"].append({"step_description": component, "step_status": status})
    
    json_path = os.path.join(logs_dir, "test_results.json")
    with open(json_path, "w") as json_file:
        json.dump(test_results, json_file, indent=4)
    print(f"{Fore.GREEN}Generated JSON file with test results at: {json_path}{Style.RESET_ALL}")
    return json_path

def generate_reports(json_path):
    try:
        subprocess.run(["python3", REPORT_SCRIPT_PATH, json_path, CUBE_IMAGE_PATH], check=True)
        print(f"{Fore.GREEN}Report generation script executed successfully.{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}An error occurred while executing the report generation script: {e}{Style.RESET_ALL}")

def test_psense_cable(component_status, log_file_path):
    cube_orange_port = find_cube_orange_port()
    if cube_orange_port is None:
        print(f"{Fore.RED}CubeOrangePlus not found.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.YELLOW}5. Testing PSENSE{Style.RESET_ALL}\n")
    mavproxy_process = connect_mavproxy(cube_orange_port)
    
    finished_event = threading.Event()
    
    thread = threading.Thread(target=read_output, args=(mavproxy_process, component_status, log_file_path, finished_event, parse_psense_output), daemon=True)
    thread.start()
    finished_event.wait()
    mavproxy_process.terminate()
    keyboard = Controller()
    keyboard.press('\n')
    keyboard.release('\n')
    print_status({"Psense Voltage": component_status["Psense Voltage"], "Psense Current": component_status["Psense Current"], "PSENSE Overall": component_status["PSENSE Overall"]})

def test_adc(component_status, log_file_path):
    cube_orange_port = find_cube_orange_port()
    if cube_orange_port is None:
        print(f"{Fore.RED}CubeOrangePlus not found.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.YELLOW}6. Testing ADC{Style.RESET_ALL}\n")
    mavproxy_process = connect_mavproxy(cube_orange_port)
    
    finished_event = threading.Event()
    
    thread = threading.Thread(target=read_output, args=(mavproxy_process, component_status, log_file_path, finished_event, parse_adc_output), daemon=True)
    thread.start()
    finished_event.wait()
    mavproxy_process.terminate()
    keyboard = Controller()
    keyboard.press('\n')
    keyboard.release('\n')
    print_status({"ADC": component_status["ADC"]})

def test_i2c(component_status, log_file_path):
    cube_orange_port = find_cube_orange_port()
    if cube_orange_port is None:
        print(f"{Fore.RED}CubeOrangePlus not found.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.YELLOW}7. Testing I2C{Style.RESET_ALL}\n")
    mavproxy_process = connect_mavproxy(cube_orange_port)
    
    finished_event = threading.Event()
    
    thread = threading.Thread(target=read_output, args=(mavproxy_process, component_status, log_file_path, finished_event, parse_i2c_output), daemon=True)
    thread.start()
    finished_event.wait()
    mavproxy_process.terminate()
    keyboard = Controller()
    keyboard.press('\n')
    keyboard.release('\n')
    print_status({"I2C1": component_status["I2C1"], "I2C2": component_status["I2C2"]})

def test_pwm_outputs(master):
    print(f"\n{Fore.YELLOW}1. Running PWM AUX and MAIN Out Tests, Observe LEDs on Testjig...{Style.RESET_ALL}\n")
    def set_servo_function(servo, function):
        master.mav.param_set_send(
            master.target_system,
            master.target_component,
            f'SERVO{servo}_FUNCTION'.encode('utf-8'),
            function,
            mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        time.sleep(1)

    def test_servo_output(servo_start, servo_end, description):
        for i in range(servo_start, servo_end + 1):
            set_servo_function(i, 136)  # Set to high max
        while True:
            response = input(f"{Fore.YELLOW}Press if {description} LEDs are glowing (y/n): {Style.RESET_ALL}").strip().lower()
            if response in ['y', 'n']:
                break
            print("Invalid input. Please enter 'y' or 'n':")
        for i in range(servo_start, servo_end + 1):
            set_servo_function(i, 0)  # Disable the servos
        return response == 'y'
    
    aux_out_1_6 = test_servo_output(9, 14, "AUX OUT 1-6")
    main_out_1_4 = test_servo_output(1, 4, "MAIN OUT 1-4")
    main_out_5_8 = test_servo_output(5, 8, "MAIN OUT 5-8")
   

    return {

        "AUX OUT 1-6": "PASS" if aux_out_1_6 else "FAIL",
        "MAIN OUT 1-4": "PASS" if main_out_1_4 else "FAIL",
        "MAIN OUT 5-8": "PASS" if main_out_5_8 else "FAIL"

    }

def test_radio_status(component_status):
    mavproxy_process = connect_mavproxy(find_cube_orange_port())

    print(f"{Fore.YELLOW}\n2. Testing PPM and SBUSo...{Style.RESET_ALL}\n")
    input(f"{Fore.CYAN}Hold the safety switch until it Blinks Red, then press Enter. {Style.RESET_ALL}")

    try:
        radio_status = "FAIL"
        start_time = time.time()
        while time.time() - start_time < 15:
            line = mavproxy_process.stdout.readline().strip()
            if "Radio Connected" in line:
                radio_status = "PASS"
                break
            elif "Radio Disconnected" in line:
                radio_status = "FAIL"
                break
        component_status["PPM and SBUSo"] = radio_status
    finally:
        mavproxy_process.terminate()
        keyboard = Controller()
        keyboard.press('\n')
        keyboard.release('\n')
    print_status({"PPM and SBUSo": component_status["PPM and SBUSo"]})

def main_menu():
    print(f"{Fore.CYAN}Select an option:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. Test All Interfaces{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}2. Reboot Flight Controller{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}3. Load Release Firmware{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}4. Load Test Firmware{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}5. Psense Cable Test{Style.RESET_ALL}")
    choice = ''
    while choice not in ['1', '2', '3', '4', '5']:
        choice = input(f"{Fore.CYAN}Enter your choice (1/2/3/4/5): {Style.RESET_ALL}").strip()
    return choice

def run_all_tests(qr_code):
    component_status = {}
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"{qr_code}_{timestamp}"
    production_test_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Production_Test")
    specific_folder_path = os.path.join(production_test_folder, folder_name)
    os.makedirs(specific_folder_path, exist_ok=True)
    log_file_path = os.path.join(specific_folder_path, "mavproxy_logs.txt")

    firmware_version = get_firmware_version()
    print(firmware_version)

    if "dev-4.6.0" not in firmware_version:
        load_firmware(FIRMWARE_TEST_PATH, "Test")
    
    print(get_firmware_version())

    cube_orange_port = find_cube_orange_port()
    if cube_orange_port is None:
        print(f"{Fore.RED}CubeOrangePlus not found.{Style.RESET_ALL}")
        return component_status, specific_folder_path, False

    master = mavutil.mavlink_connection(cube_orange_port, baud=115200)
    master.wait_heartbeat()
    pwm_results = test_pwm_outputs(master)
    component_status.update(pwm_results)
    print_status(pwm_results)

    test_radio_status(component_status)
    
    print(f"\n{Fore.YELLOW}3. Starting Serial Tests through Flight Computer...{Style.RESET_ALL}\n")
    integrate_serial_test(component_status, 1, [0, 0])
    integrate_serial_2_test(component_status)
    integrate_serial_test(component_status, 3, [0, 1])
    integrate_serial_test(component_status, 4, [1, 0])
    integrate_serial_test(component_status, 5, [1, 1])
    print_status({f"Serial {i}": component_status[f"Serial {i}"] for i in range(1, 6)})

    print(f"\n{Fore.YELLOW}4. Starting CAN Tests through Flight Computer...{Style.RESET_ALL}\n")
    integrate_can_test(component_status, 1, 1, 1)
    integrate_can_test(component_status, 2, 0, 0)
    print_status({f"CAN {i}": component_status[f"CAN {i}"] for i in range(1, 3)})

    test_psense_cable(component_status, os.path.join(specific_folder_path, "mavproxy_psense_logs.txt"))

    test_adc(component_status, os.path.join(specific_folder_path, "mavproxy_adc_logs.txt"))

    test_i2c(component_status, os.path.join(specific_folder_path, "mavproxy_i2c_logs.txt"))

    return component_status, specific_folder_path, True

def main():
    choice = main_menu()

    if choice == '1':
        print(f"{Fore.YELLOW}Please Ensure SD Card with Lua Scripts Loaded in FCU.{Style.RESET_ALL}")
        qr_code = input(f"{Fore.CYAN}Scan QR code on the board: {Style.RESET_ALL}")
        print(f"{Fore.GREEN}QR code scanned: {qr_code}{Style.RESET_ALL}")
        component_status, specific_folder_path, success = run_all_tests(qr_code)

        failed_tests = [component for component, status in component_status.items() if status != "PASS"]

        if failed_tests:
            print(f"{Fore.RED}One or more tests failed: {failed_tests}. Generating report and ending tests...{Style.RESET_ALL}")
            json_path = generate_test_result_json(component_status, qr_code, specific_folder_path, "Test Dev-4.6.0")
            generate_reports(json_path)
        else:
            load_firmware(FIRMWARE_FINAL_PATH, "Release")
            final_firmware_version = get_firmware_version()
            print(final_firmware_version)
            integrate_serial_2_test(component_status)
            print_status({"Serial 2": component_status["Serial 2"]})

            print(f"{Fore.GREEN}Flight Controller Unit has Completed All the tests and is Ready to use.{Style.RESET_ALL}")
            generate_test_result_json(component_status, qr_code, specific_folder_path, final_firmware_version)

            try:
                json_file_path = os.path.join(specific_folder_path, "test_results.json")
                subprocess.run(["python3", REPORT_SCRIPT_PATH, json_file_path, CUBE_IMAGE_PATH], check=True)
                print(f"{Fore.GREEN}Report generation script executed successfully.{Style.RESET_ALL}")
            except subprocess.CalledProcessError as e:
                print(f"{Fore.RED}An error occurred while executing the report generation script: {e}{Style.RESET_ALL}")
    
    elif choice == '2':
        reboot_flight_controller()

    elif choice == '3':
        load_firmware(FIRMWARE_FINAL_PATH, "Release")
        component_status = {"Serial 2": "PASS"}  # Initialize the component_status dictionary
        final_firmware_version = get_firmware_version()
        print(final_firmware_version)
        integrate_serial_2_test(component_status)
        print_status({"Serial 2": component_status["Serial 2"]})

        print(f"{Fore.GREEN}Flight Controller Unit is Ready to use.{Style.RESET_ALL}")

    elif choice == '4':
        load_firmware(FIRMWARE_TEST_PATH, "Test")
        print(get_firmware_version())

    elif choice == '5':
        print(f"{Fore.YELLOW}Please Ensure Test Firmware and SD Card with Lua Scripts Loaded in FCU{Style.RESET_ALL}")
        component_status = {}
        test_psense_cable(component_status, os.path.join(PRODUCTION_TEST_FOLDER, "mavproxy_psense_logs.txt"))

if __name__ == "__main__":
    main()
