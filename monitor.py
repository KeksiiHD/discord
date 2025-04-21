import logging
import asyncio
import threading
import time
import datetime
from bot import run_bot, disconnect_bot

logger = logging.getLogger(__name__)

class BotMonitor:
    """
    Monitors the Discord bot and restarts it if it crashes.
    """
    
    def __init__(self, bot, token):
        self.bot = bot
        self.token = token
        self.bot_thread = None
        self.running = False
        self.restart_count = 0
        self.start_time = None
        self.last_restart_time = None
        self.event_loop = None
        self.lock = threading.Lock()
    
    def start(self):
        """Start the bot and monitoring system"""
        with self.lock:
            if self.running:
                logger.warning("Bot is already running")
                return
            
            self.running = True
            self.start_time = datetime.datetime.now()
            self.start_bot()
            
            # Start the heartbeat check
            self._start_heartbeat_check()
            
            # Start the scheduled restart at 6:00 AM
            self._start_scheduled_restart()
    
    def start_bot(self):
        """Start the Discord bot in a new thread"""
        if not self.token:
            logger.error("Cannot start bot: Discord token is not set")
            return
        
        logger.info("Starting Discord bot...")
        
        # Create a new event loop for the bot
        self.event_loop = asyncio.new_event_loop()
        
        def bot_worker():
            """Worker function to run in the bot thread"""
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_until_complete(run_bot(self.bot, self.token))
        
        # Start the bot in a new thread
        self.bot_thread = threading.Thread(target=bot_worker)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        logger.info("Bot thread started")
    
    def restart_bot(self):
        """Restart the Discord bot"""
        with self.lock:
            logger.info("Restarting Discord bot...")
            self.restart_count += 1
            self.last_restart_time = datetime.datetime.now()
            
            # Disconnect the bot if it's running
            if self.bot_thread and self.bot_thread.is_alive():
                disconnect_bot(self.bot)
                
                # Wait for the thread to terminate
                self.bot_thread.join(timeout=5)
            
            # Start a new bot instance
            self.start_bot()
            logger.info("Bot restarted successfully")
    
    def _start_heartbeat_check(self):
        """Start a thread to periodically check if the bot is still running"""
        def heartbeat_worker():
            while self.running:
                time.sleep(30)  # Check every 30 seconds
                
                with self.lock:
                    # Check if the bot thread is still alive
                    if not self.bot_thread or not self.bot_thread.is_alive():
                        logger.warning("Bot thread is not running, attempting to restart...")
                        self.restart_bot()
                    
                    # Check if the bot is connected to Discord
                    if not self.is_bot_running():
                        logger.warning("Bot is not connected to Discord, attempting to restart...")
                        self.restart_bot()
        
        heartbeat_thread = threading.Thread(target=heartbeat_worker)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        logger.info("Heartbeat monitor started")
    
    def _start_scheduled_restart(self):
        """Start a thread to restart the bot at 6:00 AM every day"""
        def schedule_worker():
            while self.running:
                # Get current time
                now = datetime.datetime.now()
                
                # Calculate time until next 6:00 AM
                if now.hour >= 6:
                    # If it's already past 6 AM, schedule for next day
                    next_run = now.replace(day=now.day+1, hour=6, minute=0, second=0, microsecond=0)
                else:
                    # If it's before 6 AM, schedule for today
                    next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
                
                # Calculate seconds until next run
                seconds_until_restart = (next_run - now).total_seconds()
                
                logger.info(f"Scheduled restart in {seconds_until_restart} seconds (at 6:00 AM)")
                
                # Sleep until the scheduled time
                time.sleep(seconds_until_restart)
                
                # Perform restart
                logger.info("Performing scheduled daily restart at 6:00 AM")
                self.restart_bot()
        
        schedule_thread = threading.Thread(target=schedule_worker)
        schedule_thread.daemon = True
        schedule_thread.start()
        logger.info("Scheduled restart at 6:00 AM configured")
    
    def stop(self):
        """Stop the bot and monitoring system"""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            
            # Disconnect the bot
            disconnect_bot(self.bot)
            
            # Wait for the thread to terminate
            if self.bot_thread:
                self.bot_thread.join(timeout=5)
            
            logger.info("Bot monitor stopped")
    
    def is_bot_running(self):
        """Check if the bot is connected to Discord"""
        return self.bot.is_ready() if hasattr(self.bot, 'is_ready') else False
    
    def get_uptime(self):
        """Get the bot's uptime as a formatted string"""
        if not self.start_time:
            return "Not started"
        
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    
    def get_last_restart_time(self):
        """Get the time of the last restart"""
        if not self.last_restart_time:
            return "Never restarted"
        return self.last_restart_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_restart_count(self):
        """Get the number of times the bot has been restarted"""
        return self.restart_count
    
    def get_guild_count(self):
        """Get the number of guilds (servers) the bot is connected to"""
        if hasattr(self.bot, 'guilds'):
            return len(self.bot.guilds)
        return 0
