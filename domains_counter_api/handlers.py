import json
import time
from jsonschema import validate

from aiohttp import web
from tldextract import tldextract

json_schema = {
    "type": "object",
    "properties": {
        "links": {
            "type": "array",
            "items": {
                "type": "string"
            },
        },
    },
}


class Handlers:
    def __init__(self, loop, dbi):
        self.loop = loop
        self.dbi = dbi

    async def add_links(self, request):
        '''
        Хэндлер сохранения в базе переданного списка доменов и времени
        обращения к ним.
        Ожидаем список доменов в теле запроса в json словаре вида:
            {
              'links': [
                'https://ya.ru',
                'https://ya.ru?q=123',
                'funbox.ru',
                'https://stackoverflow.com/questions/11828270/how-to-exit-the-
                 vim-editor'
              ]
            }
        В базе храним ТОЛЬКО домены, а не полные ссылки. Разные ссылки с
        одинаковыми доменами, считаем один раз. Для уже имеющихся в базе
        доменов обновим время обращения к ним.
        Временем обращания к домену считаем время получения запроса сервисом.

        :return:
            {'status': 'ok'} - при получении корректной структуры данных, иначе
            400 BadRequest
        '''
        raw_body = await request.text()
        try:
            body = json.loads(raw_body)
            validate(body, json_schema)
        except (TypeError, Exception) as e:
            return web.json_response(
                status=web.HTTPBadRequest.status_code,
                data={'status': f'BadRequest ({e})'}
            )

        links = body.get('links')

        domains = set([
            tldextract.extract(link).registered_domain for link in links
        ])
        timestamp = int(time.time())
        self.loop.create_task(self.dbi.add_domains(domains, timestamp))

        return web.json_response({
            'status': 'ok',
        })

    async def get_visited_domain(self, request):
        '''
        Хэндлер получения списка уникальных посещенных доменов за переданный
        интервал времени.
        Границы интересующего интервала (в секундах от начала эпохи Unix)
        ожидаем в виде query параметров запроса `from` -- начало и
        `to` -- конец интервала.

        :return:
            `json` со списком уникальных доменов вида:
                {
                  'status': 'ok',
                  'domains': [
                    'funbox.ru',
                    'stackoverflow.com'
                  ]
                }
        '''
        try:
            req_from = int(request.query.get('from'))
            req_to = int(request.query.get('to'))
        except ValueError as e:
            return web.json_response(
                status=web.HTTPBadRequest.status_code,
                data={'status': f'BadRequest ({e})'}
            )

        domains = await self.dbi.get_domains_by_scores(req_from, req_to)
        return web.json_response({
            'status': 'ok',
            'domains': domains
        })
