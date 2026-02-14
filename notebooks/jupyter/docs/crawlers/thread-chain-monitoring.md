# Thread Chain Monitoring

## Active Thread Chain

Monitoring the following thread chain on /b/:

### Thread Relationships

```
944305638 (Archived)
    ↓
944308851 (Active)
    ↓
944311751 (Active)
```

### Monitored Threads

1. **944311751** - "IRL Big ass & hips"
   - Status: Active
   - Monitor: Running in `jupyter.dev.local`

2. **944308851** - Previous thread
   - Status: Active
   - Monitor: Running in `jupyter.dev.local`

3. **944310047** - Additional thread
   - Status: Active
   - Monitor: Running in `jupyter.dev.local`

4. **944297214** - "First Feet Thread of 2026"
   - Status: Active
   - Monitor: Running in `jupyter.dev.local`

5. **944305638** - "Girls you jerk to"
   - Status: Archived (404)
   - Note: Linked from 944308851

## Automatic Thread Following

The monitor automatically:
- Detects linked threads in posts
- Starts monitoring new continuation threads
- Tracks thread relationships in Neo4j graph

## Check Status

```bash
# View all running monitors
docker exec jupyter ps aux | grep monitor_imageboard

# Check specific thread logs
docker exec jupyter tail -f /tmp/imageboard_monitor_944154000.log
docker exec jupyter tail -f /tmp/imageboard_monitor_944156718.log
docker exec jupyter tail -f /tmp/imageboard_monitor_944152051.log

# Query thread relationships in Neo4j
docker exec jupyter python -c "
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
query = '''
MATCH (t1:Thread)-[r:CONTINUES_TO]->(t2:Thread)
WHERE t1.board = 'b' AND t2.board = 'b'
RETURN t1.thread_id as from_thread, t2.thread_id as to_thread
ORDER BY t1.thread_id
'''
result = neo4j.execute_read(query)
for r in result:
    print(f'/b/{r[\"from_thread\"]} -> /b/{r[\"to_thread\"]}')
"
```

## Images Organization

Images from these threads are organized at:
- `cache/imageboard/images/b/944154000/`
- `cache/imageboard/images/b/944156718/`
- `cache/imageboard/images/b/944152051/`
- `cache/imageboard/images/b/944158692/` (when created)



