import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from . import models, schemas

# --- AI Behavior Engine --- #

def calculate_discipline_score(tasks: List[models.Task]) -> float:
    """Calculate discipline score based on task completion and timeliness."""
    if not tasks:
        return 0.0
    
    df = pd.DataFrame([
        {
            'status': t.status,
            'difficulty': t.difficulty,
            'is_mandatory': t.is_mandatory,
            'start_time': t.start_time,
            'completed_at': t.completed_at,
            'started_at': t.started_at,
            'duration': t.duration # Task duration in minutes
        } for t in tasks
    ])
    
    total_score = 0
    max_possible_score = 0

    for index, row in df.iterrows():
        difficulty_points = row['difficulty'] * 10 # Base points for difficulty
        max_possible_score += difficulty_points

        if row['status'] == 'COMPLETED':
            task_start = row['started_at'] if row['started_at'] else row['start_time']
            task_completed = row['completed_at']
            
            if task_completed and task_start:
                time_to_complete = (task_completed - task_start).total_seconds() / 60
                expected_duration = row['duration'] # Use actual task duration

                if time_to_complete <= expected_duration * 0.9: # Early completion (10% buffer)
                    total_score += difficulty_points * 1.2 # Quality bonus
                elif time_to_complete <= expected_duration * 1.1: # On-time (10% buffer)
                    total_score += difficulty_points
                else: # Late completion
                    total_score += difficulty_points * 0.7 # Reduced points
            else:
                total_score += difficulty_points # Fallback if timestamps are missing

        elif row['status'] == 'STARTED':
            total_score += difficulty_points * 0.5 # Partial credit for started tasks
        elif row['status'] == 'MISSED':
            total_score -= difficulty_points * 0.8 # Penalty for missed
        elif row['status'] == 'LOCKED':
            total_score -= difficulty_points * 1.5 # Heavy penalty for locked

    if max_possible_score == 0:
        return 0.0
    
    # Normalize score to be between 0 and 1
    normalized_score = max(0.0, min(1.0, total_score / max_possible_score))
    return normalized_score

def calculate_fatigue_level(sleep_quality_score: float, missed_tasks_today: int) -> int:
    """Calculate fatigue level based on sleep quality and missed tasks."""
    fatigue = 0
    
    # Poor sleep increases fatigue (lower sleep_quality_score means higher fatigue)
    fatigue += int((1 - sleep_quality_score) * 5) # Max 5 points for very poor sleep
    
    # Missed tasks increase fatigue
    fatigue += missed_tasks_today * 2 # 2 points per missed task

    return min(10, max(0, fatigue)) # Cap fatigue between 0 and 10

def get_subject_weakness_index(tasks: List[models.Task]) -> Dict[str, float]:
    """Identify weak subjects based on performance over all tasks."""
    subject_performance = {}
    for task in tasks:
        if task.subject not in subject_performance:
            subject_performance[task.subject] = {'completed': 0, 'total': 0}
        
        if task.status == 'COMPLETED':
            subject_performance[task.subject]['completed'] += 1
        subject_performance[task.subject]['total'] += 1
    
    weakness_index = {}
    for subject, data in subject_performance.items():
        if data['total'] > 0:
            completion_rate = data['completed'] / data['total']
            weakness_index[subject] = 1 - completion_rate # Higher value means weaker
        else:
            weakness_index[subject] = 0.5 # Neutral if no tasks for this subject
            
    return weakness_index

def calculate_sleep_quality_and_rem(duration_minutes: int) -> (float, int):
    """Calculate sleep quality score (0-1) and estimated REM cycles."""
    target_sleep_minutes = 7 * 60 # 7 hours
    
    # Sleep Quality Score:
    # Ideal sleep is 7-9 hours. Penalize for too little or too much.
    if duration_minutes < 6 * 60: # Less than 6 hours
        quality_score = max(0.0, (duration_minutes - 4 * 60) / (2 * 60)) * 0.5 # Scales from 0 to 0.5
    elif duration_minutes > 9 * 60: # More than 9 hours
        quality_score = max(0.0, 1 - (duration_minutes - 9 * 60) / (2 * 60)) * 0.8 # Scales from 0.8 down
    else: # 6-9 hours is good
        quality_score = 0.7 + (duration_minutes - 6 * 60) / (3 * 60) * 0.3 # Scales from 0.7 to 1.0
    quality_score = round(max(0.0, min(1.0, quality_score)), 2)

    # Estimated REM cycles:
    # Average REM cycle is about 90 minutes (1.5 hours)
    rem_cycle_count = int(duration_minutes / 90) if duration_minutes > 0 else 0
    
    return quality_score, rem_cycle_count

def generate_daily_schedule(db_session, user_stats: Optional[models.UserStats] = None, previous_tasks: Optional[List[models.Task]] = None) -> List[schemas.TaskCreate]:
    """
    AI Engine to generate a strict daily schedule.
    Ensures 7 hours sleep, mandatory exercise, and PCM rotation.
    Dynamically adjusts based on user_stats and previous_tasks.
    """
    schedule = []
    now = datetime.utcnow()
    today_date = now.date()
    
    # Get previous day's sleep quality for fatigue calculation
    last_daily_summary = db_session.query(models.DailySummary).order_by(models.DailySummary.date.desc()).first()
    sleep_quality_yesterday = last_daily_summary.sleep_quality_score if last_daily_summary else 0.7 # Default if no data
    missed_tasks_yesterday = sum(1 for t in previous_tasks if t.status in ['MISSED', 'LOCKED'] and t.start_time.date() == (today_date - timedelta(days=1))) if previous_tasks else 0
    
    fatigue_level = calculate_fatigue_level(sleep_quality_yesterday, missed_tasks_yesterday)
    subject_weakness = get_subject_weakness_index(previous_tasks) if previous_tasks else {}

    # Adjust workload based on fatigue
    total_study_minutes_target = 8 * 60 # 8 hours default
    if fatigue_level > 5:
        total_study_minutes_target *= (1 - (fatigue_level - 5) * 0.1) # Reduce by 10% per fatigue point over 5
    total_study_minutes_target = max(4 * 60, total_study_minutes_target) # Minimum 4 hours study

    # Define fixed blocks
    # We'll schedule tasks from 6 AM to 11 PM.
    current_time = datetime.combine(today_date, datetime.min.time()) + timedelta(hours=6) # Start at 6 AM
    end_of_day = datetime.combine(today_date, datetime.min.time()) + timedelta(hours=23) # End at 11 PM

    # Mandatory Sleep Block (for the *next* day, or representing the current day's required sleep)
    # This is a placeholder to ensure the rule is met, actual scheduling is for waking hours
    # The actual sleep session will be tracked by the user
    schedule.append(schemas.TaskCreate(
        title="MANDATORY SLEEP BLOCK (7 hours minimum)",
        subject="Health",
        difficulty=1,
        start_time=datetime.combine(today_date, datetime.min.time()) + timedelta(hours=23), # 11 PM today
        end_time=datetime.combine(today_date + timedelta(days=1), datetime.min.time()) + timedelta(hours=6), # 6 AM tomorrow
        duration=7*60,
        is_mandatory=True,
        is_rest_block=True,
        is_free_time=True
    ))

    # 1. Morning Exercise (Mandatory)
    schedule.append(schemas.TaskCreate(
        title="Morning Exercise & Routine",
        subject="Health",
        difficulty=2,
        start_time=current_time,
        end_time=current_time + timedelta(minutes=60),
        duration=60,
        is_mandatory=True
    ))
    current_time += timedelta(minutes=60)

    # 2. Study Blocks (PCM Rotation, adjusted by weakness)
    subjects = ["Physics", "Chemistry", "Mathematics"]
    # Sort subjects by weakness (weakest first)
    sorted_subjects = sorted(subjects, key=lambda s: subject_weakness.get(s, 0.5), reverse=True)

    study_block_count = 0
    while current_time < end_of_day - timedelta(hours=4) and study_block_count < 5: # Leave room for free time and evening tasks
        subject = sorted_subjects[study_block_count % len(sorted_subjects)]
        duration = 90 + np.random.randint(-15, 15) # 75-105 minutes per block
        if total_study_minutes_target <= 0: # Stop if target reached
            break
        duration = min(duration, total_study_minutes_target)

        schedule.append(schemas.TaskCreate(
            title=f"{subject} Deep Work Session",
            subject=subject,
            difficulty=4,
            start_time=current_time,
            end_time=current_time + timedelta(minutes=duration),
            duration=duration,
            is_mandatory=True
        ))
        current_time += timedelta(minutes=duration)
        total_study_minutes_target -= duration

        # Mandatory Rest Block (15-60 mins)
        rest_duration = 30 + np.random.randint(-10, 10) # 20-40 minutes
        if current_time + timedelta(minutes=rest_duration) < end_of_day - timedelta(hours=2):
            schedule.append(schemas.TaskCreate(
                title="Mandatory Rest Block",
                subject="Rest",
                difficulty=1,
                start_time=current_time,
                end_time=current_time + timedelta(minutes=rest_duration),
                duration=rest_duration,
                is_rest_block=True,
                is_free_time=True
            ))
            current_time += timedelta(minutes=rest_duration)
        study_block_count += 1

    # 3. Free Time Blocks (Rest, Break, Personal Time)
    # Ensure minimum 2-3 rest blocks daily (already handled above)
    # Add a larger personal time block towards the evening
    if current_time < end_of_day - timedelta(minutes=90):
        personal_time_duration = (end_of_day - timedelta(minutes=90) - current_time).total_seconds() / 60
        if personal_time_duration > 30:
            schedule.append(schemas.TaskCreate(
                title="Personal Time / Hobbies",
                subject="Personal",
                difficulty=1,
                start_time=current_time,
                end_time=current_time + timedelta(minutes=int(personal_time_duration)),
                duration=int(personal_time_duration),
                is_free_time=True
            ))
            current_time += timedelta(minutes=int(personal_time_duration))

    # 4. Evening Revision / Weak Areas
    if current_time < end_of_day:
        remaining_time = (end_of_day - current_time).total_seconds() / 60
        if remaining_time > 30:
            schedule.append(schemas.TaskCreate(
                title="Daily Review & Planning",
                subject="Revision",
                difficulty=3,
                start_time=current_time,
                end_time=current_time + timedelta(minutes=int(remaining_time)),
                duration=int(remaining_time),
                is_mandatory=True
            ))
            current_time += timedelta(minutes=int(remaining_time))

    # Sort schedule by start time
    schedule.sort(key=lambda x: x.start_time)
    return schedule

def update_user_stats_from_tasks(db_session, tasks: List[models.Task], current_stats: models.UserStats, sleep_quality_today: float) -> models.UserStats:
    """
    Updates user statistics based on completed tasks and daily performance.
    """
    today_tasks = [t for t in tasks if t.start_time.date() == datetime.utcnow().date()]
    
    # Calculate discipline score for today
    discipline_score = calculate_discipline_score(today_tasks)

    # Calculate total points for today
    points_earned_today = sum(t.points_awarded for t in today_tasks if t.status == 'COMPLETED')

    # Update total points
    current_stats.total_points += points_earned_today
    current_stats.discipline_score = discipline_score # This could be an average or daily score
    current_stats.fatigue_level = calculate_fatigue_level(sleep_quality_today, sum(1 for t in today_tasks if t.status in ['MISSED', 'LOCKED']))
    current_stats.subject_weakness_index = get_subject_weakness_index(tasks) # Update based on all tasks

    # Placeholder for other stats (productivity, time efficiency, focus consistency)
    current_stats.productivity_score = (current_stats.productivity_score * 0.8 + discipline_score * 0.2) # Simple moving average
    current_stats.time_efficiency = 0.0 # Needs more complex calculation
    current_stats.focus_consistency_score = 0.0 # Needs more complex calculation
    current_stats.sleep_compliance_score = sleep_quality_today

    return current_stats

def update_daily_summary(db_session, tasks: List[models.Task], sleep_session: Optional[models.SleepSession] = None):
    today = datetime.utcnow().date()
    daily_summary = db_session.query(models.DailySummary).filter(models.DailySummary.date == today).first()
    if not daily_summary:
        daily_summary = models.DailySummary(date=today)

    today_tasks = [t for t in tasks if t.start_time.date() == today]

    daily_summary.total_tasks = len(today_tasks)
    daily_summary.completed_tasks = sum(1 for t in today_tasks if t.status == 'COMPLETED')
    daily_summary.missed_tasks = sum(1 for t in today_tasks if t.status == 'MISSED')
    daily_summary.locked_tasks = sum(1 for t in today_tasks if t.status == 'LOCKED')
    daily_summary.total_study_minutes = sum(t.duration for t in today_tasks if not t.is_rest_block and not t.is_free_time and t.status == 'COMPLETED')
    daily_summary.total_rest_minutes = sum(t.duration for t in today_tasks if (t.is_rest_block or t.is_free_time) and t.status == 'COMPLETED')
    daily_summary.points_earned_today = sum(t.points_awarded for t in today_tasks if t.status == 'COMPLETED')

    if sleep_session:
        daily_summary.sleep_duration_minutes = sleep_session.duration_minutes
        daily_summary.sleep_quality_score = sleep_session.sleep_quality_score
        daily_summary.rem_cycle_count = sleep_session.rem_cycle_count

    db_session.add(daily_summary)
    db_session.commit()
    db_session.refresh(daily_summary)
    return daily_summary
