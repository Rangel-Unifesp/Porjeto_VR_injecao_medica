#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <ArduinoJson.h>

// --- Configurações de Rede e MQTT ---
const char* SSID = "NOME_DA_SUA_REDE_WIFI";
const char* PASSWORD = "SENHA_DA_SUA_REDE_WIFI";
// Use "mosquitto" se estiver rodando via Docker Compose, ou o IP da máquina host
const char* MQTT_BROKER = "192.168.1.10"; 
const int   MQTT_PORT = 1883;

// --- Tópicos MQTT ---
const char* MQTT_DATA_TOPIC = "simulador/haptico/dados";    // Para PUBLICAR dados dos sensores
const char* MQTT_COMMAND_TOPIC = "simulador/haptico/comandos"; // Para OUVIR comandos de força

// --- Configurações I2C ---
const int ARDUINO_SLAVE_ADDRESS = 9;

// Estrutura de dados para RECEBER do escravo.
// DEVE SER IDÊNTICA à definida no código do Arduino.
struct SensorData {
  int fsrValue;
  long encoderValue;
};

// --- Clientes de Rede ---
WiFiClient espClient;
PubSubClient client(espClient);

// --- Controle de Tempo (Não-bloqueante) ---
unsigned long lastSensorRequestTime = 0;
const long sensorRequestInterval = 100; // Solicita dados dos sensores 10x por segundo


// --- Funções de Rede (setup_wifi e reconnect são as mesmas de antes) ---
void setup_wifi() { delay(10); Serial.print("\nConectando a "); Serial.println(SSID); WiFi.begin(SSID, PASSWORD); while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); } Serial.println("\nWiFi conectado!"); Serial.print("IP: "); Serial.println(WiFi.localIP()); }
void reconnect() { while (!client.connected()) { Serial.print("Tentando conexão MQTT..."); if (client.connect("ESP32_HapticGateway")) { Serial.println("conectado!"); client.subscribe(MQTT_COMMAND_TOPIC); } else { Serial.print("falhou, rc="); Serial.print(client.state()); Serial.println(" tentando novamente em 5s"); delay(5000); } } }

// --- Função para enviar comando para o Arduino via I2C ---
void sendMotorCommand(byte direction, byte speed) {
  Wire.beginTransmission(ARDUINO_SLAVE_ADDRESS);
  Wire.write(direction); // Envia o byte da direção
  Wire.write(speed);     // Envia o byte da velocidade
  Wire.endTransmission();
}

// --- Callback MQTT: Chamada ao receber um comando do backend ---
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Comando recebido do MQTT: ");
  Serial.write(payload, length);
  Serial.println();

  StaticJsonDocument<200> doc;
  deserializeJson(doc, payload, length);

  // Extrai os valores do JSON recebido
  // Exemplo de JSON esperado: {"direction": 1, "speed": 200}
  byte direction = doc["direction"]; // 0=parado, 1=frente, 2=ré
  byte speed = doc["speed"];         // 0-255

  // Envia o comando para o Arduino
  sendMotorCommand(direction, speed);
}

void setup() {
  Serial.begin(115200);

  // Inicia o I2C como Mestre (pinos padrão 21=SDA, 22=SCL)
  Wire.begin(); 

  setup_wifi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); // Essencial para o MQTT

  // --- Lógica de polling de sensores (não-bloqueante) ---
  if (millis() - lastSensorRequestTime >= sensorRequestInterval) {
    lastSensorRequestTime = millis();

    // 1. Solicita os dados do Arduino
    // O segundo parâmetro é o número de bytes esperados (tamanho da struct)
    Wire.requestFrom(ARDUINO_SLAVE_ADDRESS, sizeof(SensorData));

    // 2. Lê os dados se estiverem disponíveis
    if (Wire.available() >= sizeof(SensorData)) {
      SensorData receivedData;
      Wire.readBytes((byte*)&receivedData, sizeof(receivedData));

      // 3. Prepara um JSON para publicar os dados no MQTT
      StaticJsonDocument<200> doc;
      doc["fsr"] = receivedData.fsrValue;
      doc["encoder"] = receivedData.encoderValue;

      char buffer[200];
      serializeJson(doc, buffer);
      
      // 4. Publica no MQTT
      client.publish(MQTT_DATA_TOPIC, buffer);
      // Serial.print("Dados publicados no MQTT: ");
      // Serial.println(buffer);
    }
  }
}