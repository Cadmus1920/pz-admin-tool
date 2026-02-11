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
        resp = client.execute_command(cmd)

        # Read bytes from the other end
        s2.settimeout(1.0)
        data = b''
        try:
            # Read whatever was sent (should be single write)
            data = s2.recv(4096)
        except socket.timeout:
            print('No data received from client socket')
            return 1

        if len(data) < 12:
            print('Packet too small:', len(data))
            return 2

        # Parse
        size = struct.unpack('<i', data[0:4])[0]
        rid = struct.unpack('<i', data[4:8])[0]
        ptype = struct.unpack('<i', data[8:12])[0]
        payload = data[12:]

        expected_payload = cmd.encode('utf-8') + b"\x00\x00"
        expected_size = 4 + 4 + len(expected_payload)

        print('size field:', size)
        print('expected size:', expected_size)
        print('request id:', rid)
        print('expected id:', 43)  # request_id was 42 then incremented
        print('type:', ptype)
        print('payload repr:', repr(payload))

        # Checks
        ok = True
        if size != expected_size:
            print('SIZE MISMATCH')
            ok = False
        if rid != 43:
            print('REQUEST ID MISMATCH')
            ok = False
        if ptype != RCONClient.SERVERDATA_EXECCOMMAND:
            print('TYPE MISMATCH')
            ok = False
        if payload != expected_payload:
            print('PAYLOAD MISMATCH')
            ok = False

        print('TEST OK' if ok else 'TEST FAILED')
        return 0 if ok else 3
    finally:
        try:
            s1.close()
        except:
            pass
        try:
            s2.close()
        except:
            pass


if __name__ == '__main__':
    exit_code = test_execute_command_packet()
    if exit_code == 0:
        print('RCON packet construction test passed')
    else:
        print('RCON packet construction test failed with code', exit_code)
    raise SystemExit(exit_code)
