"""
33/11 kV Substation Digital Twin API
This API collects and serves real-time substation data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Substation Digital Twin API",
    description="API for 33/11 kV substation monitoring and control",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class TransformerData(BaseModel):
    transformer_id: str
    primary_voltage: float = Field(..., description="Primary side voltage (kV)")
    secondary_voltage: float = Field(..., description="Secondary side voltage (kV)")
    primary_current: float = Field(..., description="Primary current (A)")
    secondary_current: float = Field(..., description="Secondary current (A)")
    oil_temperature: float = Field(..., description="Oil temperature (°C)")
    winding_temperature: float = Field(..., description="Winding temperature (°C)")
    load_percentage: float = Field(..., description="Load percentage (%)")
    power_factor: float = Field(..., description="Power factor")
    timestamp: datetime = Field(default_factory=datetime.now)

class CircuitBreakerData(BaseModel):
    breaker_id: str
    status: str = Field(..., description="open/closed/tripped")
    voltage: float = Field(..., description="Voltage (kV)")
    current: float = Field(..., description="Current (A)")
    operation_count: int = Field(..., description="Number of operations")
    timestamp: datetime = Field(default_factory=datetime.now)

class BusbarData(BaseModel):
    busbar_id: str
    voltage: float = Field(..., description="Busbar voltage (kV)")
    frequency: float = Field(..., description="Frequency (Hz)")
    active_power: float = Field(..., description="Active power (MW)")
    reactive_power: float = Field(..., description="Reactive power (MVAr)")
    timestamp: datetime = Field(default_factory=datetime.now)

class AlarmData(BaseModel):
    alarm_id: str
    equipment_id: str
    severity: str = Field(..., description="critical/warning/info")
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

# In-memory storage (replace with database in production)
substation_data = {
    "transformers": [],
    "circuit_breakers": [],
    "busbars": [],
    "alarms": []
}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "33/11 kV Substation Digital Twin API",
        "status": "running",
        "endpoints": {
            "transformers": "/api/transformers",
            "circuit_breakers": "/api/circuit-breakers",
            "busbars": "/api/busbars",
            "alarms": "/api/alarms",
            "dashboard": "/api/dashboard"
        }
    }

# Transformer Endpoints
@app.post("/api/transformers", status_code=201)
async def add_transformer_data(data: TransformerData):
    """Add new transformer reading from IoT sensor"""
    substation_data["transformers"].append(data.dict())
    # Keep only last 100 readings per transformer
    substation_data["transformers"] = substation_data["transformers"][-100:]
    return {"status": "success", "data": data}

@app.get("/api/transformers")
async def get_all_transformers():
    """Get all transformer data"""
    return {
        "count": len(substation_data["transformers"]),
        "data": substation_data["transformers"]
    }

@app.get("/api/transformers/{transformer_id}")
async def get_transformer(transformer_id: str):
    """Get specific transformer data"""
    transformer_readings = [
        t for t in substation_data["transformers"] 
        if t["transformer_id"] == transformer_id
    ]
    if not transformer_readings:
        raise HTTPException(status_code=404, message="Transformer not found")
    return {
        "transformer_id": transformer_id,
        "latest": transformer_readings[-1],
        "history": transformer_readings
    }

# Circuit Breaker Endpoints
@app.post("/api/circuit-breakers", status_code=201)
async def add_breaker_data(data: CircuitBreakerData):
    """Add circuit breaker status from IoT sensor"""
    substation_data["circuit_breakers"].append(data.dict())
    substation_data["circuit_breakers"] = substation_data["circuit_breakers"][-100:]
    return {"status": "success", "data": data}

@app.get("/api/circuit-breakers")
async def get_all_breakers():
    """Get all circuit breaker data"""
    return {
        "count": len(substation_data["circuit_breakers"]),
        "data": substation_data["circuit_breakers"]
    }

@app.get("/api/circuit-breakers/{breaker_id}")
async def get_breaker(breaker_id: str):
    """Get specific circuit breaker data"""
    breaker_readings = [
        b for b in substation_data["circuit_breakers"] 
        if b["breaker_id"] == breaker_id
    ]
    if not breaker_readings:
        raise HTTPException(status_code=404, message="Circuit breaker not found")
    return {
        "breaker_id": breaker_id,
        "latest": breaker_readings[-1],
        "history": breaker_readings
    }

# Busbar Endpoints
@app.post("/api/busbars", status_code=201)
async def add_busbar_data(data: BusbarData):
    """Add busbar reading from IoT sensor"""
    substation_data["busbars"].append(data.dict())
    substation_data["busbars"] = substation_data["busbars"][-100:]
    return {"status": "success", "data": data}

@app.get("/api/busbars")
async def get_all_busbars():
    """Get all busbar data"""
    return {
        "count": len(substation_data["busbars"]),
        "data": substation_data["busbars"]
    }

# Alarm Endpoints
@app.post("/api/alarms", status_code=201)
async def create_alarm(data: AlarmData):
    """Create new alarm"""
    substation_data["alarms"].append(data.dict())
    return {"status": "success", "data": data}

@app.get("/api/alarms")
async def get_alarms(severity: Optional[str] = None):
    """Get all alarms, optionally filtered by severity"""
    alarms = substation_data["alarms"]
    if severity:
        alarms = [a for a in alarms if a["severity"] == severity]
    return {
        "count": len(alarms),
        "data": alarms
    }

# Dashboard Overview Endpoint
@app.get("/api/dashboard")
async def get_dashboard():
    """Get complete substation overview for dashboard"""
    
    # Get latest readings for each equipment
    latest_transformers = {}
    for t in substation_data["transformers"]:
        latest_transformers[t["transformer_id"]] = t
    
    latest_breakers = {}
    for b in substation_data["circuit_breakers"]:
        latest_breakers[b["breaker_id"]] = b
    
    latest_busbars = {}
    for bb in substation_data["busbars"]:
        latest_busbars[bb["busbar_id"]] = bb
    
    # Get active alarms
    active_alarms = [a for a in substation_data["alarms"]][-10:]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "transformers": list(latest_transformers.values()),
        "circuit_breakers": list(latest_breakers.values()),
        "busbars": list(latest_busbars.values()),
        "alarms": active_alarms,
        "statistics": {
            "total_transformers": len(latest_transformers),
            "total_breakers": len(latest_breakers),
            "total_busbars": len(latest_busbars),
            "active_alarms": len(active_alarms)
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Run the server
if __name__ == "__main__":
    print("🔌 Starting Substation Digital Twin API...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🌐 Dashboard Endpoint: http://localhost:8000/api/dashboard")
    uvicorn.run(app, host="0.0.0.0", port=8000)