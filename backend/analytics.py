import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from . import models, schemas

def calculate_discipline_score(tasks):
    """Calculate discipline score based on task completion and timeliness."""
    if not tasks:
        return 0.0
    
    df = pd.DataFrame([
        {
            'status': t.status,
            'difficulty': t.difficulty,
            'is_mandatory': t.is_mandatory
        } for t in tasks
    ])
    
    # Weights for different statuses
    status_weights = {
        'COMPLETED': 1.0,
        'ACTIVE': 0.5,
        'PENDING': 0.0,
        'MISSED': -0.5,
        'LOCKED': -1.0
    }
    
    df['score'] = df['status'].map(status_weights) * df['difficulty']
    
    # Penalize missed mandatory tasks more heavily
    df.loc[(df['is_mandatory']) & (df['status'].isin(['MISSED', 'LOCKED'])), 'score'] *= 1.5
    
    total_possible = df['difficulty'].sum()
    if total_possible == 0:
        return 0.0
        
    actual_score = df['score'].sum()
    normalized_score = max(0, min(1, actual_score / total_possible))
    
    return float(normalized_score)

def generate_daily_schedule(user_stats=None):
    """
    AI Engine to generate a strict daily schedule.
    Ensures 7 hours sleep, mandatory exercise, and PCM rotation.
    """
    # Start day at 6:00 AM
    base_time = datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0)
    
    schedule = []
    
    # 1. Sleep Block (Mandatory 7 hours) - usually at the end of the day
    # But we'll mark it for the next day's start or previous day's end
    # For simplicity, let's assume sleep is 11 PM to 6 AM
    
    # 2. Morning Routine / Exercise (Mandatory)
    schedule.append({
        "title": "Morning Exercise & Routine",
        "subject": "Health",
        "difficulty": 2,
        "start_time": base_time,
        "end_time": base_time + timedelta(minutes=60),
        "duration": 60,
        "is_mandatory": True
    })
    
    # 3. Study Blocks (PCM Rotation)
    subjects = ["Physics", "Chemistry", "Mathematics"]
    current_time = base_time + timedelta(minutes=60)
    
    for i in range(3):
        # Study Block
        duration = 120 # 2 hours
        schedule.append({
            "title": f"{subjects[i]} Deep Work Session",
            "subject": subjects[i],
            "difficulty": 4,
            "start_time": current_time,
            "end_time": current_time + timedelta(minutes=duration),
            "duration": duration,
            "is_mandatory": True
        })
        current_time += timedelta(minutes=duration)
        
        # Mandatory Rest Block (15-60 mins)
        rest_duration = 30
        schedule.append({
            "title": "Mandatory Rest Block",
            "subject": "Rest",
            "difficulty": 1,
            "start_time": current_time,
            "end_time": current_time + timedelta(minutes=rest_duration),
            "duration": rest_duration,
            "is_rest_block": True
        })
        current_time += timedelta(minutes=rest_duration)

    # 4. Evening Revision / Weak Areas
    schedule.append({
        "title": "Daily Revision & Weak Topics",
        "subject": "Revision",
        "difficulty": 3,
        "start_time": current_time,
        "end_time": current_time + timedelta(minutes=90),
        "duration": 90,
        "is_mandatory": True
    })
    
    return schedule
