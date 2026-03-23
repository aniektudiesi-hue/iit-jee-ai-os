from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class TaskBase(BaseModel):
    title: str
    subject: str
    difficulty: int
    start_time: datetime
    end_time: datetime
    duration: int
    is_mandatory: bool = False
    is_rest_block: bool = False
    is_free_time: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    points_awarded: Optional[int] = None
    completed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None

class Task(TaskBase):
    id: int
    status: str
    points_awarded: int
    completed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserStatsBase(BaseModel):
    date: datetime
    total_points: int
    sleep_hours: float
    fatigue_level: int
    discipline_score: float
    focus_score: float
    productivity_score: float
    subject_weakness_index: Dict[str, float]
    time_efficiency: float
    sleep_compliance_score: float
    focus_consistency_score: float

class UserStats(UserStatsBase):
    id: int

    class Config:
        from_attributes = True

class DailySummaryBase(BaseModel):
    date: datetime
    total_tasks: int
    completed_tasks: int
    missed_tasks: int
    locked_tasks: int
    total_study_minutes: int
    total_rest_minutes: int
    sleep_duration_minutes: int
    points_earned_today: int

class DailySummary(DailySummaryBase):
    id: int

    class Config:
        from_attributes = True
