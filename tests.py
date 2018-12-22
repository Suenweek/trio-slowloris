from multiprocessing import Process
from functools import partial
from socketserver import ForkingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytest
import trio

from slowloris import slowloris


# Let's just hope the port is available...
PORT = 32123
POOL_SIZE = 4

ForkingHTTPServer = type('ForkingHTTPServer', (ForkingMixIn, HTTPServer), {})
ForkingHTTPServer.max_children = POOL_SIZE


def _serve():
    with ForkingHTTPServer(('', PORT), BaseHTTPRequestHandler) as server:
        server.serve_forever()


@pytest.fixture(name='server')
def fixture_server():
    p = Process(target=_serve)
    p.start()
    yield
    p.terminate()


async def test_slowloris(server, nursery):
    nursery.start_soon(partial(
        slowloris,
        host='localhost',
        port=PORT,
        interval=10,
        cons=POOL_SIZE
    ))

    await trio.sleep(5)

    stream = await trio.open_tcp_stream('localhost', PORT)
    async with stream:
        await stream.send_all(b'GET / HTTP/1.1\r\n\r\n')
        with trio.move_on_after(5):
            await stream.receive_some(1)
            pytest.fail('Unreachable')
