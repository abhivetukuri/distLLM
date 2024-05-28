from flask import Flask, request, render_template, redirect, url_for, jsonify
import subprocess
import os
import psutil
import platform
import cpuinfo

app = Flask(__name__)
devices = []

# Function to run shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

# Function to gather device information
def get_device_info():
    device_info = {
        'cpu_count': psutil.cpu_count(),
        'total_memory': psutil.virtual_memory().total,
        'available_memory': psutil.virtual_memory().available,
        'gpu_count': 0,  # Assuming no GPU for now
        'gpu_info': [],  # Assuming no GPU info for now
        'system_info': {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_info': cpuinfo.get_cpu_info(),
        }
    }
    return device_info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    network_ip = data.get('network')

    if not network_ip:
        # Start as head node
        os.environ['RAY_ENABLE_WINDOWS_OR_OSX_CLUSTER'] = '1'
        command = "ray start --head --port=6375"
        stdout, stderr = run_command(command)
        network_ip = "192.168.1.225:6375"  # Assuming this IP address, adjust as necessary
    else:
        # Join an existing cluster
        os.environ['RAY_ENABLE_WINDOWS_OR_OSX_CLUSTER'] = '1'
        command = f"ray start --address='{network_ip}'"
        stdout, stderr = run_command(command)

    device_info = get_device_info()
    devices.append({'network': network_ip, 'device_info': device_info})

    return jsonify({
        'message': 'Device registered successfully',
        'network_ip': network_ip,
        'stdout': stdout,
        'stderr': stderr
    })

@app.route('/network')
def network():
    return render_template('network.html', devices=devices)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)