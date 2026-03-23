# IIT JEE AI Discipline Operating System

An ultra-strict AI-driven discipline enforcement machine for IIT JEE preparation.

## Features
- **Single-User Only**: No login, no multiple accounts.
- **Strict Discipline**: Tasks are locked if not started within a 10-minute grace window.
- **AI Schedule Engine**: Dynamically generates a daily schedule based on weak subjects and fatigue.
- **Mandatory Sleep**: Enforces a minimum of 7 hours of sleep daily.
- **Analytics Dashboard**: Visualizes study time, subject performance, and discipline scores using Chart.js.
- **PostgreSQL Integration**: Persistent storage for tasks and stats.

## Deployment on Render

1. **Create a New Web Service**:
   - Connect your GitHub repository.
   - Render will automatically detect the `render.yaml` file.
   - It will provision a PostgreSQL database and a Web Service.

2. **Environment Variables**:
   - `DATABASE_URL`: Automatically provided by Render's database connection.

3. **Local Development**:
   ```bash
   pip install -r requirements.txt
   uvicorn backend.main:app --reload
   ```

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js
- **Data Analysis**: Pandas, NumPy
- **Database**: PostgreSQL (Render)
