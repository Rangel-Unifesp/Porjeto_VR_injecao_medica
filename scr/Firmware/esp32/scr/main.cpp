#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h> // Para parsear e criar mensagens JSON

// Configurações de Wi-Fi
const char* WIFI_SSID = "SEU_WIFI_SSID"; // Substitua pelo SSID da sua rede
const char* WIFI_PASSWORD = "SUA_WIFI_SENHA"; // Substitua pela senha da sua rede

// Configurações do Broker MQTT
const char* MQTT_BROKER = "192.168.1.100"; // Substitua pelo IP do seu broker MQTT (máquina rodando o docker-compose)
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "esp32-haptic-simulator";

// Tópicos MQTT (devem alinhar com o backend)
const char* MQTT_TOPIC_STATUS_ESP32 = "esp32/status";
const char* MQTT_TOPIC_COMMANDS_FROM_BACKEND = "simulador/esp32/comandos";
const char* MQTT_TOPIC_FEEDBACK_SOFA_FROM_BACKEND = "simulador/esp32/feedback_sofa";

// Pinos (mesmo que simulados, é bom definir)
// const int FSR_PIN = 34; // Exemplo para um pino ADC
// const int MOTOR_EN_PIN = 13; // Enable para L298N
// const int MOTOR_IN1_PIN = 12;
// const int MOTOR_IN2_PIN = 14;
// const int ENCODER_A_PIN = 25;
// const int ENCODER_B_PIN = 26;

// Variáveis globais para simulação
int simulated_fsr_value = 0;
long simulated_encoder_position = 0;
bool motor_active = false;
int motor_speed = 0; // 0-255
int motor_direction = 1; // 1 para frente, -1 para trás

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastMsg = 0;
char msg[256]; // Buffer para mensagens MQTT

void setupWifi() {
    delay(10);
    Serial.println();
    Serial.print("Conectando a ");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int retries = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        if (retries++ > 20) { // Tenta por 10 segundos
            Serial.println("\nFalha ao conectar ao WiFi. Reiniciando...");
            ESP.restart();
        }
    }

    Serial.println("");
    Serial.println("WiFi conectado!");
    Serial.print("Endereco IP: ");
    Serial.println(WiFi.localIP());
}

void controlMotor(bool active, int speed, int direction) {
    motor_active = active;
    motor_speed = constrain(speed, 0, 255); // Garante que a velocidade esteja entre 0-255
    motor_direction = direction;

    if (motor_active) {
        Serial.print("Motor ATIVADO. Velocidade: ");
        Serial.print(motor_speed);
        Serial.print(", Direcao: ");
        Serial.println(motor_direction == 1 ? "FRENTE" : "TRAS");
        // Lógica real de controle do L298N viria aqui:
        // digitalWrite(MOTOR_IN1_PIN, direction == 1 ? HIGH : LOW);
        // digitalWrite(MOTOR_IN2_PIN, direction == 1 ? LOW : HIGH);
        // analogWrite(MOTOR_EN_PIN, motor_speed); // Ou ledcWrite para ESP32
    } else {
        Serial.println("Motor DESATIVADO.");
        // analogWrite(MOTOR_EN_PIN, 0);
    }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Mensagem recebida no topico: ");
    Serial.println(topic);
    Serial.print("Payload: ");
    String received_payload_str = "";
    for (unsigned int i = 0; i < length; i++) {
        received_payload_str += (char)payload[i];
    }
    Serial.println(received_payload_str);
    Serial.println("-----------------------");

    StaticJsonDocument<256> doc; // Aumentar o tamanho para acomodar payloads maiores
    DeserializationError error = deserializeJson(doc, payload, length);

    if (error) {
        Serial.print(F("deserializeJson() falhou: "));
        Serial.println(error.f_str());
        return;
    }

    if (strcmp(topic, MQTT_TOPIC_COMMANDS_FROM_BACKEND) == 0) {
        const char* event = doc["event"];
        if (event) {
            Serial.print("Evento recebido do backend: ");
            Serial.println(event);

            if (strcmp(event, "injection_start") == 0) {
                Serial.println("Simulando inicio da injecao: motor resistindo.");
                // Simular resistência: motor "puxando" contra o usuário
                controlMotor(true, 150, -1); // Ativa motor, velocidade média, direção "para trás"
            } else if (strcmp(event, "injection_stop") == 0) { // Novo evento para parar
                Serial.println("Simulando fim da injecao: motor para.");
                controlMotor(false, 0, 0);
            } else if (strcmp(event, "hand_position_update") == 0) {
                // Poderia usar a posição da mão para algo, mas por enquanto só log
                // Exemplo se o payload for {"event": "hand_position_update", "payload": {"position": {"x": 0.1, ...}}}
                // ou {"event": "hand_position_update", "position": "0.1 0.2 0.3"} como no backend ws_handler
                if (doc.containsKey("position")) {
                     // Se position for um objeto:
                     // float x = doc["position"]["x"];
                     // Serial.print("Posicao da mao recebida (simulado): x="); Serial.println(x);
                     // Se position for uma string:
                     const char* pos_str = doc["position"];
                     Serial.print("Posicao da mao recebida (string): "); Serial.println(pos_str);
                }
            } else {
                 Serial.print("Evento desconhecido em comandos do backend: "); Serial.println(event);
            }
        } else {
            Serial.println("Campo 'event' ausente no comando do backend.");
        }
    } else if (strcmp(topic, MQTT_TOPIC_FEEDBACK_SOFA_FROM_BACKEND) == 0) {
        if (doc.containsKey("type") && strcmp(doc["type"], "force") == 0) {
            float force_value = doc["value"]; // Range de 0.0 a 1.0 (exemplo)
            Serial.print("Feedback de forca do SOFA recebido: ");
            Serial.println(force_value);

            // Mapear force_value (0.0 a 1.0) para velocidade do motor (0 a 255)
            int target_speed = (int)(force_value * 255.0);
            Serial.print("Aplicando forca no motor (velocidade): ");
            Serial.println(target_speed);
            controlMotor(true, target_speed, -1); // Resistência proporcional à força
        } else {
            Serial.println("Tipo de feedback SOFA desconhecido ou chave 'type' ausente.");
        }
    }
}

void reconnectMqtt() {
    while (!mqttClient.connected()) {
        Serial.print("Tentando conexao MQTT...");
        if (mqttClient.connect(MQTT_CLIENT_ID)) {
            Serial.println("conectado!");
            mqttClient.subscribe(MQTT_TOPIC_COMMANDS_FROM_BACKEND);
            Serial.print("Subscrito a: "); Serial.println(MQTT_TOPIC_COMMANDS_FROM_BACKEND);
            mqttClient.subscribe(MQTT_TOPIC_FEEDBACK_SOFA_FROM_BACKEND);
            Serial.print("Subscrito a: "); Serial.println(MQTT_TOPIC_FEEDBACK_SOFA_FROM_BACKEND);

            StaticJsonDocument<128> statusDoc;
            statusDoc["deviceId"] = MQTT_CLIENT_ID;
            statusDoc["status"] = "online";
            statusDoc["ip"] = WiFi.localIP().toString();

            String output;
            serializeJson(statusDoc, output);
            mqttClient.publish(MQTT_TOPIC_STATUS_ESP32, output.c_str());
            Serial.print("Status inicial publicado em "); Serial.println(MQTT_TOPIC_STATUS_ESP32);

        } else {
            Serial.print("falhou, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" tentando novamente em 5 segundos");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    // pinMode(FSR_PIN, INPUT);
    // pinMode(MOTOR_EN_PIN, OUTPUT);
    // ... etc para outros pinos
    Serial.println("Pinos configurados (simulado).");

    setupWifi();
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Conexão WiFi perdida. Tentando reconectar...");
        setupWifi();
    }

    if (!mqttClient.connected()) {
        reconnectMqtt();
    }
    mqttClient.loop();

    unsigned long now = millis();

    // Simular leitura de FSR e Encoder
    if (motor_active && motor_direction == 1) {
        simulated_fsr_value += 10;
        simulated_encoder_position += 50;
    } else if (motor_active && motor_direction == -1) {
         simulated_fsr_value += 5;
    } else {
        if(simulated_fsr_value > 0) simulated_fsr_value -=5;
    }
    simulated_fsr_value = constrain(simulated_fsr_value, 0, 1023);
    if (simulated_encoder_position < 0) simulated_encoder_position = 0; // Exemplo de limite para encoder


    if (now - lastMsg > 5000) { // Publica a cada 5 segundos
        lastMsg = now;

        StaticJsonDocument<256> sensorDataDoc;
        sensorDataDoc["deviceId"] = MQTT_CLIENT_ID;
        sensorDataDoc["timestamp"] = millis();
        sensorDataDoc["fsr_value"] = simulated_fsr_value;
        sensorDataDoc["encoder_position"] = simulated_encoder_position;
        sensorDataDoc["motor_active"] = motor_active;
        sensorDataDoc["motor_speed"] = motor_speed;
        sensorDataDoc["motor_direction"] = motor_direction;

        String output;
        serializeJson(sensorDataDoc, output);

        snprintf(msg, sizeof(msg), "%s", output.c_str());
        Serial.print("Publicando status/dados sensores: ");
        Serial.println(msg);
        mqttClient.publish(MQTT_TOPIC_STATUS_ESP32, msg);
    }
}
