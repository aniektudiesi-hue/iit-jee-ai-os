document.addEventListener('DOMContentLoaded', () => {
    const taskList = document.getElementById('task-list');
    const pointsDisplay = document.getElementById('points-display');
    const disciplineDisplay = document.getElementById('discipline-display');
    const sleepDisplay = document.getElementById('sleep-display');
    const generateBtn = document.getElementById('generate-btn');

    // Fetch tasks from API
    async function fetchTasks() {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            renderTasks(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
            taskList.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--danger);">Failed to load tasks. Please try again.</div>';
        }
    }

    // Fetch stats from API
    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            pointsDisplay.textContent = stats.total_points;
            disciplineDisplay.textContent = `${Math.round(stats.discipline_score * 100)}%`;
            sleepDisplay.textContent = `${stats.sleep_hours}h`;
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    // Render tasks to the UI
    function renderTasks(tasks) {
        if (tasks.length === 0) {
            taskList.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No tasks scheduled for today. Click "Regenerate Schedule" to start.</div>';
            return;
        }

        taskList.innerHTML = '';
        tasks.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = `task-item status-${task.status.toLowerCase()}`;
            
            const startTime = new Date(task.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const endTime = new Date(task.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            taskItem.innerHTML = `
                <div class="task-info">
                    <div class="task-title">${task.title}</div>
                    <div class="task-meta">${task.subject} | ${startTime} - ${endTime} (${task.duration} min)</div>
                </div>
                <div class="task-status status-${task.status.toLowerCase()}">${task.status}</div>
            `;
            taskList.appendChild(taskItem);
        });
    }

    // Handle schedule generation
    generateBtn.addEventListener('click', async () => {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        try {
            await fetch('/api/generate-schedule', { method: 'POST' });
            await fetchTasks();
        } catch (error) {
            console.error('Error generating schedule:', error);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Regenerate Schedule';
        }
    });

    // Initial load
    fetchTasks();
    fetchStats();
});
