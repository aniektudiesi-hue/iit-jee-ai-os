from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta
import json
from apscheduler.schedulers.background import BackgroundScheduler

from . import crud, models, schemas, database, analytics
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IIT JEE AI Discipline OS")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Background scheduler for auto-generation
scheduler = BackgroundScheduler()

def auto_generate_daily_schedule():
    """Auto-generate schedule at midnight every day"""
    db = database.SessionLocal()
    try:
        user_stats = crud.get_user_stats(db)
        previous_tasks = crud.get_past_tasks(db)

        # Clear existing tasks for today
        today_tasks = crud.get_today_tasks(db)
        for task in today_tasks:
            db.delete(task)
        db.commit()

        # Generate new schedule
        new_schedule_data = analytics.generate_daily_schedule(db, user_stats, previous_tasks)
        
        # Save to database
        for task_data in new_schedule_data:
            crud.create_task(db, task_data)
        db.commit()

        # Update stats and daily summary after schedule generation
        all_tasks = crud.get_tasks(db)
        latest_sleep_session = crud.get_sleep_sessions(db, limit=1)
        sleep_quality_today = latest_sleep_session[0].sleep_quality_score if latest_sleep_session and not latest_sleep_session[0].is_active else 0.7

        updated_stats = analytics.update_user_stats_from_tasks(db, all_tasks, user_stats if user_stats else models.UserStats(
            date=datetime.utcnow(), total_points=0, sleep_hours=7.0, fatigue_level=0, discipline_score=0.0, focus_score=0.0,
            productivity_score=0.0, subject_weakness_index=\'{}\', time_efficiency=0.0, sleep_compliance_score=1.0, focus_consistency_score=0.0
        ), sleep_quality_today)
        crud.create_or_update_user_stats(db, updated_stats)
        analytics.update_daily_summary(db, all_tasks, latest_sleep_session[0] if latest_sleep_session and not latest_sleep_session[0].is_active else None)
        
        print("✅ Daily schedule auto-generated at midnight")
    except Exception as e:
        print(f"❌ Error in auto-generation: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """On app startup, check if today's schedule exists. If not, generate it."""
    db = database.SessionLocal()
    try:
        models.Base.metadata.create_all(bind=engine) # Ensure tables are created
        today_tasks = crud.get_today_tasks(db)
        if not today_tasks:
            print("🔄 No tasks for today. Generating schedule...")
            auto_generate_daily_schedule()
        
        # Start background scheduler for midnight auto-generation
        if not scheduler.running:
            scheduler.add_job(auto_generate_daily_schedule, trigger=\'cron\', hour=0, minute=0)
            scheduler.start()
            print("⏰ Background scheduler started for daily auto-generation")
    except Exception as e:
        print(f"Error during startup: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler on app shutdown"""
    if scheduler.running:
        scheduler.shutdown()

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

@app.get("/dashboard")
async def read_dashboard():
    return FileResponse("frontend/dashboard.html")

# API Endpoints

@app.get("/api/tasks", response_model=List[schemas.Task])
def get_today_tasks_api(db: Session = Depends(get_db)):
    """Get today's tasks with automatic status enforcement"""
    crud.check_and_update_task_statuses(db)
    return crud.get_today_tasks(db)

@app.get("/api/tasks/past", response_model=List[schemas.Task])
def get_past_tasks_api(db: Session = Depends(get_db)):
    """Get past tasks (completed/missed)"""
    return crud.get_past_tasks(db)

@app.get("/api/tasks/active", response_model=Optional[schemas.Task])
def get_active_task_api(db: Session = Depends(get_db)):
    """Get currently active task"""
    crud.check_and_update_task_statuses(db)
    return crud.get_active_task(db)

@app.post("/api/tasks", response_model=schemas.Task)
def create_task_api(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task (admin use)"""
    return crud.create_task(db, task)

@app.patch("/api/tasks/{task_id}", response_model=schemas.Task)
def update_task_api(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """Update task details"""
    db_task = crud.update_task(db, task_id, task_update)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_update.status == "COMPLETED" and db_task.completed_at:
        db_task.points_awarded = db_task.difficulty * 10
        crud.update_task(db, task_id, schemas.TaskUpdate(points_awarded=db_task.points_awarded))

    return db_task

@app.post("/api/tasks/{task_id}/start", response_model=schemas.Task)
def start_task_api(task_id: int, db: Session = Depends(get_db)):
    """Start a task (marks as STARTED within grace window)"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    now = datetime.utcnow()
    grace_window = db_task.start_time + timedelta(minutes=10)
    
    if db_task.status in ["PENDING", "ACTIVE"] and now <= grace_window:
        db_task.status = "STARTED"
        db_task.started_at = now
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    else:
        raise HTTPException(status_code=400, detail="Task cannot be started. Grace window expired or already locked.")
    return db_task

@app.post("/api/tasks/{task_id}/complete", response_model=schemas.Task)
def complete_task_api(task_id: int, db: Session = Depends(get_db)):
    """Complete a task (only if STARTED)"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if db_task.status == "STARTED":
        db_task.status = "COMPLETED"
        db_task.completed_at = datetime.utcnow()
        db_task.points_awarded = db_task.difficulty * 10
        
        if db_task.started_at and (db_task.completed_at - db_task.started_at).total_seconds() / 60 < db_task.duration:
            db_task.points_awarded += db_task.difficulty * 5  # Early completion bonus
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    else:
        raise HTTPException(status_code=400, detail="Task must be in STARTED status to complete.")
    return db_task

@app.get("/api/stats", response_model=schemas.UserStats)
def get_user_stats_api(db: Session = Depends(get_db)):
    """Get user statistics"""
    stats = crud.get_user_stats(db)
    if stats is None:
        return schemas.UserStats(
            id=0,
            date=datetime.utcnow(),
            total_points=0,
            sleep_hours=7.0,
            fatigue_level=0,
            discipline_score=0.0,
            focus_score=0.0,
            productivity_score=0.0,
            subject_weakness_index={},
            time_efficiency=0.0,
            sleep_compliance_score=1.0,
            focus_consistency_score=0.0
        )
    if isinstance(stats.subject_weakness_index, str):
        stats.subject_weakness_index = json.loads(stats.subject_weakness_index) if stats.subject_weakness_index else {}
    return stats

@app.get("/api/daily-summary", response_model=Optional[schemas.DailySummary])
def get_daily_summary_api(db: Session = Depends(get_db)):
    """Get today's summary"""
    today = datetime.utcnow().date()
    return crud.get_daily_summary(db, today)

@app.get("/api/time-info")
def get_time_info():
    """Get current time and day info for frontend"""
    now = datetime.utcnow()
    return {
        "current_time": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "date": now.strftime("%Y-%m-%d"),
        "hour": now.hour,
        "minute": now.minute
    }

@app.post("/api/generate-schedule")
def generate_schedule_api(db: Session = Depends(get_db)):
    """Manually regenerate schedule (for testing/admin)"""
    user_stats = crud.get_user_stats(db)
    previous_tasks = crud.get_past_tasks(db)

    today_tasks = crud.get_today_tasks(db)
    for task in today_tasks:
        db.delete(task)
    db.commit()

    new_schedule_data = analytics.generate_daily_schedule(db, user_stats, previous_tasks)
    
    for task_data in new_schedule_data:
        crud.create_task(db, task_data)
    db.commit()

    all_tasks = crud.get_tasks(db)
    latest_sleep_session = crud.get_sleep_sessions(db, limit=1)
    sleep_quality_today = latest_sleep_session[0].sleep_quality_score if latest_sleep_session and not latest_sleep_session[0].is_active else 0.7

    updated_stats = analytics.update_user_stats_from_tasks(db, all_tasks, user_stats if user_stats else models.UserStats(
        date=datetime.utcnow(), total_points=0, sleep_hours=7.0, fatigue_level=0, discipline_score=0.0, focus_score=0.0,
        productivity_score=0.0, subject_weakness_index=\'{}\', time_efficiency=0.0, sleep_compliance_score=1.0, focus_consistency_score=0.0
    ), sleep_quality_today)
    crud.create_or_update_user_stats(db, updated_stats)
    analytics.update_daily_summary(db, all_tasks, latest_sleep_session[0] if latest_sleep_session and not latest_sleep_session[0].is_active else None)

    return {"message": f"Generated {len(new_schedule_data)} tasks for today"}

# --- Sleep Tracking Endpoints ---

@app.post("/api/sleep/start", response_model=schemas.SleepSession)
def start_sleep_session(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    # Allow starting sleep only after 11 PM (23:00) and before 6 AM (06:00)
    if not (now.hour >= 23 or now.hour < 6):
        raise HTTPException(status_code=400, detail="Sleep can only be started between 11 PM and 6 AM.")

    active_session = crud.get_active_sleep_session(db)
    if active_session:
        raise HTTPException(status_code=400, detail="An active sleep session is already running.")
    
    sleep_session_create = schemas.SleepSessionCreate(start_time=now)
    return crud.create_sleep_session(db, sleep_session_create)

@app.post("/api/sleep/stop", response_model=schemas.SleepSession)
def stop_sleep_session(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    active_session = crud.get_active_sleep_session(db)
    if not active_session:
        raise HTTPException(status_code=400, detail="No active sleep session to stop.")
    
    duration_minutes = int((now - active_session.start_time).total_seconds() / 60)
    sleep_quality, rem_cycles = analytics.calculate_sleep_quality_and_rem(duration_minutes)

    sleep_session_update = schemas.SleepSessionUpdate(
        end_time=now,
        duration_minutes=duration_minutes,
        sleep_quality_score=sleep_quality,
        rem_cycle_count=rem_cycles,
        is_active=False
    )
    updated_session = crud.update_sleep_session(db, active_session.id, sleep_session_update)

    # Update UserStats and DailySummary with new sleep data
    all_tasks = crud.get_tasks(db)
    user_stats = crud.get_user_stats(db)
    if user_stats:
        user_stats.sleep_hours = duration_minutes / 60
        updated_stats = analytics.update_user_stats_from_tasks(db, all_tasks, user_stats, sleep_quality)
        crud.create_or_update_user_stats(db, updated_stats)
    
    analytics.update_daily_summary(db, all_tasks, updated_session)

    return updated_session

@app.get("/api/sleep/active", response_model=Optional[schemas.SleepSession])
def get_active_sleep_session_api(db: Session = Depends(get_db)):
    return crud.get_active_sleep_session(db)

@app.get("/api/sleep/history", response_model=List[schemas.SleepSession])
def get_sleep_history_api(db: Session = Depends(get_db)):
    return crud.get_sleep_sessions(db)
