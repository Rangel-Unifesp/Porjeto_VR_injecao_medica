import sys
import os

# Adjust path to import from app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from sofa_bridge import send_command_to_sofa, get_data_from_sofa

def test_send_command_to_sofa():
    print("Testing send_command_to_sofa...")
    try:
        send_command_to_sofa("TEST_SOFA_COMMAND")
        print("send_command_to_sofa PASSED")
        assert True # If it runs without error
    except Exception as e:
        print(f"send_command_to_sofa FAILED: {e}")
        assert False

def test_get_data_from_sofa():
    print("Testing get_data_from_sofa...")
    try:
        data = get_data_from_sofa()
        print(f"get_data_from_sofa returned: {data}")
        assert isinstance(data, dict) # Check if it returns a dictionary as expected
        print("get_data_from_sofa PASSED")
    except Exception as e:
        print(f"get_data_from_sofa FAILED: {e}")
        assert False

if __name__ == "__main__":
    test_send_command_to_sofa()
    test_get_data_from_sofa()
    print("All sofa_bridge tests finished.")
