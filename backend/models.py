from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    subject = Column(String)
    difficulty = Column(Integer) # 1-5
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Integer) # in minutes
    status = Column(String, default="PENDING") # PENDING, ACTIVE, COMPLETED, LOCKED, MISSED
    is_mandatory = Column(Boolean, default=False)
    points_awarded = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    is_rest_block = Column(Boolean, default=False)

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    total_points = Column(Integer, default=0)
    sleep_hours = Column(Float, default=0.0)
    fatigue_level = Column(Integer, default=0) # 1-10
    discipline_score = Column(Float, default=0.0)
    focus_score = Column(Float, default=0.0)
