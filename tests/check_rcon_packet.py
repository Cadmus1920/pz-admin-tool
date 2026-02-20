import sys
import os
import sys
import os
import socket
import struct
import time

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pz_admin_tool import RCONClient


def test_execute_command_packet():
    # Create a socketpair (Unix domain) for local testing
    s1, s2 = socket.socketpair()
    try:
        client = RCONClient('127.0.0.1', 12345, 'pass')
        client.sock = s1
        client.authenticated = True
        client.request_id = 42

        # Monkeypatch _recv_all to avoid waiting for a response
        client._recv_all = lambda n: None

        # Call execute_command which will send a packet
        cmd = 'test_command'
        _ = client.execute_command(cmd)

        # Read bytes from the other end
        s2.settimeout(1.0)
        data = b''
        try:
            # Read whatever was sent (should be single write)
            data = s2.recv(4096)
        except socket.timeout:
            assert False, 'No data received from client socket'

        assert len(data) >= 12, f'Packet too small: {len(data)}'

        # Parse
        size = struct.unpack('<i', data[0:4])[0]
        rid = struct.unpack('<i', data[4:8])[0]
        ptype = struct.unpack('<i', data[8:12])[0]
        payload = data[12:]

        expected_payload = cmd.encode('utf-8') + b"\x00\x00"
        expected_size = 4 + 4 + len(expected_payload)

        assert size == expected_size, f'size mismatch: {size} != {expected_size}'
        assert rid == 43, f'request id mismatch: {rid} != 43'
        assert ptype == RCONClient.SERVERDATA_EXECCOMMAND, f'type mismatch: {ptype}'
        assert payload == expected_payload, f'payload mismatch: {repr(payload)}'
    finally:
        try:
            s1.close()
        except:
            pass
        try:
            s2.close()
        except:
            pass
