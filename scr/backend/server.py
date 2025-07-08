from flask import Flask, send_from_directory
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading

# --- Configurações ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SOFA_RESULTS = "simulador/sofa/resultados"
STATIC_FOLDER = '../frontend' # Pasta onde estão seus arquivos HTML, CSS, JS

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Lógica MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT-Backend] Conectado ao Broker!")
        client.subscribe(TOPIC_SOFA_RESULTS)
    else:
        print(f"[MQTT-Backend] Falha na conexão, código: {rc}")

def on_message(client, userdata, msg):
    """Recebe dados do SOFA e retransmite via WebSocket."""
    try:
        payload = json.loads(msg.payload.decode())
        # Envia apenas os dados relevantes para o frontend
        if "needle_tip_position" in payload:
            # Emite um evento chamado 'update_scene' para todos os clientes conectados
            socketio.emit('update_scene', {'position': payload['needle_tip_position']})
    except Exception as e:
        print(f"[WebSocket] Erro ao processar mensagem: {e}")

def mqtt_thread_func():
    client = mqtt.Client("backend_server_listener")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# --- Rotas HTTP ---
@app.route('/')
def serve_index():
    """Serve o arquivo principal do frontend."""
    return send_from_directory(STATIC_FOLDER, 'Interacao3d.HTML')

# --- Main ---
if __name__ == '__main__':
    print("[Backend] Iniciando o servidor web e o listener MQTT...")
    
    # Inicia o cliente MQTT em uma thread separada
    mqtt_thread = threading.Thread(target=mqtt_thread_func)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    # Inicia o servidor Flask-SocketIO
    # Usar '0.0.0.0' torna o servidor acessível na sua rede local
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 