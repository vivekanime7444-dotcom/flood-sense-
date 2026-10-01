from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
from flask import render_template
import urllib.request
import json

OWM_API_KEY = "203af3d17f3375c49d3e5bcb8be1c19a"  # <--- PASTE YOUR API KEY HERE

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration for our mock stations
STATIONS = {
    "nashik": {
        "station_id": "GRB-062",
        "station_name": "Godavari at Nashik",
        "river_name": "Godavari",
        "location": "Nashik, Maharashtra",
        "basin": "Godavari Basin",
        "normal_water_level": 2.8,
        "danger_water_level": 4.5,
        "max_water_level": 7.2,
        "normal_rainfall": 40,
        "danger_rainfall": 100,
        "coords": [19.9975, 73.7898]
    },
    "kakinada": {
        "station_id": "KND-001",
        "station_name": "Godavari at Kakinada",
        "river_name": "Godavari",
        "location": "Kakinada, Andhra Pradesh",
        "basin": "Godavari Basin",
        "normal_water_level": 2.8,
        "danger_water_level": 4.5,
        "max_water_level": 7.2,
        "normal_rainfall": 40,
        "danger_rainfall": 100,
        "coords": [16.9891, 82.2475]
    }
}
current_station_key = "kakinada"

# Global variable to store current readings
current_reading = {
    "water_level": 2.8,
    "rainfall": 35,
    "timestamp": datetime.now().isoformat(),
    "risk_level": "NORMAL"
}

def calculate_risk(water_level, rainfall):
    """Calculate flood risk level based on thresholds"""
    if water_level > 4.5 and rainfall > 100:
        return "HIGH"
    elif water_level > 3.8 or rainfall > 70:
        return "MEDIUM"
    elif water_level > 3.2 or rainfall > 50:
        return "LOW"
    else:
        return "NORMAL"

def get_real_weather(lat, lon):
    if OWM_API_KEY == "YOUR_API_KEY_HERE":
        return None
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
        req = urllib.request.Request(url, headers={'User-Agent': 'FloodSense/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
            rain = 0.0
            if 'rain' in data and '1h' in data['rain']:
                rain = data['rain']['1h'] * 24
                
            temp = data.get('main', {}).get('temp', 25.0)
            wind = data.get('wind', {}).get('speed', 5.0)
            
            return {
                "rainfall": rain,
                "temperature": temp,
                "wind_speed": wind
            }
    except Exception as e:
        print(f"Error fetching real weather: {e}")
    return None

def get_mock_data():
    """Get current mock data with gradual changes"""
    global current_reading, current_station_key
    station_data = STATIONS[current_station_key]
    
    # Try to get REAL weather data
    real_weather = None
    if "coords" in station_data:
        lat, lon = station_data["coords"]
        real_weather = get_real_weather(lat, lon)
        
    if real_weather is not None:
        current_reading["rainfall"] = real_weather["rainfall"]
        current_reading["temperature"] = real_weather["temperature"]
        current_reading["wind_speed"] = real_weather["wind_speed"]
        
        # Link water level to real rainfall: 
        # If it's raining heavily, increase water level, else decrease to normal
        if real_weather["rainfall"] > 50:
            current_reading["water_level"] += random.uniform(0.01, 0.03)
        elif current_reading["water_level"] > station_data.get("normal_water_level", 2.8):
            current_reading["water_level"] -= random.uniform(0.01, 0.02)
        else:
            # Introduce minor natural jitter so the chart is always active
            current_reading["water_level"] += random.uniform(-0.01, 0.01)
            
            # Keep it near the normal level, not dropping too low
            normal = station_data.get("normal_water_level", 2.8)
            if current_reading["water_level"] < normal - 0.1:
                current_reading["water_level"] += 0.02
    else:
        # Fallback to pure mock logic if no API key or error
        current_reading["rainfall"] += random.uniform(-0.5, 1.0)
        current_reading["water_level"] += random.uniform(-0.02, 0.03)
        current_reading.setdefault("temperature", 25.0)
        current_reading.setdefault("wind_speed", 5.0)
        current_reading["temperature"] += random.uniform(-0.1, 0.1)
        current_reading["wind_speed"] += random.uniform(-0.1, 0.1)
    
    # Ensure values stay within realistic ranges
    current_reading["water_level"] = max(1.0, min(7.0, round(current_reading["water_level"], 2)))
    current_reading["rainfall"] = max(0, min(200, round(current_reading["rainfall"], 1)))
    current_reading["temperature"] = round(current_reading["temperature"], 1)
    current_reading["wind_speed"] = round(current_reading["wind_speed"], 1)
    
    # Update timestamp and risk level
    current_reading["timestamp"] = datetime.now().isoformat()
    current_reading["risk_level"] = calculate_risk(
        current_reading["water_level"], 
        current_reading["rainfall"]
    )
    
    return {**station_data, **current_reading}

def simulate_emergency():
    """Force dangerous levels for demo purposes"""
    global current_reading
    current_reading.update({
        "water_level": 5.8,
        "rainfall": 150,
        "timestamp": datetime.now().isoformat(),
        "risk_level": "HIGH"
    })
    return get_mock_data()

def reset_to_normal():
    """Reset to normal levels"""
    global current_reading
    current_reading.update({
        "water_level": 2.8,
        "rainfall": 35,
        "timestamp": datetime.now().isoformat(),
        "risk_level": "NORMAL"
    })
    return get_mock_data()

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    station = STATIONS[current_station_key]
    return jsonify({
        "status": "OK", 
        "message": "FloodSense API is running",
        "station_monitored": station["station_id"],
        "station_name": station["station_name"],
        "data_source": "Mock CWC/IMD Data (Stable Demo Version)"
    })

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/set-station', methods=['POST'])
def set_station():
    global current_station_key
    data = request.json
    
    query = data.get('query')
    coords = data.get('coords')
    
    if query and coords:
        key = query.lower().replace(" ", "_")
        if key not in STATIONS:
            STATIONS[key] = {
                "station_id": f"DYN-{random.randint(100, 999)}",
                "station_name": query,
                "river_name": "Local River",
                "location": query,
                "basin": "Unknown Basin",
                "normal_water_level": 2.8,
                "danger_water_level": 4.5,
                "max_water_level": 7.2,
                "normal_rainfall": 40,
                "danger_rainfall": 100,
                "coords": coords
            }
        current_station_key = key
        return jsonify({"status": "success", "message": f"Station set to {query}"})

    station_key = data.get('station_key')
    if station_key and station_key in STATIONS:
        current_station_key = station_key
        return jsonify({"status": "success", "message": f"Station set to {STATIONS[station_key]['station_name']}"})
    return jsonify({"status": "error", "message": "Invalid station key"}), 400


@app.route('/api/station-data', methods=['GET'])
def get_station_data():
    """
    Main endpoint: Returns realistic mock CWC data
    """
    try:
        data = get_mock_data()
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk-assessment', methods=['GET'])
def get_risk_assessment():
    """
    Returns only the risk assessment
    """
    try:
        data = get_mock_data()
        return jsonify({
            "station_id": data["station_id"],
            "station_name": data["station_name"],
            "risk_level": data["risk_level"],
            "water_level": data["water_level"],
            "rainfall": data["rainfall"],
            "timestamp": data["timestamp"],
            "alert_threshold_water": 4.5,
            "alert_threshold_rain": 100
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/send-alert', methods=['POST'])
def send_alert():
    """
    Send alert based on current risk level
    """
    try:
        # Get current data
        current_data = get_mock_data()
        
        # Get request data
        request_data = request.get_json() or {}
        phone_number = request_data.get('phone', '+91XXXXXXXXXX')
        custom_message = request_data.get('message', '')
        
        # Create alert message
        if not custom_message:
            alert_message = (
                f"🌊 FloodSense Alert: {current_data['station_name']}\n"
                f"⚠️ Risk Level: {current_data['risk_level']}\n"
                f"💧 Water Level: {current_data['water_level']}m (Danger: 4.5m)\n"
                f"🌧️ Rainfall: {current_data['rainfall']}mm/24h (Danger: 100mm)\n"
                f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            alert_message = custom_message

        # Simulate SMS sending - This will print to console
        print("🔴" * 50)
        print("📱 SMS ALERT SENT:")
        print(f"   To: {phone_number}")
        print(f"   Message: {alert_message}")
        print("🔴" * 50)

        return jsonify({
            "status": "success",
            "message": "Alert sent successfully",
            "risk_level": current_data["risk_level"],
            "recipient": phone_number,
            "alert_message": alert_message,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate-emergency', methods=['POST'])
def trigger_emergency():
    """
    Force a HIGH risk scenario for demo purposes
    """
    try:
        emergency_data = simulate_emergency()
        
        # Auto-send alert for emergency
        alert_message = (
            f"🚨 CRITICAL FLOOD ALERT: {emergency_data['station_name']}\n"
            f"💧 Water Level: {emergency_data['water_level']}m (DANGER!)\n"
            f"🌧️ Rainfall: {emergency_data['rainfall']}mm/24h (DANGER!)\n"
            f"⚠️ Immediate action required!"
        )
        
        print("🚨" * 50)
        print("🔥 EMERGENCY SIMULATION ACTIVATED")
        print(f"   {alert_message}")
        print("🚨" * 50)

        return jsonify({
            "status": "emergency_activated",
            "risk_level": "HIGH",
            "message": "Emergency scenario simulated",
            "data": emergency_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset-data', methods=['POST'])
def reset_data():
    """
    Reset to normal conditions
    """
    try:
        normal_data = reset_to_normal()
        
        return jsonify({
            "status": "data_reset",
            "message": "Data reset to normal conditions",
            "risk_level": "NORMAL",
            "data": normal_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/station-info', methods=['GET'])
def get_station_info():
    """Returns information about the monitored station"""
    return jsonify({
        "station": MOCK_STATION,
        "alert_thresholds": {
            "water_level": {
                "normal": "< 3.2m",
                "low_risk": "3.2m - 3.8m", 
                "medium_risk": "3.8m - 4.5m",
                "high_risk": "> 4.5m"
            },
            "rainfall": {
                "normal": "< 50mm",
                "low_risk": "50mm - 70mm",
                "medium_risk": "70mm - 100mm", 
                "high_risk": "> 100mm"
            }
        }
    })

if __name__ == '__main__':
    print("🚀 Starting FloodSense Mock API Server")
    print("✅ Using stable mock data - No API dependencies")
    station = STATIONS[current_station_key]
    print(f"📡 Monitoring: {station['station_name']}")
    print("\n📋 API Endpoints:")
    print("   GET  /api/health            - Health check")
    print("   GET  /api/station-data      - Get mock CWC data")
    print("   GET  /api/risk-assessment   - Get risk assessment") 
    print("   GET  /api/station-info      - Get station info")
    print("   POST /api/send-alert        - Send SMS alert")
    print("   POST /api/simulate-emergency - Force high risk scenario")
    print("   POST /api/reset-data        - Reset to normal")
    print("\n🌐 Server running on http://localhost:5000")
    print("📧 Alerts will be printed to this console")
    
    app.run(debug=True, host='0.0.0.0', port=5000)