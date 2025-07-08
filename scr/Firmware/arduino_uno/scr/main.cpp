#include <Wire.h>
#include <stdint.h> // Para tipos de dados com tamanho fixo


const int I2C_SLAVE_ADDRESS = 9;

// Pinos do Driver de Motor L298N
const int PIN_MOTOR_ENA = 9;  // PWM para controlar a velocidade
const int PIN_MOTOR_IN1 = 8;  // Controle de direção 1
const int PIN_MOTOR_IN2 = 7;  // Controle de direção 2

// Pino do Sensor de Força (FSR)
const int PIN_FSR = A0;       // Pino analógico

// Pinos do Encoder do Motor
const int PIN_ENCODER_A = 2;  // Deve ser um pino de interrupção (2 ou 3 no Uno/Nano)
const int PIN_ENCODER_B = 3;  // O outro pino de interrupção para determinar a direção

// --- Variáveis Globais ---
// 'volatile' é essencial para variáveis modificadas dentro de uma interrupção.
volatile int32_t encoderCount = 0;

// Estrutura de dados para ENVIAR para o mestre
// Usar tipos de tamanho fixo garante compatibilidade entre diferentes arquiteturas (ex: Arduino e ESP32)
struct SensorData {
  int16_t fsrValue;
  int32_t encoderValue;
};

// Enum para os estados/direções do motor para maior clareza do código
enum MotorState {
  BRAKE = 0,
  FORWARD = 1,
  REVERSE = 2
};

// Variáveis para RECEBER comandos do mestre
byte motorSpeed = 0;
MotorState motorDirection = BRAKE;


// Chamada quando o Mestre (ESP32) ENVIA dados para este Escravo.
// Usada para receber comandos de controle do motor.
void receiveEvent(int howMany) {
  // Lê os comandos apenas se o número esperado de bytes foi recebido
  if (howMany >= 2) {
    motorDirection = (MotorState)Wire.read(); // Primeiro byte é a direção
    motorSpeed = Wire.read();                 // Segundo byte é a velocidade
  }

  // Limpa o buffer de recepção para descartar quaisquer bytes extras e evitar erros
  while (Wire.available() > 0) {
    Wire.read();
  }
}

// Chamada quando o Mestre (ESP32) SOLICITA dados deste Escravo.
// Usada para enviar os dados dos sensores.
void requestEvent() {
  SensorData data;
  data.fsrValue = analogRead(PIN_FSR);
  
  // Lê o valor do encoder de forma segura (desabilitando interrupções brevemente)
  noInterrupts();
  data.encoderValue = encoderCount;
  interrupts();
  
  // Envia os bytes da estrutura de dados de volta para o Mestre
  Wire.write((byte*)&data, sizeof(data));
}

// --- Função de Interrupção do Encoder ---
// Chamada a cada pulso de subida no pino A do encoder.
void updateEncoder() {
  // A leitura do pino B dentro da interrupção do pino A nos permite determinar a direção.
  // Se o pino B estiver em nível baixo quando o A sobe, a rotação é em um sentido.
  // Se estiver em nível alto, é no sentido oposto.
  // A direção exata (horário/anti-horário) depende da fiação e pode ser invertida
  // trocando encoderCount++ por encoderCount--.
  if (digitalRead(PIN_ENCODER_B) == LOW) {
    encoderCount++; // Assumindo rotação em um sentido
  } else {
    encoderCount--; // Rotação no sentido oposto
  }
}

// --- Função para controlar o motor ---
void setMotor() {
  switch (motorDirection) {
    case FORWARD: // Frente
      digitalWrite(PIN_MOTOR_IN1, HIGH);
      digitalWrite(PIN_MOTOR_IN2, LOW);
      analogWrite(PIN_MOTOR_ENA, motorSpeed);
      break;
    case REVERSE: // Ré
      digitalWrite(PIN_MOTOR_IN1, LOW);
      digitalWrite(PIN_MOTOR_IN2, HIGH);
      analogWrite(PIN_MOTOR_ENA, motorSpeed);
      break;
    case BRAKE: // Freio (ou Parado)
    default:
      digitalWrite(PIN_MOTOR_IN1, LOW);
      digitalWrite(PIN_MOTOR_IN2, LOW);
      analogWrite(PIN_MOTOR_ENA, 0);
      break;
  }
}


void setup() {
  Serial.begin(115200);
  Serial.println("Controlador Háptico (Arduino) - Escravo I2C Inicializado");

  // Configura os pinos do motor como saída
  pinMode(PIN_MOTOR_ENA, OUTPUT);
  pinMode(PIN_MOTOR_IN1, OUTPUT);
  pinMode(PIN_MOTOR_IN2, OUTPUT);

  // Configura o pino do FSR como entrada
  pinMode(PIN_FSR, INPUT);

  // Configura a interrupção para o encoder
  pinMode(PIN_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_ENCODER_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_A), updateEncoder, RISING);

  // Inicia o I2C como escravo
  Wire.begin(I2C_SLAVE_ADDRESS);
  // Registra as funções de callback
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
}

void loop() {
  // A principal tarefa no loop é aplicar o estado mais recente do motor,
  // que foi definido pelos comandos recebidos via I2C.
  setMotor();

  // Pequeno delay para estabilidade, embora não estritamente necessário.
  delay(10);
}