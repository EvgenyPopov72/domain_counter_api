import asyncio
import logging
import logging.config

import toml
from aiohttp import web

from domains_counter_api import dbi
from domains_counter_api.handlers import Handlers

logger = logging.getLogger('domains_counter')


class DomainsCounter:
    """Приложение -- API для хранения доменов и времени обращения к ним."""

    def __init__(self, loop, config):
        self.loop = loop
        self.server_params = config['server']
        self.server_params.setdefault('host', 'localhost')
        self.server_params.setdefault('port', '8000')

        self.database_params = config['redis']
        self.dbi = dbi.Interface(**self.database_params)

        self.web_app = web.Application()
        handlers = Handlers(self.loop, self.dbi)
        self.web_app.add_routes([
            web.post('/visited_links', handlers.add_links),
            web.get('/visited_domains', handlers.get_visited_domain),
        ])
        self.web_app_runner = web.AppRunner(self.web_app)

        loop.create_task(self.setup())

    async def setup(self):
        '''
        Подключимся к базе и запустим веб-сервер.
        :return:
        '''
        if not await self.dbi.connect():
            return

        await self.web_app_runner.setup()
        await web.TCPSite(self.web_app_runner, **self.server_params).start()
        logger.debug('Server started')

    async def _cleanup(self):
        """Подчистим все открытые коннекты."""

        logger.debug('Server stopping..')
        await self.dbi.cleanup()
        await self.web_app_runner.cleanup()

    def stop(self):
        """Начнем процесс остановки всего."""

        self.loop.run_until_complete(self._cleanup())


def load_config(filename):
    """
    Загрузим конфигурацию из toml файла.
    :param filename:
        `str`, имя файла с конфигурацией
    :return:
        'dict', словарь с конфигурацией
    """

    return toml.load(filename)


def main():
    logger.debug('Starting..')
    config = load_config('config/config.toml')

    logging.config.dictConfig(config['logging'])

    loop = asyncio.get_event_loop()
    app = DomainsCounter(loop, config)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        app.stop()
        loop.close()

    logger.debug('Server stopped.')


if __name__ == '__main__':
    main()
