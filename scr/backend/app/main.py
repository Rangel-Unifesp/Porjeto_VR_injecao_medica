from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import paho.mqtt.client as mqtt
from contextlib import asynccontextmanager


# --- Configurações ---
# Configs do MQTT Broker
MQTT_BROKER = "localhost" # Ou o IP do seu broker
MQTT_PORT = 1883
# Tópico para receber dados do ESP32 (sensores, status, etc.)
MQTT_TOPIC_SENSORS = "simulador/esp32/dados"
# Tópico para enviar comandos para o ESP32 (ligar motor, etc.)
MQTT_TOPIC_COMMANDS = "simulador/esp32/comandos"

# Fila para comunicação segura entre a thread do MQTT e o loop do asyncio
mqtt_queue = asyncio.Queue()

# Conjunto global para WebSockets conectados
connected_websockets = set()

# --- Funções do Cliente MQTT ---

def on_connect(client, userdata, flags, rc):
    """Callback executado quando o cliente se conecta ao broker."""
    if rc == 0:
        print("Conectado ao MQTT Broker com sucesso!")
        # Subscreve ao tópico de sensores do ESP32
        client.subscribe(MQTT_TOPIC_SENSORS)
    else:
        print(f"Falha ao conectar, código de retorno: {rc}\n")

def on_message(client, userdata, msg):
    """Callback executado quando uma mensagem é recebida do broker."""
    message = msg.payload.decode()
    print(f"Mensagem recebida do tópico '{msg.topic}': {message}")
    # Coloca a mensagem na fila para ser processada pelo asyncio
    try:
        mqtt_queue.put_nowait(message)
    except asyncio.QueueFull:
        print("A fila de mensagens está cheia. Descartando mensagem.")


# --- Tarefas de Background ---

async def broadcast_mqtt_messages():
    """Consome mensagens da fila e as envia para todos os clientes WebSocket."""
    while True:
        message = await mqtt_queue.get()
        # Cria uma cópia do set para iterar, evitando problemas de concorrência
        # se um cliente se desconectar durante o envio.
        for websocket in list(connected_websockets):
            try:
                await websocket.send_text(message)
            except Exception:
                # O cliente pode ter se desconectado, remove da lista ativa
                connected_websockets.remove(websocket)
        mqtt_queue.task_done()

# --- Gerenciamento do Ciclo de Vida do App (Lifespan) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o início e o fim de tarefas de background."""
    print("Iniciando o servidor...")
    # Configura e conecta o cliente MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start() # Inicia a thread de rede do MQTT
    
    # Guarda o cliente no estado do app para uso posterior
    app.state.mqtt_client = client
    
    # Inicia a tarefa que transmite mensagens da fila para os websockets
    asyncio.create_task(broadcast_mqtt_messages())
    
    yield # O servidor está rodando
    
    print("Encerrando o servidor...")
    client.loop_stop() # Para a thread de rede
    client.disconnect()


# --- Inicialização do FastAPI ---

app = FastAPI(lifespan=lifespan)

# --- Endpoints da API ---

@app.get("/")
async def root():
    """Endpoint principal para verificar se o backend está ativo."""
    return {"message": "✅ Backend do simulador háptico ativo"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para comunicação em tempo real com o frontend."""
    await websocket.accept()
    connected_websockets.add(websocket)
    print(f"Novo cliente conectado. Total: {len(connected_websockets)}")
    
    try:
        while True:
            # Aguarda por uma mensagem do cliente (frontend)
            data = await websocket.receive_text()
            print(f"Comando recebido do frontend via WebSocket: {data}")
            
            # **PARTE COMPLETADA**: Publica a mensagem recebida no tópico de comandos do MQTT
            # para que o ESP32 possa recebê-la.
            websocket.app.state.mqtt_client.publish(MQTT_TOPIC_COMMANDS, data)
            
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
        print(f"Cliente desconectado. Total: {len(connected_websockets)}")
    except Exception as e:
        print(f"Ocorreu um erro no WebSocket: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

# Para rodar o backend, use o comando no terminal:
# uvicorn nome_do_arquivo:app --reload --host 0.0.0.0 --port 8000
