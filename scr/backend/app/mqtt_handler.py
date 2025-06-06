# scr/backend/app/mqtt_handler.py
import paho.mqtt.client as mqtt
import asyncio
import json

# Importa a lista de WebSockets conectados do ws_handler
# Esta é uma dependência circular simplificada para este exemplo.
# Em uma aplicação maior, considere usar callbacks, um bus de eventos, ou injeção de dependência.
try:
    from .ws_handler import connected_websockets
except ImportError:
    # Fallback para testes ou se a estrutura de importação direta falhar inicialmente
    print("ALERTA: Falha ao importar connected_websockets de .ws_handler. Usando lista mock.")
    connected_websockets = []


MQTT_BROKER = "mosquitto" # Ou o endereço do seu broker
MQTT_PORT = 1883
MQTT_TOPIC_ESP32_STATUS = "esp32/status" # Tópico para receber status do ESP32
# Novos nomes de tópicos conforme solicitado
MQTT_COMMAND_TOPIC_ESP32 = "simulador/esp32/comandos"
MQTT_FEEDBACK_TOPIC_ESP32 = "simulador/esp32/feedback_sofa"

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

async def send_message_to_clients(message_str: str):
    """ Envia uma mensagem para todos os clientes WebSocket conectados. """
    print(f"Tentando enviar para {len(connected_websockets)} clientes: {message_str}")
    if not connected_websockets:
        print("Nenhum cliente WebSocket conectado para enviar a mensagem MQTT.")
        return

    # Crie uma cópia da lista para evitar problemas se a lista for modificada durante a iteração
    sockets_to_send = list(connected_websockets)
    for websocket in sockets_to_send:
        try:
            await websocket.send_text(message_str)
            print(f"Mensagem enviada para o cliente WebSocket: {message_str}")
        except Exception as e:
            print(f"Erro ao enviar mensagem para o WebSocket: {e}")
            # Considere remover o websocket da lista se ele não estiver mais ativo,
            # mas cuidado com a modificação da lista enquanto itera.
            # A remoção já é tratada no ws_handler na desconexão.


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT com sucesso.")
        client.subscribe(MQTT_TOPIC_ESP32_STATUS) # Continua inscrito no status do ESP32
        print(f"Inscrito no tópico: {MQTT_TOPIC_ESP32_STATUS}")
        # A inscrição no MQTT_FEEDBACK_TOPIC_ESP32 (anteriormente MQTT_TOPIC_SOFA_FEEDBACK)
        # seria para o ESP32 se inscrever, não o backend. O backend publica neste tópico.
        # Se o backend precisar *receber* feedback do SOFA via MQTT (além do que já faz),
        # um novo tópico de subscrição seria necessário. Por ora, manteremos as subscrições existentes.
        # Se houver um tópico específico para o backend receber feedback do SOFA (que não seja para o ESP32),
        # ele deveria ser adicionado aqui. Ex: client.subscribe("sofa/backend/feedback")
    else:
        print(f"Falha ao conectar ao broker MQTT, código de retorno: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Mensagem recebida do MQTT - Tópico: {msg.topic}, Mensagem: {payload}")

    # Encaminha a mensagem para os clientes WebSocket.
    # O asyncio.run pode ser problemático se já houver um loop rodando.
    # Melhor usar asyncio.create_task se dentro de um contexto async,
    # ou uma forma de enfileirar a tarefa para o loop de eventos principal.
    # Para este exemplo, e dado que on_message é chamado em um thread do Paho,
    # precisamos de uma maneira de executar uma corrotina.
    try:
        # Tenta obter ou criar um loop de eventos para o thread atual do Paho
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            asyncio.create_task(send_message_to_clients(f"MQTT: {msg.topic}: {payload}"))
        else:
            loop.run_until_complete(send_message_to_clients(f"MQTT: {msg.topic}: {payload}"))

    except RuntimeError as e:
        # Se get_event_loop() falhar porque não há loop de eventos no thread atual
        print(f"RuntimeError ao obter event loop em on_message: {e}. Criando novo loop.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(send_message_to_clients(f"MQTT: {msg.topic}: {payload}"))
    except Exception as e:
        print(f"Exceção em on_message ao tentar enviar para WebSockets: {e}")


def init_mqtt():
    """Inicializa e configura o cliente MQTT."""
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"Conectando ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}...")
    except Exception as e:
        print(f"Erro ao conectar ao MQTT broker: {e}")
        # Tratar o erro (e.g., tentar reconectar, logar, sair)
        return False # Indica falha na inicialização

    # mqtt_client.loop_start() é chamado em main.py
    return True # Indica sucesso na inicialização

def publish_command_to_esp32(command_payload: str):
    """Publica um comando (string JSON) para o tópico de comandos do ESP32."""
    if mqtt_client.is_connected():
        result = mqtt_client.publish(MQTT_COMMAND_TOPIC_ESP32, command_payload, qos=1)
        print(f"[MQTT Handler] Publicando comando para ESP32 no tópico {MQTT_COMMAND_TOPIC_ESP32}: {command_payload}, Resultado: {result.rc}")
    else:
        print(f"[MQTT Handler] Cliente MQTT não conectado. Não foi possível enviar comando para ESP32.")

def publish_sofa_feedback_to_esp32(feedback_payload: str):
    """Publica feedback do SOFA (string JSON) para o tópico de feedback do ESP32."""
    if mqtt_client.is_connected():
        result = mqtt_client.publish(MQTT_FEEDBACK_TOPIC_ESP32, feedback_payload, qos=1)
        print(f"[MQTT Handler] Publicando feedback SOFA para ESP32 no tópico {MQTT_FEEDBACK_TOPIC_ESP32}: {feedback_payload}, Resultado: {result.rc}")
    else:
        print(f"[MQTT Handler] Cliente MQTT não conectado. Não foi possível enviar feedback SOFA para ESP32.")

# Para testes diretos do mqtt_handler (opcional)
if __name__ == '__main__':
    # Configuração para teste standalone
    if not connected_websockets: # Adiciona um mock WebSocket se estiver vazio
        class MockWebSocket:
            async def send_text(self, message):
                print(f"[MockWebSocket] Enviando: {message}")

            async def accept(self): print("[MockWebSocket] Conexão aceita")
            async def close(self): print("[MockWebSocket] Conexão fechada")

        mock_ws = MockWebSocket()
        # Simula a conexão de um cliente
        async def connect_mock():
            await mock_ws.accept()
            connected_websockets.append(mock_ws)

        loop = asyncio.get_event_loop()
        if not loop.is_running():
             loop.run_until_complete(connect_mock())
        else:
            asyncio.create_task(connect_mock())


    if init_mqtt():
        mqtt_client.loop_start()
        print("Cliente MQTT iniciado para teste. Enviando mensagem de teste...")
        try:
            # Teste de envio para ESP32
            test_cmd_payload = json.dumps({"action": "test_light", "value": "on"})
            publish_command_to_esp32(test_cmd_payload)

            # Simula recebimento de mensagem do ESP32 para encaminhar aos WebSockets
            # mqtt_client.publish(MQTT_TOPIC_ESP32_STATUS, '{"status":"test_ok"}')

            # Mantém o script rodando para o loop MQTT
            while True:
                pass
        except KeyboardInterrupt:
            print("Teste MQTT interrompido.")
        finally:
            mqtt_client.loop_stop()
            print("Loop MQTT parado.")
    else:
        print("Falha ao inicializar o cliente MQTT para teste.")
