from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TaskBase(BaseModel):
    title: str
    subject: str
    difficulty: int
    start_time: datetime
    end_time: datetime
    duration: int
    is_mandatory: bool = False
    is_rest_block: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    points_awarded: Optional[int] = None
    completed_at: Optional[datetime] = None

class Task(TaskBase):
    id: int
    status: str
    points_awarded: int
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserStatsBase(BaseModel):
    date: datetime
    total_points: int
    sleep_hours: float
    fatigue_level: int
    discipline_score: float
    focus_score: float

class UserStats(UserStatsBase):
    id: int

    class Config:
        from_attributes = True
