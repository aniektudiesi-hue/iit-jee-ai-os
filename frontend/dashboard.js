document.addEventListener('DOMContentLoaded', async () => {
    const pointsDisplay = document.getElementById('points-display');
    const disciplineDisplay = document.getElementById('discipline-display');
    const sleepDisplay = document.getElementById('sleep-display');
    const fatigueDisplay = document.getElementById('fatigue-display');
    const completedTasksDisplay = document.getElementById('completed-tasks');
    const missedTasksDisplay = document.getElementById('missed-tasks');
    const lockedTasksDisplay = document.getElementById('locked-tasks');
    const studyTimeDisplay = document.getElementById('study-time');

    // Fetch stats
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

    // Fetch daily summary
    async function fetchDailySummary() {
        try {
            const response = await fetch('/api/daily-summary');
            const summary = await response.json();
            if (summary) {
                completedTasksDisplay.textContent = summary.completed_tasks;
                missedTasksDisplay.textContent = summary.missed_tasks;
                lockedTasksDisplay.textContent = summary.locked_tasks;
                studyTimeDisplay.textContent = `${(summary.total_study_minutes / 60).toFixed(1)}h`;
            }
        } catch (error) {
            console.error('Error fetching daily summary:', error);
        }
    }

    // Fetch tasks for chart data
    async function fetchTasksForCharts() {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            return tasks;
        } catch (error) {
            console.error('Error fetching tasks:', error);
            return [];
        }
    }

    // Initialize charts with REAL data only
    async function initializeCharts() {
        const tasks = await fetchTasksForCharts();

        // Study Time Distribution Chart - REAL DATA
        const subjectCounts = {};
        tasks.forEach(task => {
            if (!task.is_rest_block && !task.is_free_time && task.status === 'COMPLETED') {
                subjectCounts[task.subject] = (subjectCounts[task.subject] || 0) + task.duration;
            }
        });

        const ctx1 = document.getElementById('studyChart').getContext('2d');
        new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: Object.keys(subjectCounts).length > 0 ? Object.keys(subjectCounts) : ['No Data'],
                datasets: [{
                    data: Object.values(subjectCounts).length > 0 ? Object.values(subjectCounts) : [1],
                    backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#64748b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });

        // Subject Performance Chart (Radar) - REAL DATA
        const stats = await fetch('/api/stats').then(r => r.json());
        const subjectWeakness = stats.subject_weakness_index || {};
        const subjectLabels = Object.keys(subjectWeakness);
        const subjectScores = subjectLabels.map(s => Math.round((1 - subjectWeakness[s]) * 100));

        const ctx2 = document.getElementById('subjectChart').getContext('2d');
        new Chart(ctx2, {
            type: 'radar',
            data: {
                labels: subjectLabels.length > 0 ? subjectLabels : ['Physics', 'Chemistry', 'Math'],
                datasets: [{
                    label: 'Performance Score',
                    data: subjectScores.length > 0 ? subjectScores : [0, 0, 0],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });

        // Weekly Productivity Chart - REAL DATA
        const completedTasks = tasks.filter(t => t.status === 'COMPLETED');
        const dailyPoints = {};
        completedTasks.forEach(task => {
            const date = new Date(task.completed_at).toLocaleDateString('en-US', { weekday: 'short' });
            dailyPoints[date] = (dailyPoints[date] || 0) + task.points_awarded;
        });
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const points = days.map(d => dailyPoints[d] || 0);

        const ctx3 = document.getElementById('productivityChart').getContext('2d');
        new Chart(ctx3, {
            type: 'line',
            data: {
                labels: days,
                datasets: [{
                    label: 'Points Earned',
                    data: points,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });

        // Sleep Compliance Chart - REAL DATA (fetch from sleep history)
        try {
            const sleepResponse = await fetch('/api/sleep/history');
            const sleepSessions = await sleepResponse.json();
            const sleepByDay = {};
            sleepSessions.filter(s => !s.is_active).forEach(session => {
                const date = new Date(session.start_time).toLocaleDateString('en-US', { weekday: 'short' });
                sleepByDay[date] = (sleepByDay[date] || 0) + session.duration_minutes / 60;
            });
            const sleepHours = days.map(d => sleepByDay[d] || 0);

            const ctx4 = document.getElementById('sleepChart').getContext('2d');
            new Chart(ctx4, {
                type: 'bar',
                data: {
                    labels: days,
                    datasets: [{
                        label: 'Sleep Hours',
                        data: sleepHours,
                        backgroundColor: '#2563eb',
                        borderColor: '#1d4ed8',
                        borderWidth: 1
                    }, {
                        label: 'Target (7h)',
                        data: [7, 7, 7, 7, 7, 7, 7],
                        borderColor: '#10b981',
                        borderWidth: 2,
                        type: 'line',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        } catch (error) {
            console.error('Error loading sleep data:', error);
        }
    }

    // Initial load
    await fetchStats();
    await fetchDailySummary();
    await initializeCharts();

    // Auto-refresh every 30 seconds
    setInterval(async () => {
        await fetchStats();
        await fetchDailySummary();
    }, 30000);
});
