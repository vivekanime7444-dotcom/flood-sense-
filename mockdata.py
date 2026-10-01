from datetime import datetime, timedelta
import random

# Configuration for our mock station
MOCK_STATION = {
    "station_id": "KND-001",
    "station_name": "Godavari at Kakinada",
    "river_name": "Godavari",
    "location": "Kakinada, Andhra Pradesh",
    "basin": "Godavari Basin",
    "normal_water_level": 2.8,
    "danger_water_level": 4.5,
    "max_water_level": 7.2,
    "normal_rainfall": 40,
    "danger_rainfall": 100
}

def generate_mock_reading():
    """Generate realistic mock sensor readings that change gradually"""
    
    # Base values with some random fluctuation
    base_water_level = 2.8 + random.uniform(-0.3, 0.5)
    base_rainfall = 35 + random.uniform(-10, 15)
    
    # Ensure values stay within realistic ranges
    water_level = max(1.0, min(7.0, round(base_water_level, 2)))
    rainfall = max(0, min(200, round(base_rainfall, 1)))
    
    # Simulate rising levels during "monsoon season" (60% chance)
    if random.random() < 0.6:
        water_level += random.uniform(0.1, 0.4)
        rainfall += random.uniform(5, 20)
    
    # Generate realistic timestamp (within last 15 minutes)
    timestamp = (datetime.now() - timedelta(minutes=random.randint(0, 15))).isoformat()
    
    return {
        "water_level": water_level,
        "rainfall": rainfall,
        "timestamp": timestamp
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

# Initial mock reading
current_reading = generate_mock_reading()
current_reading["risk_level"] = calculate_risk(
    current_reading["water_level"], 
    current_reading["rainfall"]
)

def get_mock_data():
    """Get current mock data with gradual changes"""
    global current_reading
    
    # Update readings with small changes (simulate real sensors)
    current_reading["water_level"] += random.uniform(-0.1, 0.2)
    current_reading["rainfall"] += random.uniform(-2, 5)
    
    # Ensure values stay within realistic ranges
    current_reading["water_level"] = max(1.0, min(7.0, round(current_reading["water_level"], 2)))
    current_reading["rainfall"] = max(0, min(200, round(current_reading["rainfall"], 1)))
    
    # Update timestamp and risk level
    current_reading["timestamp"] = datetime.now().isoformat()
    current_reading["risk_level"] = calculate_risk(
        current_reading["water_level"], 
        current_reading["rainfall"]
    )
    
    return {**MOCK_STATION, **current_reading}

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