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
=======
def send_command_to_sofa(command):
    """
    Sends a command to the SOFA simulation.

    Args:
        command (str): The command to send to SOFA.
    """
    print(f"Sending command to SOFA: {command}")
    # In the future, this function will interact with the SOFA simulation instance.
    pass

def get_data_from_sofa():
    """
    Retrieves data from the SOFA simulation.

    Returns:
        dict: Placeholder data from SOFA.
    """
    print("Getting data from SOFA...")
    # In the future, this function will retrieve actual data from the SOFA simulation.
    return {"status": "simulating", "value": 42}

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    send_command_to_sofa("START_SIMULATION")
    data = get_data_from_sofa()
    print(f"Received data from SOFA: {data}")