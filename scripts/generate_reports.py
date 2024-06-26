import json
import os
import sys
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def read_json_data(json_file_path):
    with open(json_file_path, 'r') as file:
        return json.load(file)

def generate_summary_log(test_data, summary_log_path, now):
    with open(summary_log_path, 'w') as file:
        file.write(f"Date and Time: {now}\n")
        file.write(f"QR Code: {test_data['qr_code']}\n")
        file.write(f"Firmware Version: {test_data['final_firmware_version']}\n")
        for i, result in enumerate(test_data['test_results'], start=1):
            file.write(f"Step {i}: {result['step_description']} - Status: {result['step_status']}\n")

def generate_pdf_report(test_data, pdf_report_path, template_path, image_path, now):
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template('report_template.html')
    html_content = template.render(test_data=test_data, imageUrl=image_path, now=now)
    HTML(string=html_content, base_url=template_path).write_pdf(pdf_report_path)

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_reports.py <path_to_json_file> <image_path>")
        sys.exit(1)
    json_file_path, image_path = sys.argv[1:3]
    test_data = read_json_data(json_file_path)
    logs_dir = os.path.dirname(json_file_path)
    summary_log_path = os.path.join(logs_dir, "summary_log.txt")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generate_summary_log(test_data, summary_log_path, now)
    qr_code = test_data['qr_code']
    pdf_report_path = os.path.join(logs_dir, f"Test_Report_{qr_code}.pdf")
    generate_pdf_report(test_data, pdf_report_path, os.path.dirname(__file__), image_path, now)
    print("Report generation completed successfully.")

if __name__ == "__main__":
    main()
