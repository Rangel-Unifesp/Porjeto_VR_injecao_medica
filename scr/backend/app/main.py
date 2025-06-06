# scr/backend/app/main.py
from fastapi import FastAPI
import asyncio

# Importar os handlers e outros módulos necessários
from .ws_handler import router as websocket_router
from .mqtt_handler import init_mqtt, mqtt_client # Importa o cliente MQTT e a função de inicialização
# from .sofa_bridge import ... # Se necessário no futuro diretamente em main
=======
# Import handlers and bridge functions
from .mqtt_handler import handle_mqtt_message, send_mqtt_command
from .ws_handler import handle_websocket_message, send_update_to_websocket
# from .sofa_bridge import send_command_to_sofa, get_data_from_sofa # Placeholder for future use

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Iniciando aplicação FastAPI...")
    # Iniciar o loop do cliente MQTT em um thread separado
    # Isso é crucial para que ele não bloqueie o loop de eventos do FastAPI/Uvicorn
    try:
        mqtt_client.loop_start()
        print("Loop do cliente MQTT iniciado.")
    except Exception as e:
        print(f"Erro ao iniciar o loop do cliente MQTT: {e}")
        # Considerar logar este erro ou tratá-lo de forma mais robusta

@app.on_event("shutdown")
async def shutdown_event():
    print("Encerrando aplicação FastAPI...")
    # Parar o loop do cliente MQTT
    try:
        mqtt_client.loop_stop()
        print("Loop do cliente MQTT parado.")
    except Exception as e:
        print(f"Erro ao parar o loop do cliente MQTT: {e}")
    # Outras limpezas, se necessário

@app.get("/")
async def root():
    return {"message": "Backend do Simulador Háptico Modularizado Ativo"}
=======
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