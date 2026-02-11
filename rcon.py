"""RCON client module extracted from the main UI file.
Provides `RCONClient` for communicating with Project Zomboid RCON.
"""
import socket
import struct
import logging

# Set up logger for RCON operations
logger = logging.getLogger(__name__)


class RCONClient:
    """RCON client for communicating with Project Zomboid server.
    
    Implements the RCON (Remote Console) protocol as used by Source engine and
    Project Zomboid. The protocol uses TCP sockets with a binary packet format.
    
    Packet Structure:
        All multi-byte integers are little-endian.
        - Size (4 bytes): total bytes in packet (id + type + body)
        - ID (4 bytes): request/response id for pairing
        - Type (4 bytes): command type (see constants below)
        - Body (0–N bytes): payload, must end with 2 null bytes
    
    Protocol Flow:
        1. Client connects to RCON port (default 16261)
        2. Client sends AUTH packet with password
        3. Server may send empty RESPONSE_VALUE before AUTH_RESPONSE
        4. Server sends AUTH_RESPONSE with id=-1 if failed, id>=0 if success
        5. Client sends EXECCOMMAND packets
        6. Server responds with RESPONSE_VALUE packets
        7. Client calls disconnect to close
    
    Critical Notes:
        - Packets always end with exactly 2 null bytes, not 1
        - SERVERDATA_EXECCOMMAND and SERVERDATA_AUTH_RESPONSE both use type value 2
        - Empty response packets (type 0) may appear during multi-packet sequences
    """
    
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0
    
    def __init__(self, host, port, password):
        """Initialize RCON client.
        
        Args:
            host (str): Server hostname or IP address
            port (int): RCON port (typically 16261)
            password (str): RCON password (not trimmed; spaces are intentional)
        """
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self.request_id = 0
        self.authenticated = False
        
    def connect(self):
        """Establish connection to RCON server and authenticate.
        
        Opens a TCP socket to the RCON server and performs authentication
        using the configured password. Handles the RCON handshake which may
        include an empty RESPONSE_VALUE packet before the authentication response.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            Exception: If connection fails, times out, or authentication is rejected
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((self.host, self.port))
            
            # Authenticate
            self.request_id += 1
            auth_id = self.request_id
            
            # CRITICAL: Body needs password + 2 null terminators (not 1!)
            auth_body = self.password.encode('utf-8')
            packet_data = auth_body + b'\x00\x00'  # Two null terminators
            packet_size = 4 + 4 + len(packet_data)  # id + type + data
            
            packet = struct.pack('<i', packet_size)   # size
            packet += struct.pack('<i', auth_id)      # id  
            packet += struct.pack('<i', self.SERVERDATA_AUTH)  # type
            packet += packet_data
            
            self.sock.sendall(packet)
            
            # Read first packet (might be empty SERVERDATA_RESPONSE_VALUE)
            size_data = self._recv_all(4)
            if not size_data:
                raise Exception("Auth failed - no response")
            
            response_size = struct.unpack('<i', size_data)[0]
            response_data = self._recv_all(response_size)
            
            if not response_data or len(response_data) < 8:
                raise Exception("Auth failed - incomplete response")
            
            first_packet_type = struct.unpack('<i', response_data[4:8])[0]
            
            # If first packet is empty response (type 0), read the auth response
            if first_packet_type == self.SERVERDATA_RESPONSE_VALUE:
                size_data = self._recv_all(4)
                if not size_data:
                    raise Exception("Auth failed - no auth response")
                
                response_size = struct.unpack('<i', size_data)[0]
                response_data = self._recv_all(response_size)
                
                if not response_data or len(response_data) < 4:
                    raise Exception("Auth failed - incomplete auth response")
            
            # Check auth result
            response_id = struct.unpack('<i', response_data[:4])[0]
            if response_id == -1:
                raise Exception("Authentication failed - wrong password")
            
            self.authenticated = True
            return True
            
        except socket.timeout:
            logger.error("RCON connection timed out to %s:%d", self.host, self.port)
            raise Exception("Connection timed out - check host and port")
        except ConnectionRefusedError:
            logger.error("RCON connection refused to %s:%d - is RCON enabled?", self.host, self.port)
            raise Exception("Connection refused - is RCON enabled and server running?")
        except Exception:
            if self.sock:
                try:
                    self.sock.close()
                except Exception as e:
                    logger.debug("Error closing socket during auth failure: %s", e)
                self.sock = None
            raise
    
    def disconnect(self):
        """Close RCON connection"""
        if self.sock:
            try:
                self.sock.close()
                logger.info("RCON disconnected from %s:%d", self.host, self.port)
            except (OSError, socket.error) as e:
                logger.debug("Error closing RCON socket: %s", e)
            self.sock = None
            self.authenticated = False
    
    def execute_command(self, command):
        """Execute a command on the server using existing connection.
        
        Sends an EXECCOMMAND packet and waits for the server's response.
        The command string is encoded as UTF-8 and padded with 2 null bytes
        per RCON protocol.
        
        Args:
            command (str): RCON command to execute (e.g. 'players', 'save')
            
        Returns:
            str: Command output (empty string if no response body)
            
        Raises:
            Exception: If not connected, socket errors, or timeouts occur
        """
        if not self.sock or not self.authenticated:
            raise Exception("Not connected to server")
        
        try:
            # Send command
            self.request_id += 1
            cmd_id = self.request_id
            
            # Build command packet with 2 null terminators
            cmd_body = command.encode('utf-8')
            packet_data = cmd_body + b'\x00\x00'
            packet_size = 4 + 4 + len(packet_data)
            
            packet = struct.pack('<i', packet_size)
            packet += struct.pack('<i', cmd_id)
            packet += struct.pack('<i', self.SERVERDATA_EXECCOMMAND)
            packet += packet_data
            
            self.sock.sendall(packet)
            
            # Read response
            response_text = ""
            
            size_data = self._recv_all(4)
            if size_data:
                response_size = struct.unpack('<i', size_data)[0]
                response_data = self._recv_all(response_size)
                
                if response_data and len(response_data) >= 8:
                    response_text = response_data[8:].rstrip(b'\x00').decode('utf-8', errors='ignore')
            
            return response_text
            
        except (BrokenPipeError, ConnectionResetError):
            logger.error("RCON connection lost while executing command")
            self.authenticated = False
            raise Exception("Connection lost - please reconnect")
        except socket.timeout:
            logger.error("RCON command timed out")
            raise Exception("Command timed out")
        except Exception as e:
            logger.error("RCON command failed: %s", e)
            raise Exception(f"Command failed: {str(e)}")
    
    def _recv_all(self, n):
        """Receive exactly n bytes from socket.
        
        Handles partial reads and EOF. Retries receiving data until
        exactly n bytes are accumulated or an error occurs.
        
        Args:
            n (int): number of bytes to receive
            
        Returns:
            bytes: Exactly n bytes, or None if peer closes or socket error
        """
        data = b''
        while len(data) < n:
            try:
                chunk = self.sock.recv(n - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.error:
                return None
        return data
