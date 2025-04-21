import os
import logging
import threading
import time
import datetime
import flask
from flask import Flask, render_template, jsonify
from reaktions_bot_vollversion import create_discord_bot, BotMonitor

# Konfiguriere Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discord_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Erstelle Flask-App
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Hole Discord-Token aus Umgebungsvariablen
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN ist nicht konfiguriert!")

# Erstelle Discord-Bot
discord_bot = create_discord_bot()

# Initialisiere den Bot-Monitor
bot_monitor = BotMonitor(discord_bot, DISCORD_TOKEN)

# Starte den Bot in einem separaten Thread
def start_bot():
    def run_bot_monitor():
        logger.info("Starte Discord-Bot-Monitor...")
        bot_monitor.start()
    
    # Starte den Bot-Monitor in einem separaten Thread
    bot_thread = threading.Thread(target=run_bot_monitor)
    bot_thread.daemon = True
    bot_thread.start()
    logger.info("Bot-Monitor-Thread gestartet")

# Initialisiere den Bot beim Start
with app.app_context():
    start_bot()

# Routen
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API-Endpunkt zum Abrufen des Bot-Status"""
    status_data = {
        'is_running': bot_monitor.is_bot_running(),
        'uptime': bot_monitor.get_uptime(),
        'last_restart': bot_monitor.get_last_restart_time(),
        'restart_count': bot_monitor.get_restart_count(),
        'server_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'bot_guilds': bot_monitor.get_guild_count(),
    }
    return jsonify(status_data)

@app.route('/api/restart', methods=['POST'])
def restart_bot():
    """API-Endpunkt zum manuellen Neustarten des Bots"""
    logger.info("Manueller Neustart über API angefordert")
    bot_monitor.restart_bot()
    return jsonify({'status': 'wird neu gestartet'})

@app.route('/api/logs')
def get_logs():
    """API-Endpunkt zum Abrufen der neuesten Logs"""
    try:
        with open('discord_bot.log', 'r') as log_file:
            # Hole die letzten 50 Zeilen
            lines = log_file.readlines()[-50:]
            return jsonify({'logs': lines})
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Log-Datei: {e}")
        return jsonify({'error': 'Fehler beim Lesen der Logs', 'logs': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)