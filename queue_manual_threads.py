import redis
import json
import os

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
r = redis.from_url(REDIS_URL)

threads = [{"board": "b", "thread_id": 944488457, "subject": "Manual Image Download"}]

for t in threads:
    r.rpush('queue:monitors', json.dumps(t))
    print(f"Queued {t['thread_id']}")
