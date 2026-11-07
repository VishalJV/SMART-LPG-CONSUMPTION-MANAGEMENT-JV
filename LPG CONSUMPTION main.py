from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json

app = FastAPI()

class ConnectedClients:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(data))

manager = ConnectedClients()

# ESP32 data format
class SensorData(BaseModel):
    device_id: str
    sensor_value: float
    status: str

# ESP32 sends HTTP POST here
@app.post("/api/update")
async def update_data(data: SensorData):
    payload = data.model_dump()
    # Live updates broadcast to all open dashboard screens
    await manager.broadcast(payload)
    return {"status": "success", "received": payload}

# Frontend connects here for real-time live streaming
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)