import asyncio

import pytest

from domains_counter_api.server import DomainsCounter

pytest_plugins = 'aiohttp.pytest_plugin'


@pytest.fixture
def config(aiohttp_unused_port):
    return {
        "server": {
            "host": "127.0.0.1",
            "port": aiohttp_unused_port()
        },
        "redis": {
            "uri": "redis://localhost/0"
        }
    }


@pytest.fixture
async def server(config, loop):
    server = DomainsCounter(loop, config)

    # Это нужно чтобы таска поднятия коннекта к базе точно завершилась
    await asyncio.sleep(0.1)
    return server


@pytest.fixture
async def dbi(server):
    return server.dbi


@pytest.fixture
async def app(server, dbi):
    await dbi.pool.flushall()
    yield server.web_app

    await dbi.pool.flushall()
    await server._cleanup()
