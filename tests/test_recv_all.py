import sys
import os
import socket
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pz_admin_tool import RCONClient


class FakeSockError:
    def recv(self, n):
        raise socket.error("simulated recv error")


def test_recv_all_partial():
    s1, s2 = socket.socketpair()
    try:
        client = RCONClient('127.0.0.1', 1234, 'pw')
        client.sock = s1

        data = b'hello_world'
        # send in two parts
        s2.sendall(data[:5])
        time.sleep(0.05)
        s2.sendall(data[5:])

        got = client._recv_all(len(data))
        if got != data:
            print('test_recv_all_partial: FAILED', got)
            return 2
        print('test_recv_all_partial: OK')
        return 0
    finally:
        s1.close(); s2.close()


def test_recv_all_peer_closed_returns_none():
    s1, s2 = socket.socketpair()
    try:
        client = RCONClient('127.0.0.1', 1234, 'pw')
        client.sock = s1

        # Close peer without sending
        s2.close()
        got = client._recv_all(10)
        if got is not None:
            print('test_recv_all_peer_closed_returns_none: FAILED', got)
            return 3
        print('test_recv_all_peer_closed_returns_none: OK')
        return 0
    finally:
        try:
            s1.close()
        except:
            pass


def test_recv_all_recv_raises_returns_none():
    client = RCONClient('127.0.0.1', 1234, 'pw')
    client.sock = FakeSockError()
    got = client._recv_all(5)
    if got is not None:
        print('test_recv_all_recv_raises_returns_none: FAILED', got)
        return 4
    print('test_recv_all_recv_raises_returns_none: OK')
    return 0


if __name__ == '__main__':
    codes = []
    codes.append(test_recv_all_partial())
    codes.append(test_recv_all_peer_closed_returns_none())
    codes.append(test_recv_all_recv_raises_returns_none())

    failed = [c for c in codes if c != 0]
    if failed:
        print('Some tests failed:', failed)
        raise SystemExit(1)
    print('All _recv_all tests passed')
    raise SystemExit(0)
