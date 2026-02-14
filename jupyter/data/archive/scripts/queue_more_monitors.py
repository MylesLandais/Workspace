import redis, json

r = redis.from_url('redis://localhost:6381')

threads = [
    {'board': 'b', 'thread_id': 944408571, 'subject': 'v2'},
    {'board': 'b', 'thread_id': 944405258, 'subject': '4.0'},
]

for t in threads:
    r.rpush('queue:monitors', json.dumps(t))
    print(f"Queued: {t['board']}/{t['thread_id']} - {t['subject']}")

print(f"\nQueue length: {r.llen('queue:monitors')}")
