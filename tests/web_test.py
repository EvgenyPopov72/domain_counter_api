import json
import time

import pytest


async def test_add_links(aiohttp_client, app, monkeypatch):
    client = await aiohttp_client(app)

    # 'Вернемся' в начало 70-х прошлого века
    monkeypatch.setattr(time, 'time', lambda: 0)

    data = {
        'links': [
            'https://ya.ru',
            'https://ya.ru?q=123',
            'funbox.ru',
            'https://stackoverflow.com/questions/11828270/how-to-exit-the-vim'
            '-editor',
            'https://funbox.ru/q/python.pdf',
        ]
    }

    # Сохраним первый набор ссылок
    response = await client.post('/visited_links', data=json.dumps(data))
    now = int(time.time())
    assert response.status == 200

    content = await response.json()
    assert content == {'status': 'ok'}

    # 'Перенесемся' на 10 секунд вперед
    monkeypatch.setattr(time, 'time', lambda: 10)

    data_after_now = {
        'links': [
            'https://habr.com/',
            'https://google.com?q=123',
            'https://funbox.ru/q/elixir.pdf',
        ]
    }

    # Сохраним второй набор ссылок
    response = await client.post('/visited_links',
                                 data=json.dumps(data_after_now))
    after_now = int(time.time())

    assert now != after_now
    assert response.status == 200

    content = await response.json()
    assert content == {'status': 'ok'}

    # Получим первый набор ссылок
    response = await client.get('/visited_domains',
                                params={'from': 0, 'to': now})
    assert response.status == 200

    content = await response.json()
    assert content == {
        'status': 'ok',
        'domains': [
            'stackoverflow.com',
            'ya.ru'
        ]
    }

    # Получим второй набор ссылок
    response = await client.get('/visited_domains',
                                params={'from': now + 1, 'to': after_now})
    assert response.status == 200

    content = await response.json()
    assert content == {
        'status': 'ok',
        'domains': [
            'funbox.ru',
            'google.com',
            'habr.com',
        ]
    }

    # Получим все ссылки
    response = await client.get('/visited_domains',
                                params={'from': 0, 'to': after_now})
    assert response.status == 200

    content = await response.json()
    assert content == {
        'status': 'ok',
        'domains': [
            'stackoverflow.com',
            'ya.ru',
            'funbox.ru',
            'google.com',
            'habr.com',
        ]
    }


@pytest.mark.parametrize(
    'data', ('123фвв', 'asd', '{"links": [1, 3, 4]}')
)
async def test_add_links_invalid_params(aiohttp_client, app, data):
    client = await aiohttp_client(app)
    response = await client.post('/visited_links', data=data)
    assert response.status == 400


@pytest.mark.parametrize(
    'params', ('123фвв', 'asd')
)
async def test_visited_domains_invalid_params(aiohttp_client, app, params):
    client = await aiohttp_client(app)
    response = await client.get('/visited_domains',
                                params={'from': params, 'to': params})
    assert response.status == 400
