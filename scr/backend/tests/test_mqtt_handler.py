import sys
import os

# Adjust path to import from app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from mqtt_handler import handle_mqtt_message, send_mqtt_command

def test_handle_mqtt_message():
    print("Testing handle_mqtt_message...")
    try:
        handle_mqtt_message("test/topic", '{"data": "test_payload"}')
        print("handle_mqtt_message PASSED")
        assert True # If it runs without error
    except Exception as e:
        print(f"handle_mqtt_message FAILED: {e}")
        assert False

def test_send_mqtt_command():
    print("Testing send_mqtt_command...")
    try:
        send_mqtt_command("test/command_topic", '{"command": "test_command"}')
        print("send_mqtt_command PASSED")
        assert True # If it runs without error
    except Exception as e:
        print(f"send_mqtt_command FAILED: {e}")
        assert False

if __name__ == "__main__":
    test_handle_mqtt_message()
    test_send_mqtt_command()
    print("All mqtt_handler tests finished.")
