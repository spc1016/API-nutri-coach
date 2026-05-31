import os
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['emails']
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

if __name__ == '__main__':
    conn = Redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        print("🚀 RQ Worker iniciado. Escuchando cola 'emails'...")
        worker.work()
