let activeSleepSession = null;
let sleepTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
    const startSleepBtn = document.getElementById('start-sleep-btn');
    const stopSleepBtn = document.getElementById('stop-sleep-btn');
    const sleepStatusDisplay = document.getElementById('sleep-status-display');
    const sleepControlCard = document.getElementById('sleep-control-card');
    const sleepQualityCard = document.getElementById('sleep-quality-card');

    // Fetch current time to determine if sleep can be started
    async function updateSleepControlsBasedOnTime() {
        try {
            const response = await fetch('/api/time-info');
            const timeInfo = await response.json();
            const hour = timeInfo.hour;

            // Allow sleep only between 11 AM (11) and 4 AM (next day)
            const canStartSleep = hour >= 11 || hour < 4;
            startSleepBtn.style.display = canStartSleep ? 'block' : 'none';
            
            if (!canStartSleep) {
                sleepStatusDisplay.innerHTML = `
                    <p style="font-size: 1.125rem; color: var(--danger);">⏰ Sleep tracking is only available between 11 AM and 4 AM</p>
                    <p style="color: var(--text-muted);">Current time: ${timeInfo.day_of_week}, ${timeInfo.date} at ${String(hour).padStart(2, '0')}:${String(timeInfo.minute).padStart(2, '0')}</p>
                `;
            }
        } catch (error) {
            console.error('Error fetching time info:', error);
        }
    }

    // Fetch active sleep session
    async function fetchActiveSleepSession() {
        try {
            const response = await fetch('/api/sleep/active');
            if (response.ok) {
                activeSleepSession = await response.json();
                updateSleepUI();
            }
        } catch (error) {
            console.error('Error fetching active sleep session:', error);
        }
    }

    // Update sleep UI based on active session
    function updateSleepUI() {
        if (activeSleepSession && activeSleepSession.is_active) {
            startSleepBtn.style.display = 'none';
            stopSleepBtn.style.display = 'block';
            
            const startTime = new Date(activeSleepSession.start_time);
            sleepStatusDisplay.innerHTML = `
                <p style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">😴 Sleeping...</p>
                <p style="color: var(--text-muted);">Started at: ${startTime.toLocaleTimeString()}</p>
                <div id="sleep-timer" style="font-size: 2rem; font-weight: 800; color: var(--success); margin-top: 1rem; font-family: 'Courier New', monospace;">00:00:00</div>
            `;
            
            // Start timer to show elapsed sleep time
            startSleepTimer();
        } else {
            startSleepBtn.style.display = 'block';
            stopSleepBtn.style.display = 'none';
            sleepStatusDisplay.innerHTML = `<p style="font-size: 1.125rem; color: var(--text-muted);">No active sleep session</p>`;
            if (sleepTimer) clearInterval(sleepTimer);
        }
    }

    // Start sleep timer
    function startSleepTimer() {
        if (sleepTimer) clearInterval(sleepTimer);
        
        sleepTimer = setInterval(() => {
            if (activeSleepSession && activeSleepSession.start_time) {
                const elapsed = Math.floor((new Date() - new Date(activeSleepSession.start_time)) / 1000);
                const hours = Math.floor(elapsed / 3600);
                const minutes = Math.floor((elapsed % 3600) / 60);
                const seconds = elapsed % 60;
                
                const timerDisplay = document.getElementById('sleep-timer');
                if (timerDisplay) {
                    timerDisplay.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                }
            }
        }, 1000);
    }

    // Start sleep
    startSleepBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/sleep/start', { method: 'POST' });
            if (response.ok) {
                activeSleepSession = await response.json();
                updateSleepUI();
                alert('🌙 Sleep tracking started. Sleep well!');
            } else {
                const error = await response.json();
                alert(`❌ Error: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error starting sleep:', error);
            alert('❌ Error starting sleep session');
        }
    });

    // Stop sleep
    stopSleepBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/sleep/stop', { method: 'POST' });
            if (response.ok) {
                const completedSession = await response.json();
                activeSleepSession = null;
                updateSleepUI();
                
                // Display sleep quality analysis
                displaySleepQualityAnalysis(completedSession);
                
                // Refresh sleep history
                await fetchSleepHistory();
                
                alert(`✅ Sleep session ended!\n\n📊 Sleep Quality: ${Math.round(completedSession.sleep_quality_score * 100)}%\n💤 REM Cycles: ${completedSession.rem_cycle_count}`);
            } else {
                const error = await response.json();
                alert(`❌ Error: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error stopping sleep:', error);
            alert('❌ Error stopping sleep session');
        }
    });

    // Display sleep quality analysis
    function displaySleepQualityAnalysis(session) {
        sleepQualityCard.style.display = 'block';
        
        const hours = Math.floor(session.duration_minutes / 60);
        const minutes = session.duration_minutes % 60;
        
        document.getElementById('sleep-duration').textContent = `${hours}h ${minutes}m`;
        document.getElementById('sleep-quality-score').textContent = `${Math.round(session.sleep_quality_score * 100)}%`;
        document.getElementById('rem-cycles').textContent = session.rem_cycle_count;
        
        // Generate feedback based on sleep quality
        let feedback = '';
        if (session.sleep_quality_score >= 0.8) {
            feedback = '🌟 Excellent sleep! Your body is well-rested. Maintain this sleep schedule for optimal performance.';
        } else if (session.sleep_quality_score >= 0.6) {
            feedback = '✅ Good sleep quality. You should feel refreshed and ready for the day ahead.';
        } else if (session.sleep_quality_score >= 0.4) {
            feedback = '⚠️ Fair sleep quality. Consider adjusting your sleep schedule or environment for better rest.';
        } else {
            feedback = '❌ Poor sleep quality. The system will reduce your workload today to help you recover.';
        }
        
        document.getElementById('sleep-quality-feedback').textContent = feedback;
    }

    // Fetch sleep history
    async function fetchSleepHistory() {
        try {
            const response = await fetch('/api/sleep/history');
            const sessions = await response.json();
            
            // Display last 7 sleep sessions
            const sleepHistoryGrid = document.getElementById('sleep-history-grid');
            sleepHistoryGrid.innerHTML = '';
            
            sessions.slice(0, 7).forEach(session => {
                if (!session.is_active) {
                    const startDate = new Date(session.start_time);
                    const hours = Math.floor(session.duration_minutes / 60);
                    const minutes = session.duration_minutes % 60;
                    
                    const historyItem = document.createElement('div');
                    historyItem.className = 'sleep-history-item';
                    historyItem.innerHTML = `
                        <div class="history-date">${startDate.toLocaleDateString()}</div>
                        <div class="history-duration">${hours}h ${minutes}m</div>
                        <div class="history-quality">Quality: ${Math.round(session.sleep_quality_score * 100)}%</div>
                        <div class="history-rem">REM: ${session.rem_cycle_count} cycles</div>
                    `;
                    sleepHistoryGrid.appendChild(historyItem);
                }
            });
            
            // Initialize charts with real data
            initializeSleepCharts(sessions);
        } catch (error) {
            console.error('Error fetching sleep history:', error);
        }
    }

    // Initialize sleep charts with real data
    function initializeSleepCharts(sessions) {
        const last7Days = sessions.filter(s => !s.is_active).slice(0, 7).reverse();
        
        const dates = last7Days.map(s => new Date(s.start_time).toLocaleDateString('en-US', { weekday: 'short' }));
        const durations = last7Days.map(s => s.duration_minutes / 60);
        const qualities = last7Days.map(s => s.sleep_quality_score * 100);
        
        const ctx = document.getElementById('sleepTrendChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Sleep Duration (hours)',
                        data: durations,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        yAxisID: 'y',
                        tension: 0.4
                    },
                    {
                        label: 'Sleep Quality (%)',
                        data: qualities,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Duration (hours)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Quality (%)' },
                        max: 100
                    }
                }
            }
        });
        
        // Calculate sleep efficiency and consistency
        if (last7Days.length > 0) {
            const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
            const avgQuality = qualities.reduce((a, b) => a + b, 0) / qualities.length;
            
            // Sleep efficiency: how close to 7-9 hours
            const efficiency = avgDuration >= 7 && avgDuration <= 9 ? 100 : Math.max(0, 100 - Math.abs(avgDuration - 8) * 10);
            document.getElementById('sleep-efficiency').textContent = `${Math.round(efficiency)}%`;
            
            // Consistency: standard deviation of durations
            const variance = durations.reduce((sum, d) => sum + Math.pow(d - avgDuration, 2), 0) / durations.length;
            const stdDev = Math.sqrt(variance);
            const consistency = Math.max(0, 100 - stdDev * 20); // Penalize high variance
            document.getElementById('consistency-score').textContent = `${Math.round(consistency)}%`;
        }
    }

    // Initial load
    await updateSleepControlsBasedOnTime();
    await fetchActiveSleepSession();
    await fetchSleepHistory();

    // Refresh every 30 seconds
    setInterval(async () => {
        await updateSleepControlsBasedOnTime();
        await fetchActiveSleepSession();
    }, 30000);
});
