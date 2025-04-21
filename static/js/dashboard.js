document.addEventListener('DOMContentLoaded', function() {
    // Elemente
    const botStatusIndicator = document.getElementById('bot-status-indicator');
    const uptimeDisplay = document.getElementById('uptime-display');
    const lastRestartDisplay = document.getElementById('last-restart-display');
    const restartCountDisplay = document.getElementById('restart-count-display');
    const guildCountDisplay = document.getElementById('guild-count-display');
    const serverTimeDisplay = document.getElementById('server-time-display');
    const logsDisplay = document.getElementById('logs-display');
    const restartButton = document.getElementById('restart-button');
    const refreshLogsButton = document.getElementById('refresh-logs-button');

    // Funktion zum Abrufen und Aktualisieren des Bot-Status
    function updateBotStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // Status-Indikator aktualisieren
                botStatusIndicator.innerHTML = data.is_running 
                    ? '<span class="badge bg-success">Online</span>'
                    : '<span class="badge bg-danger">Offline</span>';
                
                // Andere Statusinformationen aktualisieren
                uptimeDisplay.textContent = data.uptime;
                lastRestartDisplay.textContent = data.last_restart;
                restartCountDisplay.textContent = data.restart_count;
                guildCountDisplay.textContent = data.bot_guilds;
                serverTimeDisplay.textContent = data.server_time;
            })
            .catch(error => {
                console.error('Error fetching bot status:', error);
                botStatusIndicator.innerHTML = '<span class="badge bg-warning">Unbekannt</span>';
            });
    }

    // Funktion zum Abrufen und Aktualisieren der Logs
    function updateLogs() {
        fetch('/api/logs')
            .then(response => response.json())
            .then(data => {
                if (data.logs && data.logs.length > 0) {
                    // Log-Zeilen zusammenfügen und Anzeige aktualisieren
                    const logText = data.logs.join('');
                    logsDisplay.textContent = logText;
                    // Automatisch zum unteren Rand scrollen
                    const logsContainer = logsDisplay.parentElement;
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                } else {
                    logsDisplay.textContent = 'Keine Logs verfügbar.';
                }
            })
            .catch(error => {
                console.error('Error fetching logs:', error);
                logsDisplay.textContent = 'Fehler beim Laden der Logs. Bitte versuche es erneut.';
            });
    }

    // Handler für den Bot-Neustart-Button
    restartButton.addEventListener('click', function() {
        if (confirm('Bist du sicher, dass du den Bot neu starten möchtest?')) {
            restartButton.disabled = true;
            restartButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Neustart läuft...';
            
            fetch('/api/restart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Bot restart response:', data);
                
                // Button nach 5 Sekunden wieder aktivieren
                setTimeout(() => {
                    restartButton.disabled = false;
                    restartButton.innerHTML = '<i class="fas fa-sync me-2"></i>Bot neustarten';
                    // Status nach dem Neustart aktualisieren
                    updateBotStatus();
                    updateLogs();
                }, 5000);
            })
            .catch(error => {
                console.error('Error restarting bot:', error);
                restartButton.disabled = false;
                restartButton.innerHTML = '<i class="fas fa-sync me-2"></i>Bot neustarten';
                alert('Fehler beim Neustarten des Bots. Details im Konsolenprotokoll.');
            });
        }
    });

    // Handler für den Log-Aktualisierung-Button
    refreshLogsButton.addEventListener('click', function() {
        refreshLogsButton.disabled = true;
        refreshLogsButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Aktualisiere...';
        
        updateLogs();
        
        setTimeout(() => {
            refreshLogsButton.disabled = false;
            refreshLogsButton.innerHTML = '<i class="fas fa-sync me-2"></i>Aktualisieren';
        }, 1000);
    });

    // Initiale Aktualisierung
    updateBotStatus();
    updateLogs();
    
    // Regelmäßige Aktualisierungen einrichten (alle 10 Sekunden)
    setInterval(updateBotStatus, 10000);
    setInterval(updateLogs, 30000);
});