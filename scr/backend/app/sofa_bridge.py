import paho.mqtt.client as mqtt
import time
import json

# Tenta importar as bibliotecas do SOFA
try:
    import Sofa
    import Sofa.Core
    import Sofa.Helper
except ImportError:
    print("ERRO: Este script precisa ser executado com o Python do SOFA (runSofa).")
    exit()

# ### ALTERADO ###: Importa a função que cria a cena do nosso novo arquivo
from injecao import create_injection_scene


# --- Configurações do MQTT (sem alterações) ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SOFA_COMMANDS = "simulador/sofa/comandos"
TOPIC_SOFA_RESULTS = "simulador/sofa/resultados"

# --- Variável global para os nós do SOFA ---
sofa_handles = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("SOFA Bridge: Conectado ao MQTT Broker!")
        client.subscribe(TOPIC_SOFA_COMMANDS)
        print(f"SOFA Bridge: Inscrito no tópico '{TOPIC_SOFA_COMMANDS}'.")
    else:
        print(f"SOFA Bridge: Falha ao conectar, código {rc}")

def on_message(client, userdata, msg):
    print(f"SOFA Bridge: Mensagem recebida no tópico '{msg.topic}'")
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("SOFA Bridge: Erro ao decodificar JSON.")
        return

    if msg.topic == TOPIC_SOFA_COMMANDS:
        command = payload.get("command")
        value = payload.get("value")

        # ### ALTERADO ###: A lógica de comando agora usa os handles de 'injecao.py'
        if command == "move_needle":
            if sofa_handles and "needle_mo" in sofa_handles and isinstance(value, list) and len(value) == 6:
                print(f"SOFA Bridge: Movendo agulha para {value}")
                # Atualiza a posição da agulha usando o handle que recebemos
                with sofa_handles["needle_mo"].position.writeable() as positions:
                    for i in range(len(value)):
                        positions.value[i] = value[i]
        else:
            print(f"SOFA Bridge: Comando desconhecido '{command}'")

def main():
    # 1. Inicializar o SOFA
    root = Sofa.Core.Node("root")
    
    # ### ALTERADO ###: A criação da cena agora é delegada para o módulo injecao.py
    # A variável global 'sofa_handles' recebe as referências da cena.
    global sofa_handles 
    # A função do outro arquivo é chamada aqui para construir a simulação!
    sofa_handles = create_injection_scene(root)
    
    Sofa.Core.init(root)
    
    # 2. Configurar e Conectar o Cliente MQTT (sem alterações)
    client = mqtt.Client("sofa_bridge_client")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except ConnectionRefusedError:
        print("SOFA Bridge: ERRO - Conexão com o broker MQTT recusada.")
        return
    client.loop_start()

    print("\n--- SOFA Bridge está rodando ---")
    print("Pressione Ctrl+C para sair.")

    # 3. Loop Principal da Simulação
    try:
        while True:
            Sofa.Core.animate(root, root.dt.value)
            
            # ### ALTERADO ###: A leitura de resultados agora usa os handles de 'injecao.py'
            # Lendo a força de contato do handle que recebemos.
            # O 'force' é um array, pegamos o primeiro valor (força em X, Y, Z).
            contact_force = sofa_handles["interaction_force"].force.value[0].tolist()

            # Lendo a posição atual da ponta da agulha
            needle_tip_position = sofa_handles["needle_mo"].position.value[1].tolist()
            
            simulation_results = {
                "timestamp": time.time(),
                "force_feedback": contact_force,
                "needle_tip_position": needle_tip_position
            }
            
            client.publish(TOPIC_SOFA_RESULTS, json.dumps(simulation_results))
            time.sleep(root.dt.value)

    except KeyboardInterrupt:
        print("\nSOFA Bridge: Encerrando...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("SOFA Bridge: Desconectado do MQTT. Fim.")

if __name__ == "__main__":
    main()
