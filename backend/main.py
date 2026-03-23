from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime, timedelta

from . import crud, models, schemas, database
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IIT JEE AI Discipline OS")

# Mount static files
# In production, frontend might be served separately, but for single-repo deployment:
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

@app.get("/dashboard")
async def read_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/api/tasks", response_model=List[schemas.Task])
def read_tasks(db: Session = Depends(get_db)):
    return crud.get_today_tasks(db)

@app.post("/api/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)

@app.patch("/api/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db, task_id, task_update)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.get("/api/stats", response_model=schemas.UserStats)
def read_stats(db: Session = Depends(get_db)):
    stats = crud.get_user_stats(db)
    if stats is None:
        # Return default stats if none exist
        return schemas.UserStats(
            id=0,
            date=datetime.utcnow(),
            total_points=0,
            sleep_hours=0.0,
            fatigue_level=0,
            discipline_score=0.0,
            focus_score=0.0
        )
    return stats

from . import analytics

@app.post("/api/generate-schedule")
def generate_schedule(db: Session = Depends(get_db)):
    # 1. Clear existing tasks for today (to avoid duplicates)
    today_tasks = crud.get_today_tasks(db)
    for task in today_tasks:
        db.delete(task)
    db.commit()

    # 2. Generate new schedule using AI engine
    new_schedule = analytics.generate_daily_schedule()
    
    # 3. Save to database
    for task_data in new_schedule:
        task_create = schemas.TaskCreate(**task_data)
        crud.create_task(db, task_create)
        
    return {"message": f"Generated {len(new_schedule)} tasks for today"}
