# scr/backend/app/sofa_bridge.py

async def send_command_to_sofa(command: dict):
    # Simulação: Imprime o comando que seria enviado ao SOFA
    print(f"[SOFA Bridge] Comando recebido para SOFA: {command}")
    # No futuro, aqui ocorreria a comunicação real com o SOFA (e.g., via socket, RPC)
    # Por enquanto, vamos simular uma resposta de força.
    if command.get("action") == "injetar":
        return {"status": "success", "force_feedback": 0.5} # Exemplo de feedback de força
    return {"status": "success", "message": "Comando processado (simulado)"}

async def get_simulation_data():
    # Simulação: Retorna dados mockados da simulação
    print("[SOFA Bridge] Buscando dados da simulação (simulado)")
    return {"tissue_density": "medium", "needle_depth": 0}
