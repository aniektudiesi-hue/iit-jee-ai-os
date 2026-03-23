from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Task).offset(skip).limit(limit).all()

def get_today_tasks(db: Session):
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    return db.query(models.Task).filter(
        models.Task.start_time >= start_of_day,
        models.Task.start_time <= end_of_day
    ).order_by(models.Task.start_time).all()

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        for key, value in task_update.dict(exclude_unset=True).items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def get_user_stats(db: Session):
    return db.query(models.UserStats).order_by(models.UserStats.date.desc()).first()

def update_user_stats(db: Session, stats: schemas.UserStatsBase):
    db_stats = models.UserStats(**stats.dict())
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats
