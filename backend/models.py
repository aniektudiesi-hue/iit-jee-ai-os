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
    status = Column(String, default="PENDING") # PENDING, ACTIVE, COMPLETED, LOCKED, MISSED, STARTED
    is_mandatory = Column(Boolean, default=False)
    points_awarded = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True) # New: Timestamp when task was marked 'started'
    is_rest_block = Column(Boolean, default=False)
    is_free_time = Column(Boolean, default=False) # New: For rest, break, personal time

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    total_points = Column(Integer, default=0)
    sleep_hours = Column(Float, default=0.0)
    fatigue_level = Column(Integer, default=0) # 1-10
    discipline_score = Column(Float, default=0.0)
    focus_score = Column(Float, default=0.0)
    productivity_score = Column(Float, default=0.0) # New
    subject_weakness_index = Column(String, default="{}") # New: JSON string of weak subjects
    time_efficiency = Column(Float, default=0.0) # New
    sleep_compliance_score = Column(Float, default=0.0) # New
    focus_consistency_score = Column(Float, default=0.0) # New

class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, default=datetime.datetime.utcnow)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    missed_tasks = Column(Integer, default=0)
    locked_tasks = Column(Integer, default=0)
    total_study_minutes = Column(Integer, default=0)
    total_rest_minutes = Column(Integer, default=0)
    sleep_duration_minutes = Column(Integer, default=0)
    points_earned_today = Column(Integer, default=0)
