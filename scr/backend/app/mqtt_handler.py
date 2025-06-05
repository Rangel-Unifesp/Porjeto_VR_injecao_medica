def handle_mqtt_message(topic, payload):
    """
    Handles incoming MQTT messages.

    Args:
        topic (str): The MQTT topic of the message.
        payload (str): The payload of the message.
    """
    print(f"Received MQTT message on topic '{topic}': {payload}")
    # In the future, add logic here to parse the message and
    # interact with the simulation or other backend components.
    pass

def send_mqtt_command(topic, command):
    """
    Sends a command to an MQTT topic.

    Args:
        topic (str): The MQTT topic to send the command to.
        command (str): The command to send.
    """
    print(f"Sending MQTT command to topic '{topic}': {command}")
    # In the future, add logic here to actually publish the message
    # to an MQTT broker.
    pass

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    handle_mqtt_message("simulation/control", '{"action": "start"}')
    send_mqtt_command("simulation/parameters", '{"speed": "high"}')
