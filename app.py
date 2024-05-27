from flask import Flask, request, jsonify, render_template
import ray
import psutil
import GPUtil
import platform
import cpuinfo

app = Flask(__name__)

# Global variable to store device information
devices = []

def initialize_ray(network):
    if network:
        ray.init(address=network)
    else:
        ray.init(ignore_reinit_error=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_device():
    data = request.get_json()
    network = data.get('network', None)
    
    try:
        initialize_ray(network)
        
        @ray.remote
        def get_device_info():
            cpu_count = psutil.cpu_count()
            memory_info = psutil.virtual_memory()
            gpus = GPUtil.getGPUs()
            gpu_count = len(gpus)
            gpu_info = [{'name': gpu.name, 'total_memory': gpu.memoryTotal, 'available_memory': gpu.memoryFree} for gpu in gpus]
            system_info = {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'cpu_info': cpuinfo.get_cpu_info()
            }
            return {
                'cpu_count': cpu_count,
                'total_memory': memory_info.total,
                'available_memory': memory_info.available,
                'gpu_count': gpu_count,
                'gpu_info': gpu_info,
                'system_info': system_info
            }
        
        device_info = ray.get(get_device_info.remote())
        devices.append({
            'network': network or 'localhost',
            'device_info': device_info
        })
        return jsonify({'message': 'Device registered successfully', 'device_info': device_info}), 200
    
    except Exception as e:
        return jsonify({'message': 'Error registering device', 'error': str(e)}), 500

@app.route('/network')
def network_info():
    all_devices = devices
    try:
        @ray.remote
        def get_all_devices():
            return devices

        all_devices = ray.get(get_all_devices.remote())
    except Exception as e:
        print(f"Error retrieving devices: {e}")

    return render_template('network.html', devices=all_devices)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)