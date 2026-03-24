// Global state
let currentFocusTaskId = null;
let focusTimer = null;
let focusTimeRemaining = 0;
let currentTimeInfo = null;

document.addEventListener('DOMContentLoaded', () => {
    const taskList = document.getElementById('task-list');
    const pointsDisplay = document.getElementById('points-display');
    const disciplineDisplay = document.getElementById('discipline-display');
    const sleepDisplay = document.getElementById('sleep-display');
    const fatigueDisplay = document.getElementById('fatigue-display');
    const generateBtn = document.getElementById('generate-btn');
    const focusModal = document.getElementById('focus-modal');
    const exitFocusBtn = document.getElementById('exit-focus-btn');
    const completeFocusBtn = document.getElementById('complete-focus-btn');
    const pauseFocusBtn = document.getElementById('pause-focus-btn');

    // Fetch current time and day info
    async function fetchTimeInfo() {
        try {
            const response = await fetch('/api/time-info');
            currentTimeInfo = await response.json();
            console.log(`📅 Current Time: ${currentTimeInfo.day_of_week}, ${currentTimeInfo.date} at ${currentTimeInfo.current_time}`);
            return currentTimeInfo;
        } catch (error) {
            console.error('Error fetching time info:', error);
        }
    }

    // Fetch tasks from API
    async function fetchTasks() {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            renderTasks(tasks);
            updateActiveTaskCard(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
            taskList.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--danger);">Failed to load tasks. Please try again.</div>';
        }
    }

    // Fetch past tasks
    async function fetchPastTasks() {
        try {
            const response = await fetch('/api/tasks/past');
            const tasks = await response.json();
            renderPastTasks(tasks);
        } catch (error) {
            console.error('Error fetching past tasks:', error);
        }
    }

    // Fetch stats from API
    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            pointsDisplay.textContent = stats.total_points;
            disciplineDisplay.textContent = `${Math.round(stats.discipline_score * 100)}%`;
            sleepDisplay.textContent = `${stats.sleep_hours.toFixed(1)}h`;
            fatigueDisplay.textContent = `${stats.fatigue_level}/10`;
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    // Render tasks to the UI
    function renderTasks(tasks) {
        if (tasks.length === 0) {
            taskList.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">⏳ Generating your personalized schedule based on current time and day...</div>';
            return;
        }

        taskList.innerHTML = '';
        
        // Filter and sort tasks by time
        const now = new Date();
        // Filter tasks to only show those for the current day, or active/started tasks from previous days that haven't been resolved
        const today = now.toISOString().slice(0, 10);
        const relevantTasks = tasks.filter(t => {
            const taskDate = new Date(t.start_time).toISOString().slice(0, 10);
            return taskDate === today || (t.status === 'ACTIVE' || t.status === 'STARTED');
        });

        const upcomingTasks = relevantTasks.filter(t => new Date(t.start_time) > now && t.status === 'PENDING').sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        const activeTasks = relevantTasks.filter(t => t.status === 'ACTIVE' || t.status === 'STARTED');
        const completedTasks = relevantTasks.filter(t => t.status === 'COMPLETED');
        const lockedMissedTasks = relevantTasks.filter(t => t.status === 'LOCKED' || t.status === 'MISSED');

        // Show active tasks first
        if (activeTasks.length > 0) {
            const activeHeader = document.createElement('div');
            activeHeader.style.cssText = 'font-weight: 700; color: var(--primary); margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.875rem;';
            activeHeader.textContent = '🔴 Active Now';
            taskList.appendChild(activeHeader);

            activeTasks.forEach(task => {
                taskList.appendChild(createTaskElement(task));
            });
        }

        // Show upcoming tasks
        // Show locked/missed tasks
        if (lockedMissedTasks.length > 0) {
            const lockedMissedHeader = document.createElement('div');
            lockedMissedHeader.style.cssText = 'font-weight: 700; color: var(--danger); margin-top: 1.5rem; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.875rem;';
            lockedMissedHeader.textContent = '🚫 Locked / Missed';
            taskList.appendChild(lockedMissedHeader);

            lockedMissedTasks.forEach(task => {
                taskList.appendChild(createTaskElement(task));
            });
        }

        if (upcomingTasks.length > 0) {
            const upcomingHeader = document.createElement('div');
            upcomingHeader.style.cssText = 'font-weight: 700; color: var(--secondary); margin-top: 1.5rem; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.875rem;';
            upcomingHeader.textContent = '⏭️ Upcoming';
            taskList.appendChild(upcomingHeader);

            upcomingTasks.forEach(task => {
                taskList.appendChild(createTaskElement(task));
            });
        }

        // Show completed tasks
        if (completedTasks.length > 0) {
            const completedHeader = document.createElement('div');
            completedHeader.style.cssText = 'font-weight: 700; color: var(--success); margin-top: 1.5rem; margin-bottom: 0.5rem; text-transform: uppercase; font-size: 0.875rem;';
            completedHeader.textContent = '✅ Completed Today';
            taskList.appendChild(completedHeader);

            completedTasks.forEach(task => {
                taskList.appendChild(createTaskElement(task));
            });
        }
    }

    // Create task element
    function createTaskElement(task) {
        const taskItem = document.createElement('div');
        taskItem.className = `task-item ${task.status.toLowerCase()}`;
        
        const startTime = new Date(task.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const endTime = new Date(task.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        taskItem.innerHTML = `
            <div class="task-info">
                <div class="task-title">${task.title}</div>
                <div class="task-meta">${task.subject} | ${startTime} - ${endTime} (${task.duration} min) | Difficulty: ${task.difficulty}/5</div>
            </div>
            <div class="task-status status-${task.status.toLowerCase()}">${task.status}</div>
        `;
        
        taskItem.addEventListener('click', () => handleTaskClick(task));
        return taskItem;
    }

    // Render past tasks
    function renderPastTasks(tasks) {
        const pastTasksCard = document.getElementById('past-tasks-card');
        const pastTaskList = document.getElementById('past-task-list');
        
        if (tasks.length === 0) {
            pastTasksCard.style.display = 'none';
            return;
        }

        pastTasksCard.style.display = 'block';
        pastTaskList.innerHTML = '';
        
        tasks.slice(0, 10).forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = `task-item ${task.status.toLowerCase()}`;
            
            const startTime = new Date(task.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const completedTime = task.completed_at ? new Date(task.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A';

            taskItem.innerHTML = `
                <div class="task-info">
                    <div class="task-title">${task.title}</div>
                    <div class="task-meta">${task.subject} | Started: ${startTime} | Completed: ${completedTime}</div>
                </div>
                <div class="task-status status-${task.status.toLowerCase()}">${task.status}</div>
            `;
            pastTaskList.appendChild(taskItem);
        });
    }

    // Update active task card
    function updateActiveTaskCard(tasks) {
        const activeTaskCard = document.getElementById('active-task-card');
        const activeTaskContent = document.getElementById('active-task-content');
        const activeTask = tasks.find(t => t.status === 'ACTIVE');

        if (activeTask) {
            activeTaskCard.style.display = 'block';
            const startTime = new Date(activeTask.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const endTime = new Date(activeTask.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            activeTaskContent.innerHTML = `
                <p><strong>${activeTask.title}</strong></p>
                <p>Subject: ${activeTask.subject}</p>
                <p>Duration: ${activeTask.duration} minutes</p>
                <p>Time: ${startTime} - ${endTime}</p>
                <p style="color: var(--danger); font-weight: 600;">⚠️ 10-minute grace window to start!</p>
            `;

            document.getElementById('start-btn').onclick = () => startTask(activeTask.id);
            document.getElementById('focus-btn').onclick = () => enterFocusMode(activeTask);
        } else {
            activeTaskCard.style.display = 'none';
        }
    }

    // Handle task click
    async function handleTaskClick(task) {
        if (task.status === 'ACTIVE') {
            console.log('Task clicked:', task);
        }
    }

    // Start task
    async function startTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/start`, { method: 'POST' });
            if (response.ok) {
                const updatedTask = await response.json();
                console.log('✅ Task started:', updatedTask);
                fetchTasks();
            } else {
                alert('❌ Cannot start task. Grace window may have expired.');
            }
        } catch (error) {
            console.error('Error starting task:', error);
        }
    }

    // Enter Focus Mode
    function enterFocusMode(task) {
        currentFocusTaskId = task.id;
        focusTimeRemaining = task.duration * 60;

        startTask(task.id).then(() => {
            focusModal.style.display = 'flex';
            document.getElementById('focus-title').textContent = `Focus Mode: ${task.title}`;
            document.getElementById('focus-task-details').innerHTML = `
                <p><strong>Subject:</strong> ${task.subject}</p>
                <p><strong>Duration:</strong> ${task.duration} minutes</p>
                <p><strong>Difficulty:</strong> ${task.difficulty}/5</p>
                <p style="color: var(--primary); font-weight: 600;">🎯 Stay focused. No distractions.</p>
            `;

            startFocusTimer();
        });
    }

    // Start focus timer
    function startFocusTimer() {
        if (focusTimer) clearInterval(focusTimer);

        focusTimer = setInterval(() => {
            focusTimeRemaining--;
            updateTimerDisplay();

            if (focusTimeRemaining <= 0) {
                clearInterval(focusTimer);
                completeTask(currentFocusTaskId);
            }
        }, 1000);
    }

    // Update timer display
    function updateTimerDisplay() {
        const minutes = Math.floor(focusTimeRemaining / 60);
        const seconds = focusTimeRemaining % 60;
        const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        document.getElementById('timer-display').textContent = display;
    }

    // Complete task
    async function completeTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/complete`, { method: 'POST' });
            if (response.ok) {
                const completedTask = await response.json();
                console.log('✅ Task completed:', completedTask);
                
                focusModal.style.display = 'none';
                clearInterval(focusTimer);
                
                fetchTasks();
                fetchStats();
                
                alert(`🎉 Task completed! +${completedTask.points_awarded} points earned!`);
            } else {
                alert('❌ Error completing task.');
            }
        } catch (error) {
            console.error('Error completing task:', error);
        }
    }

    // Handle schedule generation
    generateBtn.addEventListener('click', async () => {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Regenerating...';
        try {
            const response = await fetch('/api/generate-schedule', { method: 'POST' });
            if (response.ok) {
                await fetchTasks();
                await fetchStats();
                alert('✅ Schedule regenerated successfully!');
            } else {
                alert('❌ Error generating schedule.');
            }
        } catch (error) {
            console.error('Error generating schedule:', error);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Regenerate Schedule';
        }
    });

    // Focus mode controls
    exitFocusBtn.addEventListener('click', () => {
        if (focusTimer) clearInterval(focusTimer);
        focusModal.style.display = 'none';
    });

    completeFocusBtn.addEventListener('click', () => {
        completeTask(currentFocusTaskId);
    });

    pauseFocusBtn.addEventListener('click', () => {
        if (focusTimer) {
            clearInterval(focusTimer);
            pauseFocusBtn.textContent = 'Resume';
        } else {
            startFocusTimer();
            pauseFocusBtn.textContent = 'Pause';
        }
    });

    // Auto-refresh tasks every 15 seconds to enforce grace window
    setInterval(() => {
        fetchTasks();
        fetchStats();
    }, 15000);

    // Initial load
    (async () => {
        await fetchTimeInfo();
        await fetchTasks();
        await fetchPastTasks();
        await fetchStats();
    })();
});
