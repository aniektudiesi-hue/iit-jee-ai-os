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

def get_past_tasks(db: Session):
    today = datetime.utcnow().date()
    end_of_yesterday = datetime.combine(today, datetime.min.time()) - timedelta(microseconds=1)
    return db.query(models.Task).filter(
        models.Task.end_time <= end_of_yesterday
    ).order_by(models.Task.end_time.desc()).all()

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

def create_or_update_user_stats(db: Session, stats: schemas.UserStatsBase):
    db_stats = db.query(models.UserStats).filter(models.UserStats.date == stats.date.date()).first()
    if db_stats:
        for key, value in stats.dict(exclude_unset=True).items():
            setattr(db_stats, key, value)
    else:
        db_stats = models.UserStats(**stats.dict())
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats

def get_daily_summary(db: Session, date: datetime.date):
    return db.query(models.DailySummary).filter(models.DailySummary.date == date).first()

def create_or_update_daily_summary(db: Session, summary: schemas.DailySummaryBase):
    db_summary = db.query(models.DailySummary).filter(models.DailySummary.date == summary.date.date()).first()
    if db_summary:
        for key, value in summary.dict(exclude_unset=True).items():
            setattr(db_summary, key, value)
    else:
        db_summary = models.DailySummary(**summary.dict())
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

def check_and_update_task_statuses(db: Session):
    now = datetime.utcnow()
    tasks = db.query(models.Task).filter(models.Task.status.in_(["PENDING", "ACTIVE"])).all()

    for task in tasks:
        # Rule: At start_time -> task becomes ACTIVE automatically
        if task.status == "PENDING" and now >= task.start_time:
            task.status = "ACTIVE"
            db.add(task)

        # Rule: 10-minute grace window to mark “started”
        # If not started within grace window -> task becomes LOCKED
        if task.status == "ACTIVE" and now > task.start_time + timedelta(minutes=10) and task.started_at is None:
            task.status = "LOCKED"
            db.add(task)
        
        # Rule: If task is ACTIVE and end_time has passed, and not started, it's MISSED
        if task.status == "ACTIVE" and now > task.end_time and task.started_at is None:
            task.status = "MISSED"
            db.add(task)

    db.commit()

def get_active_task(db: Session):
    now = datetime.utcnow()
    return db.query(models.Task).filter(
        models.Task.status == "ACTIVE",
        models.Task.start_time <= now,
        models.Task.end_time >= now
    ).first()
