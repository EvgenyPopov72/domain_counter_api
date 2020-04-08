import pytest


@pytest.mark.parametrize('timestamp', (1, 999))
@pytest.mark.parametrize(
    'domains', (
            ('ya.ru', 'python.org'),
            ('funbox.ru', 'google.com')
    )
)
async def test_add_domains(dbi, timestamp, domains):
    await dbi.add_domains(domains, timestamp)

    result = await dbi.pool.zrangebyscore(
        dbi.DOMAIN_KEY, withscores=True, encoding='utf-8'
    )
    expected = [(d, timestamp) for d in domains]
    assert result, expected


@pytest.mark.parametrize(
    'domains', (
            ('ya.ru', 'python.org'),
            ('funbox.ru', 'google.com')
    )
)
async def test_get_domains_by_scores(dbi, domains):
    timestamp1 = 1
    timestamp2 = 99
    extra_domain = 'https://hexdocs.pm'
    args = []
    # Добавим домены с таймстемпом в список аргументов
    for d in domains:
        args.extend((timestamp1, d))
    # Добавим еще один домен с другим таймстемпом
    args.extend((timestamp2, extra_domain))

    await dbi.pool.execute(b'ZADD', dbi.DOMAIN_KEY, *args)

    result = await dbi.get_domains_by_scores(min_score=0, max_score=timestamp1)
    assert result, domains

    result = await dbi.get_domains_by_scores(
        min_score=timestamp1 + 1, max_score=timestamp2
    )
    assert result, extra_domain

    result = await dbi.get_domains_by_scores(min_score=0, max_score=timestamp2)
    assert result, domains + extra_domain
