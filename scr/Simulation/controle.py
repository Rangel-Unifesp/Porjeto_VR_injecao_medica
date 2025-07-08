import paho.mqtt.client as mqtt
import json
import time
import threading

# --- Configurações MQTT ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# --- Tópicos para comunicação ---
# Tópicos do Simulador SOFA
TOPIC_SOFA_COMMANDS = "simulador/sofa/comandos"  # Para enviar comandos para o SOFA
TOPIC_SOFA_RESULTS = "simulador/sofa/resultados"    # Para receber resultados do SOFA

# Tópicos do Dispositivo Háptico (ESP32)
TOPIC_HAPTIC_COMMANDS = "simulador/haptico/comandos" # Para enviar comandos para o motor
TOPIC_HAPTIC_DATA = "simulador/haptico/dados"        # Para receber dados dos sensores

# --- Variáveis Globais para armazenar o último estado conhecido ---
last_haptic_data = {"encoder": 0, "fsr": 0}
last_sofa_results = {"force_feedback": [0, 0, 0], "needle_tip_position": [0, 0, 0]}
data_lock = threading.Lock()
connection_event = threading.Event()

# --- Mapeamento e Calibração ---
# Estes valores precisam ser calibrados para corresponder o movimento físico com o virtual
ENCODER_TO_MM_SCALE = 0.01  # Ex: 100 pulsos do encoder = 1mm de movimento
INITIAL_Y_POSITION_MM = 50.0 # Posição inicial da agulha no simulador

# --- Funções de Callback MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado ao Broker!")
        client.subscribe([(TOPIC_SOFA_RESULTS, 0), (TOPIC_HAPTIC_DATA, 0)])
        print(f"[MQTT] Inscrito em: {TOPIC_SOFA_RESULTS} e {TOPIC_HAPTIC_DATA}")
        connection_event.set()
    else:
        print(f"[MQTT] Falha na conexão, código: {rc}")

def on_message(client, userdata, msg):
    """Atualiza as variáveis globais com os dados mais recentes recebidos."""
    global last_haptic_data, last_sofa_results
    try:
        payload = json.loads(msg.payload.decode())
        with data_lock:
            if msg.topic == TOPIC_HAPTIC_DATA:
                last_haptic_data.update(payload)
            elif msg.topic == TOPIC_SOFA_RESULTS:
                last_sofa_results.update(payload)
    except (json.JSONDecodeError, KeyError):
        pass

# --- Funções de Controle ---
def control_loop(client):
    """Loop principal que executa a lógica de controle."""
    print("[Controlador] Loop de controle iniciado. Pressione Ctrl+C para sair.")
    
    # Define a posição inicial da agulha no SOFA
    initial_payload = {"command": "move_needle", "value": [0, INITIAL_Y_POSITION_MM, 0, 0, 0, 0]}
    client.publish(TOPIC_SOFA_COMMANDS, json.dumps(initial_payload))

    while True:
        with data_lock:
            current_encoder = last_haptic_data["encoder"]
            force_feedback_y = last_sofa_results["force_feedback"][1] # Usamos a força no eixo Y

        # 1. Mover a agulha na simulação com base no encoder
        new_needle_y = INITIAL_Y_POSITION_MM + (current_encoder * ENCODER_TO_MM_SCALE)
        move_payload = {"command": "move_needle", "value": [0, new_needle_y, 0, 0, 0, 0]}
        client.publish(TOPIC_SOFA_COMMANDS, json.dumps(move_payload))

        # 2. Aplicar força no motor com base no feedback da simulação
        motor_direction = 0  # 0: BRAKE
        motor_speed = 0

        # Se a força de resistência (negativa) for significativa, ligue o motor para "empurrar de volta"
        if force_feedback_y < -0.1: # Limiar de força para ativar o motor
            motor_direction = 2  # 2: REVERSE (puxando contra o usuário)
            # Mapeia a força para a velocidade do motor (0-255)
            motor_speed = min(int(abs(force_feedback_y) * 500), 255) # Fator de escala da força
        
        force_payload = {"direction": motor_direction, "speed": motor_speed}
        client.publish(TOPIC_HAPTIC_COMMANDS, json.dumps(force_payload))
        
        # Imprime o estado atual
        print(f"Encoder: {current_encoder:6d} -> Pos Y: {new_needle_y:5.2f} mm | Força Y: {force_feedback_y:6.3f} N -> Motor Velo: {motor_speed:3d}\r", end="")

        time.sleep(0.05) # Frequência do loop de controle (20 Hz)

# --- Função Principal ---
if __name__ == "__main__":
    client = mqtt.Client("haptic_controller_py")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print("[Main] Aguardando conexão MQTT...")
    connection_event.wait(timeout=10)

    if not connection_event.is_set():
        print("[Main] Não foi possível conectar ao broker. Encerrando.")
    else:
        try:
            control_loop(client)
        except KeyboardInterrupt:
            print("\n[Main] Encerrando por solicitação do usuário.")
        finally:
            # Para o motor ao sair
            client.publish(TOPIC_HAPTIC_COMMANDS, json.dumps({"direction": 0, "speed": 0}))

    client.loop_stop()
    client.disconnect()
    print("[Main] Desconectado.")
