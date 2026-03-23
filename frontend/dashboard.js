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

    // Initialize charts
    async function initializeCharts() {
        const tasks = await fetchTasksForCharts();

        // Study Time Distribution Chart
        const subjectCounts = {};
        tasks.forEach(task => {
            if (!task.is_rest_block && !task.is_free_time) {
                subjectCounts[task.subject] = (subjectCounts[task.subject] || 0) + task.duration;
            }
        });

        const ctx1 = document.getElementById('studyChart').getContext('2d');
        new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: Object.keys(subjectCounts),
                datasets: [{
                    data: Object.values(subjectCounts),
                    backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#64748b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Subject Performance Chart (Radar)
        const ctx2 = document.getElementById('subjectChart').getContext('2d');
        new Chart(ctx2, {
            type: 'radar',
            data: {
                labels: ['Physics', 'Chemistry', 'Math', 'Discipline', 'Focus'],
                datasets: [{
                    label: 'Current Performance',
                    data: [65, 75, 80, 90, 85],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Weekly Productivity Chart
        const ctx3 = document.getElementById('productivityChart').getContext('2d');
        new Chart(ctx3, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Points Earned',
                    data: [120, 150, 180, 140, 200, 250, 190],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Sleep Compliance Chart
        const ctx4 = document.getElementById('sleepChart').getContext('2d');
        new Chart(ctx4, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Sleep Hours',
                    data: [7, 6.5, 7.5, 7, 6, 8, 7.5],
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
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
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
