"""
IoT Sensor Data Simulator
Simulates real-time data from substation sensors and sends to API
"""

import requests
import random
import time
from datetime import datetime
import json

# API Base URL
API_URL = "http://localhost:8000"

def generate_transformer_data(transformer_id):
    """Generate realistic transformer data"""
    # Normal operating ranges for 33/11 kV transformer
    return {
        "transformer_id": transformer_id,
        "primary_voltage": round(random.uniform(32.5, 33.5), 2),  # 33 kV ±1.5%
        "secondary_voltage": round(random.uniform(10.8, 11.2), 2),  # 11 kV ±2%
        "primary_current": round(random.uniform(50, 150), 2),
        "secondary_current": round(random.uniform(150, 450), 2),  # Approximately 3x due to voltage ratio
        "oil_temperature": round(random.uniform(55, 75), 1),  # Normal oil temp
        "winding_temperature": round(random.uniform(65, 85), 1),  # Slightly higher than oil
        "load_percentage": round(random.uniform(60, 85), 1),
        "power_factor": round(random.uniform(0.85, 0.95), 2),
        "timestamp": datetime.now().isoformat()
    }

def generate_breaker_data(breaker_id):
    """Generate circuit breaker data"""
    statuses = ["closed"] * 9 + ["open"]  # 90% closed, 10% open
    return {
        "breaker_id": breaker_id,
        "status": random.choice(statuses),
        "voltage": round(random.uniform(32.5, 33.5), 2),
        "current": round(random.uniform(100, 200), 2),
        "operation_count": random.randint(100, 500),
        "timestamp": datetime.now().isoformat()
    }

def generate_busbar_data(busbar_id, voltage_level):
    """Generate busbar data"""
    return {
        "busbar_id": busbar_id,
        "voltage": round(random.uniform(voltage_level - 0.5, voltage_level + 0.5), 2),
        "frequency": round(random.uniform(49.9, 50.1), 2),
        "active_power": round(random.uniform(5, 15), 2),
        "reactive_power": round(random.uniform(2, 5), 2),
        "timestamp": datetime.now().isoformat()
    }

def check_alarms(data, equipment_type, equipment_id):
    """Check if any parameters exceed safe limits"""
    alarms = []
    
    if equipment_type == "transformer":
        if data["oil_temperature"] > 70:
            alarms.append({
                "alarm_id": f"ALM_{int(time.time())}",
                "equipment_id": equipment_id,
                "severity": "warning",
                "message": f"High oil temperature: {data['oil_temperature']}°C",
                "timestamp": datetime.now().isoformat()
            })
        
        if data["winding_temperature"] > 80:
            alarms.append({
                "alarm_id": f"ALM_{int(time.time())}",
                "equipment_id": equipment_id,
                "severity": "critical",
                "message": f"Critical winding temperature: {data['winding_temperature']}°C",
                "timestamp": datetime.now().isoformat()
            })
        
        if data["load_percentage"] > 90:
            alarms.append({
                "alarm_id": f"ALM_{int(time.time())}",
                "equipment_id": equipment_id,
                "severity": "warning",
                "message": f"High load: {data['load_percentage']}%",
                "timestamp": datetime.now().isoformat()
            })
    
    return alarms

def send_data_to_api(endpoint, data):
    """Send data to API endpoint"""
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data)
        if response.status_code in [200, 201]:
            print(f"✓ Sent to {endpoint}: {data.get('transformer_id') or data.get('breaker_id') or data.get('busbar_id')}")
            return True
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Make sure the server is running!")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def simulate_iot_data():
    """Main simulation loop"""
    print("🔌 Starting IoT Sensor Simulator...")
    print(f"📡 Sending data to: {API_URL}")
    print("=" * 60)
    
    # Equipment IDs
    transformers = ["T1", "T2"]
    breakers = ["CB1", "CB2", "CB3", "CB4"]
    busbars = [("BB_33kV", 33), ("BB_11kV", 11)]
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n📊 Cycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 60)
            
            # Send transformer data
            for t_id in transformers:
                data = generate_transformer_data(t_id)
                if send_data_to_api("/api/transformers", data):
                    # Check for alarms
                    alarms = check_alarms(data, "transformer", t_id)
                    for alarm in alarms:
                        send_data_to_api("/api/alarms", alarm)
            
            # Send circuit breaker data
            for cb_id in breakers:
                data = generate_breaker_data(cb_id)
                send_data_to_api("/api/circuit-breakers", data)
            
            # Send busbar data
            for bb_id, voltage in busbars:
                data = generate_busbar_data(bb_id, voltage)
                send_data_to_api("/api/busbars", data)
            
            print("-" * 60)
            print("⏱️  Waiting 5 seconds before next cycle...")
            time.sleep(5)  # Send data every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Simulator stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")

if __name__ == "__main__":
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✓ API is running!")
            simulate_iot_data()
        else:
            print("✗ API is not responding correctly")
    except:
        print("✗ Cannot connect to API. Please start the API server first!")
        print("  Run: python main.py")