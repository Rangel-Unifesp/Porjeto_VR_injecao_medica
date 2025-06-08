from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("Nova conexão WebSocket estabelecida.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print("Conexão WebSocket fechada.")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        send_tasks = [connection.send_text(message) for connection in self.active_connections]
        
        results = await asyncio.gather(*send_tasks, return_exceptions=True)


        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Falha ao enviar mensagem para um cliente (provavelmente desconectado): {result}")
