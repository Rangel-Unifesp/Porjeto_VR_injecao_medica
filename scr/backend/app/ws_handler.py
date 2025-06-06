# scr/backend/app/ws_handler.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json # Para formatar e parsear payloads JSON

# Importar os módulos do backend
from . import sofa_bridge
from . import mqtt_handler as backend_mqtt_handler # Renomeado para clareza

router = APIRouter()

connected_websockets: List[WebSocket] = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    client_ip = websocket.client.host if websocket.client else "desconhecido"
    print(f"Novo cliente WebSocket conectado: {client_ip}. Total: {len(connected_websockets)}")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WS Handler] Mensagem recebida do frontend ({client_ip}): {data}")

            try:
                command_data = json.loads(data) # Assumindo que o frontend envia JSON
                action = command_data.get("action")
                payload = command_data.get("payload", {}) # Pegar o payload, default para dict vazio
            except json.JSONDecodeError:
                print(f"[WS Handler] Mensagem não é JSON válido: {data}")
                await websocket.send_text(json.dumps({"source": "backend", "status": "error", "message": f"Erro: Mensagem não é JSON válido: {data}"}))
                continue # Pula para a próxima mensagem

            if action == "injetar":
                print(f"[WS Handler] Comando '{action}' recebido com payload: {payload}")

                # 1. Enviar comando para SOFA (simulado)
                # O payload de command_data (que é o `payload` aqui) é passado para o SOFA
                sofa_command_full = {"action": action, **payload} # Recria o dict original para SOFA
                sofa_response = await sofa_bridge.send_command_to_sofa(sofa_command_full)
                print(f"[WS Handler] Resposta do SOFA Bridge: {sofa_response}")

                # Enviar resposta do SOFA de volta para o cliente WebSocket que enviou o comando
                await websocket.send_text(json.dumps({"source": "sofa_bridge", "data": sofa_response}))

                # 2. Enviar comando/info para ESP32 via MQTT
                # Exemplo: notificar ESP32 sobre o início da injeção
                # Usar o payload original do comando "injetar" para detalhes
                esp32_command_payload_dict = {"event": "injection_start", "details": payload}
                backend_mqtt_handler.publish_command_to_esp32(json.dumps(esp32_command_payload_dict))

                # Se SOFA retornou feedback de força, enviar para ESP32
                if "force_feedback" in sofa_response: # Checa se a chave existe
                    force_payload_dict = {"type": "force", "value": sofa_response["force_feedback"]}
                    backend_mqtt_handler.publish_sofa_feedback_to_esp32(json.dumps(force_payload_dict))

            elif action == "mover_mao":
                position = payload.get("position") # Espera {"action": "mover_mao", "payload": {"position": "0.1 0.2 0.3"}}
                print(f"[WS Handler] Comando '{action}' recebido com dados de posição: {position}")

                # Lógica para mover a mão (pode interagir com SOFA ou apenas atualizar estado no backend)
                # Exemplo de interação com SOFA para mover_mao
                sofa_command_move = {"action": action, "position": position}
                sofa_response_move = await sofa_bridge.send_command_to_sofa(sofa_command_move)
                print(f"[WS Handler] Resposta do SOFA Bridge para '{action}': {sofa_response_move}")
                await websocket.send_text(json.dumps({"source": "sofa_bridge", "action": action, "data": sofa_response_move}))

                # Poderia também enviar a posição da mão para o ESP32 se necessário
                esp32_hand_pos_payload_dict = {"event": "hand_position_update", "position": position}
                backend_mqtt_handler.publish_command_to_esp32(json.dumps(esp32_hand_pos_payload_dict))

            elif action == "pegar_seringa" or action == "soltar_seringa":
                print(f"[WS Handler] Comando de interação com seringa '{action}' recebido. Payload: {payload}")
                # Lógica para pegar/soltar seringa (pode interagir com SOFA ou apenas atualizar estado no backend)
                # Exemplo de interação com SOFA
                sofa_command_syringe = {"action": action, **payload}
                sofa_response_syringe = await sofa_bridge.send_command_to_sofa(sofa_command_syringe)
                print(f"[WS Handler] Resposta do SOFA Bridge para '{action}': {sofa_response_syringe}")
                await websocket.send_text(json.dumps({"source": "sofa_bridge", "action": action, "data": sofa_response_syringe}))

                # Notificar ESP32 sobre a ação com a seringa
                esp32_syringe_payload_dict = {"event": action, "details": payload}
                backend_mqtt_handler.publish_command_to_esp32(json.dumps(esp32_syringe_payload_dict))

            else:
                print(f"[WS Handler] Comando desconhecido ou não tratado: {action}")
                await websocket.send_text(json.dumps({"source": "backend", "status": "error", "message": f"Comando desconhecido: {action}"}))

    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
        print(f"Cliente WebSocket ({client_ip}) desconectado. Total: {len(connected_websockets)}")
    except Exception as e:
        print(f"[WS Handler] Erro no WebSocket ({client_ip}): {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
        # Tentar enviar uma mensagem de erro se a conexão ainda estiver aberta
        try:
            await websocket.send_text(json.dumps({"source": "backend", "status": "error", "message": "Erro interno no servidor."}))
        except Exception as send_error:
            print(f"[WS Handler] Não foi possível enviar mensagem de erro para o cliente ({client_ip}): {send_error}")
=======
# Placeholder imports for modules that might be used
# from . import sofa_bridge
# from . import mqtt_handler

def handle_websocket_message(message, websocket):
    """
    Processes messages received from a WebSocket client.

    Args:
        message (str): The message received from the client.
        websocket (any): Represents the WebSocket connection (actual type depends on library).
    """
    print(f"Received WebSocket message: {message}")

    # Example of how it might interact with other modules:
    # if "sofa_command" in message:
    #     response = sofa_bridge.send_command_to_sofa(message["sofa_command"])
    #     send_update_to_websocket(websocket, {"status": "SOFA command sent", "response": response})
    # elif "mqtt_command" in message:
    #     mqtt_handler.send_mqtt_command(message["mqtt_topic"], message["mqtt_command"])
    #     send_update_to_websocket(websocket, {"status": "MQTT command sent"})
    # else:
    #     send_update_to_websocket(websocket, {"error": "Unknown message type"})
    pass

def send_update_to_websocket(websocket, data):
    """
    Sends data back to a WebSocket client.

    Args:
        websocket (any): Represents the WebSocket connection.
        data (any): The data to send to the client.
    """
    print(f"Sending update to WebSocket: {data}")
    # In a real implementation, this would use the websocket object to send data, e.g.:
    # await websocket.send_json(data)
    pass

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    class MockWebSocket:
        def __init__(self, id):
            self.id = id
        def __str__(self):
            return f"MockWebSocket(id={self.id})"

    ws_client1 = MockWebSocket(1)
    ws_client2 = MockWebSocket(2)

    handle_websocket_message('{"action": "start_simulation"}', ws_client1)
    send_update_to_websocket(ws_client1, {"status": "simulation_started", "details": "..."})

    handle_websocket_message('{"command": "set_param", "param": "speed", "value": 5}', ws_client2)
    send_update_to_websocket(ws_client2, {"status": "parameter_updated", "param": "speed", "new_value": 5})
