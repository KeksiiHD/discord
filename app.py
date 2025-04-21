import os
import logging
import threading
import datetime
import time
from flask import Flask, render_template, jsonify
from monitor import BotMonitor
from bot import create_discord_bot

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discord_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Get Discord token from environment or use default
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
logger.info("Discord token configured from environment")

# Create Discord bot
discord_bot = create_discord_bot()

# Initialize the bot monitor
bot_monitor = BotMonitor(discord_bot, DISCORD_TOKEN)

# Start the bot in a separate thread
def start_bot():
    def run_bot_monitor():
        logger.info("Starting Discord bot monitor...")
        bot_monitor.start()
    
    # Start the bot monitor in a separate thread
    bot_thread = threading.Thread(target=run_bot_monitor)
    bot_thread.daemon = True
    bot_thread.start()
    logger.info("Bot monitor thread started")

# Initialize the bot on startup
with app.app_context():
    start_bot()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API endpoint for getting bot status"""
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
    """API endpoint for manually restarting the bot"""
    logger.info("Manual restart requested via API")
    bot_monitor.restart_bot()
    return jsonify({'status': 'restarting'})

@app.route('/api/logs')
def get_logs():
    """API endpoint for fetching recent logs"""
    try:
        with open('discord_bot.log', 'r') as log_file:
            # Get the last 50 lines
            lines = log_file.readlines()[-50:]
            return jsonify({'logs': lines})
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return jsonify({'error': 'Failed to read logs', 'logs': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
