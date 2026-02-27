from celery import Celery
from database import SessionLocal
from scraper import process_thread
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("kuroba_worker", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def update_thread(board: str, thread_id: int):
    db = SessionLocal()
    try:
        print(f"Worker: Updating /{board}/{thread_id}")
        process_thread(db, board, thread_id)
    finally:
        db.close()
