import os
from redis import Redis
from rq import Worker, Queue

from app.core.config import get_settings
from app.core.logging import setup_logging


def main() -> None:
    setup_logging()
    settings = get_settings()

    # Connexion Redis à partir de REDIS_URL
    redis_conn = Redis.from_url(settings.REDIS_URL)

    # Déclare les queues à écouter
    queues = [Queue("url_scan", connection=redis_conn)]

    # Crée le worker avec la connexion explicite
    worker = Worker(queues, connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
