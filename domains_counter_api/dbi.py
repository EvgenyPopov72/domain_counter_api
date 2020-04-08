import logging

import aioredis
from aioredis import RedisError

logger = logging.getLogger('domains_counter.dbi')


class Interface:
    DOMAIN_KEY = 'domains'

    def __init__(self, **params):
        self.uri = params.get('uri', 'redis://localhost/0')
        self.pool = None

    async def connect(self):
        '''
        Подключение к базе.
        '''
        try:
            self.pool = await aioredis.create_redis_pool(self.uri)
            logger.debug('Connected to redis.')
            return True
        except (Exception) as e:
            logger.error('Error occurred while connecting to redis: %s', e)

    async def add_domains(self, domains, timestamp):
        '''
        Сохраним список доменов в базе. В качестве контейнера будем
        использовать отсортированное множество (SortedSet). В качестве ключа
        сортировки (score) используем timestamp (количество секунд от начала
        эпохи Unix).
        При добавлении уже существующих доменов в базе обновляется их score
        параметр.

        :param domains:
            `list` -- список имен доменов для сохранения в базу;
        :param timestamp:
            `int` -- количество секунд от начала эпохи Unix;
        '''
        args = []
        if isinstance(domains, (list, tuple, set)):
            for d in domains:
                args.extend((timestamp, d))
        else:
            args = [timestamp, domains]

        try:
            result = await self.pool.execute(b'ZADD', self.DOMAIN_KEY, *args)
            logger.debug('Added %s domains', result)
        except (TypeError, RedisError) as e:
            logger.error('Error occurred while adding domains: %s', e)

    async def get_domains_by_scores(self, min_score, max_score):
        '''
        Получим список доменов с рейтингом (score) из диапазона [min_score,
        max_score] включительно.

        :param min_score:
            `int` -- начало диапазона;
        :param max_score:
            `int` -- конец диапазона;
        :return:
            `list` -- список доменов;
        '''
        try:
            return await self.pool.zrangebyscore(
                self.DOMAIN_KEY, min_score, max_score, encoding='utf-8'
            )
        except (TypeError, RedisError) as e:
            logger.error('Error occurred while getting domains: %s', e)

    async def cleanup(self):
        '''
        Закроем все коннекты к redis.
        '''
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.debug('Redis connection closed.')
