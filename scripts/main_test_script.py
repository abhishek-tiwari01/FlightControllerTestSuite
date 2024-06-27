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

# Initialize colorama
init(autoreset=True)
'''
# Load configuration from environment variables or use defaults
FIRMWARE_TEST_PATH = os.getenv('FIRMWARE_TEST_PATH', '/home/maheshhg/Desktop/FlightControllerTestSuite/firmware/ArducopterTest4.6.0-dev_images/bin/arducopter.apj')
FIRMWARE_FINAL_PATH = os.getenv('FIRMWARE_FINAL_PATH', '/home/maheshhg/Desktop/FlightControllerTestSuite/firmware/ArducopterFinal4.5.2_images/bin/arducopter.apj')
GENERATE_REPORT_SCRIPT = os.getenv('GENERATE_REPORT_SCRIPT', '/home/maheshhg/Desktop/FlightControllerTestSuite/generate_reports.py')
LOG_DIR = os.getenv('LOG_DIR', '/tmp')

'''
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
LOG_DIR = os.getenv('LOG_DIR', '/tmp')
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
        master.wait_heartbeat(timeout=30)

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
            return f"\n{Fore.GREEN}Vehicle: {vehicle_type}, Firmware version: {firmware_version}{Style.RESET_ALL}\n"
        else:
            return f"{Fore.RED}Firmware not flashed or not responding.{Style.RESET_ALL}"
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

def read_output(process, component_status, log_file_path, finished_event, psense_only=False, max_lines=50, timeout=10):
    try:
        with open(log_file_path, 'w') as log_file:
            start_time = time.time()
            line_count = 0
            psense_found = False
            test_messages_found = set()

            while time.time() - start_time < timeout and line_count < max_lines:
                line = process.stdout.readline()
                if not line:
                    break

                log_file.write(line)
                log_file.flush()
                if psense_only and ("Psense Voltage" in line or "Psense Current" in line):
                    psense_found = True
                    parse_mavproxy_output(line.strip(), component_status, psense_only)
                    test_messages_found.add("Psense Voltage")
                    test_messages_found.add("Psense Current")
                elif not psense_only:
                    parse_mavproxy_output(line.strip(), component_status, psense_only)
                    for comp in ["I2C1", "I2C2", "Psense Voltage", "Psense Current", "ADC"]:
                        if comp in line:
                            test_messages_found.add(comp)
                line_count += 1

            if psense_only and not psense_found:
                component_status["Psense Voltage"] = "FAIL"
                component_status["Psense Current"] = "FAIL"
                evaluate_psense_overall(component_status)

            if not psense_only and not test_messages_found:
                print(f"{Fore.RED}Test Messages Not Received, Please Check SD Card and Lua Scripts{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error reading output: {e}{Style.RESET_ALL}")
    finally:
        finished_event.set()

def parse_mavproxy_output(line, component_status, psense_only):
    components = {
        "I2C1": "AP: I2C1:",
        "I2C2": "AP: I2C2:",
        "Psense Voltage": "AP: Psense Voltage:",
        "Psense Current": "AP: Psense Current:",
        "ADC": "AP: Rangefinder Distance:"
    }

    for comp, signal in components.items():
        if psense_only and comp not in ["Psense Voltage", "Psense Current"]:
            continue
        
        if signal in line:
            if comp in ["I2C1", "I2C2"]:
                status = "FAIL" if "ERROR" in line else "PASS"
            else:
                value = float(line.split()[-2])
                status = "PASS" if value > 11.0 else "FAIL"
            update_status(comp, status, component_status)

def update_status(component, status, component_status):
    if component_status.get(component) != status or component not in component_status:
        print_status(component, status == "PASS")
        component_status[component] = status
        if "PSENSE" in component or "Voltage" in component or "Current" in component:
            evaluate_psense_overall(component_status)

def evaluate_psense_overall(component_status):
    components = ["Psense Voltage", "Psense Current"]
    if all(c in component_status for c in components):
        overall = "PASS" if all(component_status[c] == "PASS" for c in components) else "FAIL"
        if component_status.get("PSENSE Overall") != overall:
            print_status("PSENSE Overall", overall == "PASS")
            component_status["PSENSE Overall"] = overall

def print_status(component, condition):
    color = Fore.GREEN if condition else Fore.RED
    status = "PASS" if condition else "FAIL"
    print(f"{color}{component}: {status}{Style.RESET_ALL}")

def adb_connection():
    adb_root = subprocess.run(['adb', 'root'], capture_output=True, text=True)
    if adb_root.returncode != 0 or 'cannot run as root' in adb_root.stderr.lower():
        print(f"{Fore.RED}Failed to obtain root access.{Style.RESET_ALL}")
        return None

    adb_shell = subprocess.Popen(['adb', 'shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    adb_shell.stdin.write("su\n")
    adb_shell.stdin.flush()
    time.sleep(1)
    return adb_shell

def configure_gpio(adb_shell, gpio, value):
    try:
        adb_shell.stdin.write(f"echo {gpio} > /sys/class/gpio/export\n")
        adb_shell.stdin.flush()
    except Exception as e:
        print(f"{Fore.RED}GPIO {gpio} may already be exported: {e}{Style.RESET_ALL}")
    
    direction_cmd = f"echo out > /sys/class/gpio/gpio{gpio}/direction; echo {value} > /sys/class/gpio/gpio{gpio}/value\n"
    adb_shell.stdin.write(direction_cmd)
    adb_shell.stdin.flush()

def test_serial_2():
    try:
        adb_root = subprocess.run(['adb', 'root'], capture_output=True, text=True)
        if adb_root.returncode != 0 or 'cannot run as root' in adb_root.stderr.lower():
            print(f"{Fore.RED}Failed to obtain root access.{Style.RESET_ALL}")
            return "FAIL"

        adb_shell = subprocess.Popen(['adb', 'shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        adb_shell.stdin.write("su\n")
        adb_shell.stdin.flush()
        time.sleep(1)

        mav_command = "mavproxy.py --master=/dev/ttyHS1 --baudrate=921600 --aircraft MyCopter\n"
        adb_shell.stdin.write(mav_command)
        adb_shell.stdin.flush()

        while True:
            output = adb_shell.stdout.readline()
            if "Detected vehicle" in output:
                print(f"{Fore.GREEN}Serial 2: PASS{Style.RESET_ALL}")
                adb_shell.terminate()
                return "PASS"
            elif "link 1 down" in output or not output:
                print(f"{Fore.RED}Serial 2: FAIL{Style.RESET_ALL}")
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
            print_status(f"Serial {serial_number}", True)
            return "PASS"
        elif "link 1 down" in output or not output:
            print_status(f"Serial {serial_number}", False)
            return "FAIL"

    print_status(f"Serial {serial_number}", False)
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
    for gpio in [370, 371]:
        try:
            adb_shell.stdin.write(f"echo {gpio} > /sys/class/gpio/export\n")
            adb_shell.stdin.flush()
        except Exception as e:
            print(f"{Fore.RED}GPIO {gpio} may already be exported: {e}{Style.RESET_ALL}")
    adb_shell.stdin.write(f"echo out > /sys/class/gpio/gpio370/direction; echo {gpio_a} > /sys/class/gpio/gpio370/value\n")
    adb_shell.stdin.write(f"echo out > /sys/class/gpio/gpio371/direction; echo {gpio_b} > /sys/class/gpio/gpio371/value\n")
    adb_shell.stdin.flush()

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
                print_status(f"CAN {can_number}", True)
                return "PASS"

    print_status(f"CAN {can_number}", False)
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

def test_psense_cable(component_status):
    cube_orange_port = find_cube_orange_port()
    if cube_orange_port is None:
        print(f"{Fore.RED}CubeOrangePlus not found.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.YELLOW}Connecting to MAVProxy...{Style.RESET_ALL}")
    mavproxy_process = connect_mavproxy(cube_orange_port)
    
    finished_event = threading.Event()
    log_file_path = os.path.join(LOG_DIR, "mavproxy_psense_logs.txt")
    
    print(f"{Fore.YELLOW}Reading MAVProxy output...{Style.RESET_ALL}")
    thread = threading.Thread(target=read_output, args=(mavproxy_process, component_status, log_file_path, finished_event, True), daemon=True)
    thread.start()
    finished_event.wait()
    mavproxy_process.terminate()
    
    evaluate_psense_overall(component_status)
    
    print(f"{Fore.GREEN if component_status['PSENSE Overall'] == 'PASS' else Fore.RED}Psense Cable Test Completed.{Style.RESET_ALL}")
    for component, status in component_status.items():
        if component in ["Psense Voltage", "Psense Current", "PSENSE Overall"]:
            print(f"{Fore.GREEN if status == 'PASS' else Fore.RED}{component}: {status}{Style.RESET_ALL}")

def test_pwm_outputs(master):
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
        response = input(f"{Fore.YELLOW}Press if {description} LEDs are glowing (y/n): {Style.RESET_ALL}").strip().lower()
        while response not in ['y', 'n']:
            response = input("Invalid input. Please enter 'y' or 'n': ").strip().lower()
        for i in range(servo_start, servo_end + 1):
            set_servo_function(i, 0)  # Disable the servos
        return response == 'y'

    main_out_1_4 = test_servo_output(1, 4, "MAIN OUT 1-4")
    main_out_5_8 = test_servo_output(5, 8, "MAIN OUT 5-8")
    aux_out_1_6 = test_servo_output(9, 14, "AUX OUT 1-6")

    return {
        "MAIN OUT 1-4": "PASS" if main_out_1_4 else "FAIL",
        "MAIN OUT 5-8": "PASS" if main_out_5_8 else "FAIL",
        "AUX OUT 1-6": "PASS" if aux_out_1_6 else "FAIL"
    }

def test_radio_status(component_status):
    mavproxy_process = connect_mavproxy(find_cube_orange_port())

    print(f"{Fore.YELLOW}\nReading MAVProxy output for radio status...{Style.RESET_ALL}\n")
    input(f"{Fore.CYAN}Hold the safety switch until it Blinks Red, then press Enter. {Style.RESET_ALL}")

    try:
        radio_status = "FAIL"
        start_time = time.time()
        while time.time() - start_time < 30:
            line = mavproxy_process.stdout.readline().strip()
            if "Radio Connected" in line:
                radio_status = "PASS"
                break
            elif "Radio Disconnected" in line:
                radio_status = "FAIL"
                break
        print(f"\n{Fore.YELLOW}Radio Test Completed.{Style.RESET_ALL}")
        print_status("PPM and SBUSo", radio_status == "PASS")
        component_status["PPM and SBUSo"] = radio_status
    finally:
        mavproxy_process.terminate()

def main_menu():
    print(f"{Fore.CYAN}Select an option:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. Test All Interfaces{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}2. Load Release Firmware{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}3. Load Test Firmware{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}4. Psense Cable Test{Style.RESET_ALL}")
    choice = ''
    while choice not in ['1', '2', '3', '4']:
        choice = input(f"{Fore.CYAN}Enter your choice (1/2/3/4): {Style.RESET_ALL}").strip()
    return choice

def main():
    choice = main_menu()
    component_status = {}
    qr_code = ""
    final_firmware_version = ""

    if choice == '1':
        qr_code = input(f"{Fore.CYAN}Scan QR code on the board: {Style.RESET_ALL}")
        print(f"{Fore.GREEN}QR code scanned: {qr_code}{Style.RESET_ALL}")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{qr_code}_{timestamp}"
        production_test_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Production_Test")
        specific_folder_path = os.path.join(production_test_folder, folder_name)
        os.makedirs(specific_folder_path, exist_ok=True)
        log_file_path = os.path.join(specific_folder_path, "mavproxy_logs.txt")
        
        load_firmware(FIRMWARE_TEST_PATH, "Test")
        print(get_firmware_version())

        cube_orange_port = find_cube_orange_port()
        if cube_orange_port is None:
            print(f"{Fore.RED}CubeOrangePlus not found.{Style.RESET_ALL}")
            return

        mavproxy_process = connect_mavproxy(cube_orange_port)
        finished_event = threading.Event()
        thread = threading.Thread(target=read_output, args=(mavproxy_process, component_status, log_file_path, finished_event, False), daemon=True)
        thread.start()
        finished_event.wait()
        mavproxy_process.terminate()

        master = mavutil.mavlink_connection(cube_orange_port, baud=115200)
        master.wait_heartbeat()
        
        input(f"{Fore.YELLOW}\nPress Enter twice to Proceed for MAIN & AUX Out tests:{Style.RESET_ALL}")
        pwm_results = test_pwm_outputs(master)
        component_status.update(pwm_results)

        test_radio_status(component_status)

        print(f"\n{Fore.YELLOW}Starting Serial Tests through Flight Computer...{Style.RESET_ALL}\n")
        integrate_serial_test(component_status, 1, [0, 0])
        integrate_serial_2_test(component_status)
        integrate_serial_test(component_status, 3, [0, 1])
        integrate_serial_test(component_status, 4, [1, 0])
        integrate_serial_test(component_status, 5, [1, 1])

        integrate_can_test(component_status, 1, 1, 1)
        integrate_can_test(component_status, 2, 0, 0)

        load_firmware(FIRMWARE_FINAL_PATH, "Release")
        final_firmware_version = get_firmware_version()
        print(final_firmware_version)
        integrate_serial_2_test(component_status)
        print(f"{Fore.GREEN}Flight Controller Unit has Completed All the tests and is Ready to use.{Style.RESET_ALL}")

    elif choice == '2':
        load_firmware(FIRMWARE_FINAL_PATH, "Release")
        final_firmware_version = get_firmware_version()
        integrate_serial_2_test(component_status)
        print(final_firmware_version)
        print(f"{Fore.GREEN}Flight Controller Unit is Ready to use.{Style.RESET_ALL}")

    elif choice == '3':
        load_firmware(FIRMWARE_TEST_PATH, "Test")
        print(get_firmware_version())

    elif choice == '4':
        test_psense_cable(component_status)

    if choice in ['1']:
        generate_test_result_json(component_status, qr_code, specific_folder_path, final_firmware_version)

        try:
            json_file_path = os.path.join(specific_folder_path, "test_results.json")
            subprocess.run(["python3", REPORT_SCRIPT_PATH, json_file_path, CUBE_IMAGE_PATH], check=True)
            print(f"{Fore.GREEN}Report generation script executed successfully.{Style.RESET_ALL}")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}An error occurred while executing the report generation script: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
