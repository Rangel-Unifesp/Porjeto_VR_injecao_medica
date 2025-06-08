import paho.mqtt.client as mqtt
import asyncio

# --- Configurações ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_SENSORS = "simulador/esp32/dados"
MQTT_TOPIC_COMMANDS = "simulador/esp32/comandos"

class MQTTHandler:
    """
    Uma classe para gerenciar a lógica do cliente MQTT de forma organizada.
    """
    def __init__(self, message_queue: asyncio.Queue):
        self.client = mqtt.Client()
        self.message_queue = message_queue

        # Associa os callbacks (on_connect, on_message) aos métodos da classe
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """Callback para quando o cliente se conecta ao broker."""
        if rc == 0:
            print("MQTT Handler: Conectado ao Broker com sucesso!")
            # Subscreve ao tópico de sensores assim que conecta
            client.subscribe(MQTT_TOPIC_SENSORS)
        else:
            print(f"MQTT Handler: Falha ao conectar, código: {rc}")

    def on_message(self, client, userdata, msg):
        """Callback para quando uma mensagem é recebida."""
        message = msg.payload.decode()
        print(f"MQTT Handler: Mensagem recebida de '{msg.topic}': {message}")
        # Coloca a mensagem na fila assíncrona para o FastAPI processar
        try:
            self.message_queue.put_nowait(message)
        except asyncio.QueueFull:
            print("MQTT Handler: Fila de mensagens cheia. Descartando mensagem.")

    def connect(self):
        """Conecta ao broker MQTT e inicia o loop de rede."""
        print("MQTT Handler: Conectando ao broker...")
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()  # Inicia uma thread em background para o MQTT

    def disconnect(self):
        """Para o loop de rede e desconecta do broker."""
        print("MQTT Handler: Desconectando do broker.")
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic: str, payload: str):
        """Publica uma mensagem em um tópico MQTT."""
        result = self.client.publish(topic, payload)
        # Verifica se a publicação foi bem-sucedida
        status = result[0]
        if status == 0:
            print(f"MQTT Handler: Mensagem '{payload}' enviada para o tópico '{topic}'")
        else:
            print(f"MQTT Handler: Falha ao enviar mensagem para o tópico '{topic}'")

