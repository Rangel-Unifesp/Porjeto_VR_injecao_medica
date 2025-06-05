from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import paho.mqtt.client as mqtt

# Import handlers and bridge functions
from .mqtt_handler import handle_mqtt_message, send_mqtt_command
from .ws_handler import handle_websocket_message, send_update_to_websocket
# from .sofa_bridge import send_command_to_sofa, get_data_from_sofa # Placeholder for future use

app = FastAPI()

# MQTT Broker config
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "simulador/esp32"

# Global set para WebSockets conectados
connected_websockets = set()

# Funções MQTT ---------------------------------------------------

def on_connect(client, userdata, flags, rc):
    print(f"Conectado ao MQTT Broker com código {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    # print(f"Mensagem MQTT recebida: {message}") # Original print
    handle_mqtt_message(msg.topic, message) # Call the new handler
    # Enviar mensagem para todos websockets conectados
    asyncio.run(send_message_to_clients(message))

async def send_message_to_clients(message: str):
    to_remove = set()
    for websocket in connected_websockets:
        try:
            await websocket.send_text(message)
        except Exception:
            to_remove.add(websocket)
    for ws in to_remove:
        connected_websockets.remove(ws)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()

# API REST -----------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Backend do simulador haptico ativo"}

# WebSocket -----------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # print(f"Mensagem recebida do frontend: {data}") # Original print
            handle_websocket_message(data, websocket) # Call the new handler
            # Aqui você pode encaminhar comandos para o SOFA ou ESP32
            # Example: send_update_to_websocket(websocket, {"response_from_server": "got it: " + data})
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
        print("Cliente desconectado")

# Rodar o backend:
# uvicorn main:app --host 0.0.0.0 --port 8000
