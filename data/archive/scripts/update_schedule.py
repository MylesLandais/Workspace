import os
from src.feed.scheduler.celery_app import app
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab

def update_schedule():
    """Register the imageboard coordinator task to run every 5 minutes."""
    task_name = "src.feed.scheduler.imageboard_tasks.coordinator_task"
    entry_name = "imageboard-coordinator-every-5min"
    
    # Define schedule: Every 5 minutes (300 seconds)
    schedule = 300
    
    # Ensure we use the correct Redis URL for RedBeat
    # In docker, 'valkey' is the hostname. Locally it might be 'localhost'.
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    app.conf.redbeat_redis_url = redis_url
    
    entry = RedBeatSchedulerEntry(
        entry_name,
        task_name,
        schedule,
        app=app
    )
    
    print(f"Registering task: {entry_name}")
    print(f"Task: {task_name}")
    print(f"Schedule: {schedule} seconds")
    print(f"Redis: {redis_url}")
    
    try:
        entry.save()
        print("Successfully registered schedule in RedBeat/Redis.")
    except Exception as e:
        print(f"Error registering schedule: {e}")
        print("Ensure Redis is running and accessible.")

if __name__ == "__main__":
    update_schedule()
