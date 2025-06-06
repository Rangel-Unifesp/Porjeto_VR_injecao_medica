import paho.mqtt.client as mqtt
import json
import time
import threading


MQTT_BROKER = "localhost"
MQTT_PORT = 1883


TOPIC_SOFA_COMMANDS = "simulador/sofa/comandos"

TOPIC_SOFA_RESULTS = "simulador/sofa/resultados"

last_force_feedback = [0, 0, 0]
last_needle_position = [0, 0, 0]
connected = threading.Event() 

def on_connect(client, userdata, flags, rc):
    """Callback para quando nos conectamos ao broker."""
    if rc == 0:
        print("[Controle] Conectado ao MQTT Broker com sucesso!")
        client.subscribe(TOPIC_SOFA_RESULTS)
        print(f"[Controle] Inscrito no tópico de resultados: {TOPIC_SOFA_RESULTS}")
        connected.set() 
    else:
        print(f"[Controle] Falha ao conectar, código de retorno: {rc}")
        connected.clear()

def on_message(client, userdata, msg):
    """Callback para quando recebemos uma mensagem do broker."""
    global last_force_feedback, last_needle_position
    try:
        data = json.loads(msg.payload.decode())
        if "force_feedback" in data and "needle_tip_position" in data:
            last_force_feedback = data["force_feedback"]
            last_needle_position = data["needle_tip_position"]
            ff_x = f"{last_force_feedback[0]:.2f}".rjust(8)
            ff_y = f"{last_force_feedback[1]:.2f}".rjust(8)
            ff_z = f"{last_force_feedback[2]:.2f}".rjust(8)
            pos_y = f"{last_needle_position[1]:.2f}".rjust(6)
            print(f"Posição da Ponta (Y): {pos_y} mm | Força (X, Y, Z): [{ff_x}, {ff_y}, {ff_z}] N\r", end="")

    except (json.JSONDecodeError, KeyError):
        pass

def publish_needle_position(client, y_pos):
    
    new_position = [0, 60, 0,  
                    0, float(y_pos), 0] 
    
    payload = {
        "command": "move_needle",
        "value": new_position
    }
    
    client.publish(TOPIC_SOFA_COMMANDS, json.dumps(payload))
    print("\n[Controle] Comando 'move_needle' enviado.")


if __name__ == "__main__":
    
    client = mqtt.Client("control_client")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print("[Controle] Aguardando conexão com o broker...")
    connected.wait(timeout=5) 

    if not connected.is_set():
        print("[Controle] Não foi possível conectar ao broker. Encerrando.")
        client.loop_stop()
        exit()

    print("\n--- Controle Remoto do Simulador ---")
    print("Mova a ponta da agulha no eixo Y.")
    print("Digite um valor numérico (ex: 45.5) e pressione Enter.")
    print("Digite 'sair' para encerrar.")
    print("-" * 35)

    try:
        
        publish_needle_position(client, 50)
        
        while True:
            command = input("\nNova posição Y para a ponta da agulha: ")
            if command.lower() == 'sair':
                break
            try:
                y_position = float(command)
                publish_needle_position(client, y_position)
            except ValueError:
                print("[Controle] Erro: Por favor, insira um valor numérico válido.")

    except KeyboardInterrupt:
        print("\n[Controle] Encerrando por solicitação do usuário.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[Controle] Desconectado e encerrado.")