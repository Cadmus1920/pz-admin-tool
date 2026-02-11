import sys
import os
import socket
import struct
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rcon import RCONClient


class MockRCONServer:
    """Simple mock RCON server for testing the RCONClient."""
    
    def __init__(self, port=9999, password='testpass'):
        self.port = port
        self.password = password
        self.sock = None
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the mock server in a background thread."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('127.0.0.1', self.port))
        self.sock.listen(1)
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.1)  # Give server time to start
        
    def stop(self):
        """Stop the mock server."""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.thread:
            self.thread.join(timeout=1)
    
    def _run(self):
        """Server loop."""
        while self.running:
            try:
                client, addr = self.sock.accept()
                self._handle_client(client)
            except Exception:
                break
    
    def _handle_client(self, client):
        """Handle a single client connection."""
        try:
            authenticated = False
            
            while self.running:
                # Read size
                size_data = client.recv(4)
                if not size_data:
                    break
                    
                size = struct.unpack('<i', size_data)[0]
                data = client.recv(size)
                
                if len(data) < 8:
                    continue
                
                req_id = struct.unpack('<i', data[0:4])[0]
                pkt_type = struct.unpack('<i', data[4:8])[0]
                body = data[8:].rstrip(b'\x00')
                
                # Handle AUTH (type 3)
                if pkt_type == 3:
                    password = body.decode('utf-8', errors='ignore')
                    
                    # Send empty RESPONSE_VALUE acknowledgment (id=0, type=0)
                    resp = struct.pack('<i', 10)  # size = 10 (id + type + 2 nulls)
                    resp += struct.pack('<i', 0)  # id
                    resp += struct.pack('<i', 0)  # type = RESPONSE_VALUE
                    resp += b'\x00\x00'
                    client.sendall(resp)
                    
                    if password == self.password:
                        authenticated = True
                        # Send AUTH response with matching id (success)
                        resp = struct.pack('<i', 10)  # size = 10
                        resp += struct.pack('<i', req_id)  # id = request id (auth success)
                        resp += struct.pack('<i', 0)  # type = RESPONSE_VALUE
                        resp += b'\x00\x00'
                        client.sendall(resp)
                    else:
                        # Send failure response (id = -1)
                        resp = struct.pack('<i', 10)  # size = 10
                        resp += struct.pack('<i', -1)  # id = -1 (auth failed)
                        resp += struct.pack('<i', 0)  # type = RESPONSE_VALUE
                        resp += b'\x00\x00'
                        client.sendall(resp)
                        break
                
                # Handle EXECCOMMAND (type 2)
                elif pkt_type == 2 and authenticated:
                    command = body.decode('utf-8', errors='ignore')
                    response = self._handle_command(command)
                    
                    # Send response with proper packet format
                    # Data is: id + type + body
                    resp_body = response.encode('utf-8')
                    packet_data = struct.pack('<i', req_id)
                    packet_data += struct.pack('<i', 0)  # RESPONSE_VALUE type
                    packet_data += resp_body + b'\x00\x00'
                    
                    # Packet is: size + data
                    packet = struct.pack('<i', len(packet_data))
                    packet += packet_data
                    client.sendall(packet)
        except Exception as e:
            import traceback
            print(f"Server error: {e}")
            print(traceback.format_exc())
        finally:
            try:
                client.close()
            except:
                pass
    
    def _handle_command(self, command):
        """Simulate handling a command."""
        if command == 'test':
            return 'test response'
        elif command == 'players':
            return 'Players connected (1):\nTestPlayer'
        else:
            return f'Unknown command: {command}'


def test_rcon_connect_and_auth():
    """Test RCON connection and authentication."""
    server = MockRCONServer(port=19999)
    server.start()
    time.sleep(0.2)
    
    try:
        client = RCONClient('127.0.0.1', 19999, 'testpass')
        client.connect()
        assert client.authenticated
        assert client.sock is not None
        print('test_rcon_connect_and_auth: OK')
        client.disconnect()
        return 0
    except Exception as e:
        print(f'test_rcon_connect_and_auth: FAILED - {e}')
        import traceback
        print(traceback.format_exc())
        return 1
    finally:
        server.stop()
        time.sleep(0.2)


def test_rcon_wrong_password():
    """Test RCON authentication failure."""
    server = MockRCONServer(port=19998)
    server.start()
    time.sleep(0.2)
    
    try:
        client = RCONClient('127.0.0.1', 19998, 'wrongpass')
        try:
            client.connect()
            print('test_rcon_wrong_password: FAILED - should have raised exception')
            return 1
        except Exception as e:
            if 'Authentication failed' in str(e):
                print('test_rcon_wrong_password: OK')
                return 0
            else:
                print(f'test_rcon_wrong_password: FAILED - wrong error: {e}')
                return 1
    finally:
        server.stop()
        time.sleep(0.2)


def test_rcon_execute_command():
    """Test command execution."""
    server = MockRCONServer(port=19997)
    server.start()
    time.sleep(0.2)
    
    try:
        client = RCONClient('127.0.0.1', 19997, 'testpass')
        client.connect()
        
        response = client.execute_command('test')
        assert 'test response' in response, f"Expected 'test response' in '{response}'"
        
        print('test_rcon_execute_command: OK')
        client.disconnect()
        return 0
    except Exception as e:
        import traceback
        print(f'test_rcon_execute_command: FAILED')
        print(traceback.format_exc())
        return 1
    finally:
        server.stop()
        time.sleep(0.2)


if __name__ == '__main__':
    codes = []
    codes.append(test_rcon_connect_and_auth())
    codes.append(test_rcon_wrong_password())
    codes.append(test_rcon_execute_command())
    
    failed = [c for c in codes if c != 0]
    if failed:
        print(f'Integration tests: {len(failed)} failed')
        raise SystemExit(1)
    print('All integration tests passed')
    raise SystemExit(0)
