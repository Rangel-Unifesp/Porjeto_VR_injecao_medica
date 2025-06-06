# scr/backend/app/main.py
from fastapi import FastAPI
import asyncio

# Importar os handlers e outros módulos necessários
from .ws_handler import router as websocket_router
from .mqtt_handler import init_mqtt, mqtt_client # Importa o cliente MQTT e a função de inicialização
# from .sofa_bridge import ... # Se necessário no futuro diretamente em main

app = FastAPI(title="Simulador Háptico Backend")

# Incluir o APIRouter do WebSocket Handler
app.include_router(websocket_router)

# Inicializar e configurar o cliente MQTT
if not init_mqtt():
    print("ALERTA CRÍTICO: Falha ao inicializar o cliente MQTT. Algumas funcionalidades podem não operar.")
    # Aqui você pode decidir se a aplicação deve parar ou continuar com funcionalidade reduzida.
    # Por exemplo, levantar uma SystemExit: raise SystemExit("Falha na inicialização do MQTT.")

@app.on_event("startup")
async def startup_event():
    print("Iniciando aplicação FastAPI...")
    # Iniciar o loop do cliente MQTT em um thread separado
    # Isso é crucial para que ele não bloqueie o loop de eventos do FastAPI/Uvicorn
    try:
        mqtt_client.loop_start()
        print("Loop do cliente MQTT iniciado.")
    except Exception as e:
        print(f"Erro ao iniciar o loop do cliente MQTT: {e}")
        # Considerar logar este erro ou tratá-lo de forma mais robusta

@app.on_event("shutdown")
async def shutdown_event():
    print("Encerrando aplicação FastAPI...")
    # Parar o loop do cliente MQTT
    try:
        mqtt_client.loop_stop()
        print("Loop do cliente MQTT parado.")
    except Exception as e:
        print(f"Erro ao parar o loop do cliente MQTT: {e}")
    # Outras limpezas, se necessário

@app.get("/")
async def root():
    return {"message": "Backend do Simulador Háptico Modularizado Ativo"}

# Para rodar o backend (exemplo):
# uvicorn scr.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# Ajuste o comando conforme a estrutura do seu projeto se estiver rodando de fora da pasta 'app'
# Por exemplo, de dentro de 'scr/backend': uvicorn app.main:app --reload
# Ou da raiz do projeto: python -m uvicorn scr.backend.app.main:app --reload
