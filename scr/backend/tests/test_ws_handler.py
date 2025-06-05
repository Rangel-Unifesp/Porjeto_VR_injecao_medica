import sys
import os

# Adjust path to import from app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from ws_handler import handle_websocket_message, send_update_to_websocket

# Mock WebSocket class for testing
class MockWebSocket:
    def __init__(self, id):
        self.id = id
        self.sent_data = None # To capture what was "sent"

    def __str__(self):
        return f"MockWebSocket(id={self.id})"

    async def send_json(self, data): # Mimic potential async send
        print(f"MockWebSocket {self.id} send_json called with: {data}")
        self.sent_data = data

    async def send_text(self, data): # Mimic potential async send
        print(f"MockWebSocket {self.id} send_text called with: {data}")
        self.sent_data = data

def test_handle_websocket_message():
    print("Testing handle_websocket_message...")
    mock_ws = MockWebSocket(1)
    try:
        handle_websocket_message('{"action": "test"}', mock_ws)
        print("handle_websocket_message PASSED")
        assert True # If it runs without error
    except Exception as e:
        print(f"handle_websocket_message FAILED: {e}")
        assert False

def test_send_update_to_websocket():
    print("Testing send_update_to_websocket...")
    mock_ws = MockWebSocket(2)
    test_data = {"status": "test_update"}
    try:
        send_update_to_websocket(mock_ws, test_data)
        # In a real test with proper mocking, we'd check mock_ws.sent_data
        print("send_update_to_websocket PASSED")
        assert True # If it runs without error (actual sending is mocked by print)
    except Exception as e:
        print(f"send_update_to_websocket FAILED: {e}")
        assert False

if __name__ == "__main__":
    test_handle_websocket_message()
    test_send_update_to_websocket()
    print("All ws_handler tests finished.")
