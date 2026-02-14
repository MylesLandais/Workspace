from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    board = Column(String, index=True)
    thread_id = Column(Integer, index=True) # The 4chan thread ID
    title = Column(String, nullable=True)
    last_modified = Column(DateTime, default=datetime.utcnow)
    post_count = Column(Integer, default=0)
    
    posts = relationship("Post", back_populates="thread", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    thread_db_id = Column(Integer, ForeignKey("threads.id"))
    post_no = Column(Integer)
    subject = Column(String, nullable=True)
    comment = Column(Text, nullable=True) # The HTML content
    
    # Image handling
    original_image_url = Column(String, nullable=True)
    local_image_filename = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    thread = relationship("Thread", back_populates="posts")
