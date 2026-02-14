from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database import engine, Base, get_db
from models import Thread, Post
from worker import update_thread, celery_app

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kuroba Web BFF")

# Mount static images
# These are the images downloaded by the worker
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Pydantic Schemas
class ThreadRequest(BaseModel):
    board: str
    thread_id: int

class PostResponse(BaseModel):
    post_no: int
    comment: Optional[str] = None
    subject: Optional[str] = None
    local_image_filename: Optional[str] = None
    created_at: str

    class Config:
        orm_mode = True

class ThreadResponse(BaseModel):
    id: int
    board: str
    thread_id: int
    title: Optional[str]
    post_count: int
    posts: List[PostResponse] = []

    class Config:
        orm_mode = True

@app.post("/api/track")
def track_thread(req: ThreadRequest, db: Session = Depends(get_db)):
    # Trigger background job
    update_thread.delay(req.board, req.thread_id)
    return {"status": "queued", "message": f"Tracking /{req.board}/{req.thread_id}"}

@app.get("/api/threads", response_model=List[ThreadResponse])
def list_threads(db: Session = Depends(get_db)):
    # Return threads without posts for the list view
    threads = db.query(Thread).order_by(Thread.last_modified.desc()).all()
    return threads

@app.get("/api/thread/{board}/{thread_id}", response_model=ThreadResponse)
def get_thread(board: str, thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(Thread).filter(Thread.board == board, Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
