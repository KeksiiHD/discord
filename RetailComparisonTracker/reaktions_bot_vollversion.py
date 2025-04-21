import discord
from discord.ext import commands
import asyncio
import logging
import threading
import time
import datetime
import traceback
import sys
import os

# Logging einrichten
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('discord_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Speichert die zuletzt gesendete Liste zum Bearbeiten
message_cache = {}
status_emojis = {"✅", "❌"}

# ======================
# BOT ERSTELLEN
# ======================

def create_discord_bot():
    """Factory-Funktion zum Erstellen einer neuen Discord-Bot-Instanz"""
    
    # Bot mit dem Prefix '!' erstellen
    intents = discord.Intents.default()
    intents.message_content = True  # Für das Empfangen von Nachrichteninhalten notwendig
    intents.reactions = True  # Für die Reaktionserkennung notwendig
    intents.messages = True   # Für Nachrichtenereignisse notwendig
    intents.members = True    # Für den Zugriff auf Mitglieder notwendig
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        """Event, das ausgelöst wird, wenn der Bot verbunden und bereit ist"""
        logger.info(f'Bot verbunden als {bot.user.name} (ID: {bot.user.id})')
        logger.info(f'Verbunden mit {len(bot.guilds)} Servern')
        
        # Aktivitätsstatus des Bots setzen
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Teilnehmerlisten | !liste"
        ))
    
    @bot.event
    async def on_guild_join(guild):
        """Event, das ausgelöst wird, wenn der Bot einem neuen Server beitritt"""
        logger.info(f'Bot ist einem neuen Server beigetreten: {guild.name} (ID: {guild.id})')
    
    @bot.event
    async def on_command_error(ctx, error):
        """Event, das ausgelöst wird, wenn ein Befehl einen Fehler verursacht"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Befehl nicht gefunden. Nutze `!help` um verfügbare Befehle zu sehen.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Fehlendes Argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Ungültiges Argument: {error}")
        else:
            error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            logger.error(f'Command error: {error_traceback}')
            await ctx.send("Bei der Ausführung des Befehls ist ein Fehler aufgetreten.")
    
    @bot.command(name="ping")
    async def ping(ctx):
        """Einfacher Befehl zum Überprüfen, ob der Bot reagiert"""
        latency = round(bot.latency * 1000)
        await ctx.send(f"Pong! Latenz: {latency}ms")
    
    @bot.command(name="status")
    async def status(ctx):
        """Befehl zum Anzeigen von Bot-Statusinformationen"""
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.green(),
            description="Bot ist aktiv und funktioniert."
        )
        embed.add_field(name="Latenz", value=f"{round(bot.latency * 1000)}ms")
        embed.add_field(name="Server", value=str(len(bot.guilds)))
        embed.add_field(name="API Version", value=discord.__version__)
        await ctx.send(embed=embed)
    
    @bot.command()
    async def liste(ctx, *, text=""):
        """Erstellt eine Teilnehmerliste mit X hinter jedem Namen (durch Kommas getrennt)"""
        # Entferne führende/nachfolgende Leerzeichen und teile nach Kommas
        namen = [name.strip() for name in text.split(",") if name.strip()]
        
        if not namen:
            await ctx.send("Bitte gib mindestens einen Namen an! Beispiel: `!liste Felix Westfield, Mirella Sterling, John Paul Jones`")
            return
        
        # Erstelle ein Embed für die Liste
        embed = discord.Embed(
            title="Teilnehmerliste",
            description="Reagiere mit ✅ oder ❌ um deinen Status zu ändern",
            color=discord.Color.blue()
        )
        
        # Suche nach Mitgliedern im Server, die den genannten Namen entsprechen
        guild = ctx.guild
        status_list = []
        
        for name in namen:
            # Versuche den Benutzer zu finden (nach Nickname oder Username)
            member = None
            for m in guild.members:
                if m.display_name.lower() == name.lower() or m.name.lower() == name.lower():
                    member = m
                    break
            
            if member:
                # Nutze die Hauptrolle des Mitglieds für die Farbe
                role_color = member.color.value if member.color.value != 0 else None
                status_list.append({"name": name, "member_id": member.id, "color": role_color})
            else:
                # Kein passendes Mitglied gefunden
                status_list.append({"name": name, "member_id": None, "color": None})
        
        # Füge jeden Namen zur Embed-Nachricht hinzu
        for status in status_list:
            name = status["name"]
            if status["color"]:
                # Wenn eine Farbe vorhanden ist, formatiere den Namen mit der Hex-Farbe
                hex_color = f"#{status['color']:06x}"
                embed.add_field(
                    name=f"{name}",
                    value=f"❌ Status",
                    inline=False
                )
            else:
                # Ohne Farbe
                embed.add_field(
                    name=f"{name}",
                    value=f"❌ Status",
                    inline=False
                )
        
        # Sende die Embed-Nachricht
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        # Speichere die Nachricht und die Namen
        message_cache[message.id] = {
            "author_id": ctx.author.id,
            "user_message_id": ctx.message.id,  # Speichere die ursprüngliche Nachricht-ID
            "names": namen,
            "status_list": status_list  # Speichere die Liste mit Farben
        }
        logger.info(f"Neue Liste erstellt von {ctx.author.name} mit {len(namen)} Namen")

    @bot.event
    async def on_message_edit(before, after):
        """Event, der ausgelöst wird, wenn eine Nachricht bearbeitet wurde"""
        # Wir müssen prüfen, ob diese Benutzer-Nachricht mit einer Bot-Liste verbunden ist
        # Durchsuche den Cache nach der Benutzer-Nachricht-ID
        bot_message_id = None
        for msg_id, data in message_cache.items():
            if data.get("user_message_id") == before.id:
                bot_message_id = msg_id
                break
                
        if not bot_message_id:
            return
        
        # Ignoriere Nachrichten, die vom Bot stammen (um Endlosschleifen zu vermeiden)
        if before.author.id == bot.user.id:
            return
        
        # Die Nachricht kommt vom Benutzer und ist mit einer Liste verknüpft
        logger.info(f"Liste bearbeitet von {before.author.name}")
        
        # Finde die Bot-Nachricht (die Teilnehmerliste)
        channel = before.channel
        bot_message = await channel.fetch_message(bot_message_id)
        
        # Analysiere den neuen Inhalt der Benutzernachricht
        # Entferne den Befehl "!liste" und teile nach Kommas
        befehl_text = after.content
        if befehl_text.startswith("!liste"):
            befehl_text = befehl_text[6:].strip()
            
        # Teile bei Kommas und entferne Leerzeichen
        neue_namen = [name.strip() for name in befehl_text.split(",") if name.strip()]
        
        if not neue_namen:
            return
        
        # Prüfe, ob die Nachricht ein Embed ist
        if bot_message.embeds:
            # Wir haben ein Embed-Format
            embed = bot_message.embeds[0]
            
            # Bestehende Namen und ihre Status aus den Embed-Feldern extrahieren
            bestehende_namen = []
            for field in embed.fields:
                bestehende_namen.append(field.name)
                
            # Finde Namen, die hinzugefügt werden sollen
            hinzugefuegte_namen = [name for name in neue_namen if name not in bestehende_namen]
            
            # Finde Namen, die entfernt werden sollen
            entfernte_namen = [name for name in bestehende_namen if name not in neue_namen]
            
            if not hinzugefuegte_namen and not entfernte_namen:
                # Keine Änderungen notwendig
                return
                
            # Erstelle ein neues Embed mit aktualisierten Feldern
            new_embed = discord.Embed(
                title=embed.title,
                description=embed.description,
                color=embed.color
            )
            
            # Behalte nur die Felder, die nicht entfernt werden sollen
            for field in embed.fields:
                if field.name not in entfernte_namen:
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            # Füge neue Namen hinzu und suche nach passenden Mitgliedern für Rollenfarben
            guild = channel.guild
            for name in hinzugefuegte_namen:
                # Versuche den Benutzer zu finden
                member = None
                for m in guild.members:
                    if m.display_name.lower() == name.lower() or m.name.lower() == name.lower():
                        member = m
                        break
                
                if member:
                    # Mit Rollenfarbe
                    role_color = member.color.value if member.color.value != 0 else None
                    new_embed.add_field(
                        name=name,
                        value="❌ Status",
                        inline=False
                    )
                else:
                    # Ohne Rollenfarbe
                    new_embed.add_field(
                        name=name,
                        value="❌ Status",
                        inline=False
                    )
            
            # Aktualisiere den Cache mit aktuellen Namen
            alle_namen = [name for name in bestehende_namen if name not in entfernte_namen] + hinzugefuegte_namen
            message_cache[bot_message_id]["names"] = alle_namen
            
            # Aktualisiere die Bot-Nachricht
            await bot_message.edit(embed=new_embed)
            
            log_message = []
            if hinzugefuegte_namen:
                log_message.append(f"Hinzugefügt: {', '.join(hinzugefuegte_namen)}")
            if entfernte_namen:
                log_message.append(f"Entfernt: {', '.join(entfernte_namen)}")
                
            logger.info(f"Liste aktualisiert (Embed) - {' | '.join(log_message)}")
            
        else:
            # Fallback für das alte Text-Format
            # Bestehende Namen aus der Bot-Nachricht extrahieren
            bestehende_namen = []
            bestehende_status = {}
            lines = bot_message.content.split("\n")
            
            for line in lines:
                if line and " " in line:  # Überprüfe, ob die Zeile ein Format "Name Status" hat
                    name, status = line.rsplit(" ", 1)
                    name = name.strip()
                    bestehende_namen.append(name)
                    bestehende_status[name] = status
                    
            # Finde Namen, die hinzugefügt werden sollen
            hinzugefuegte_namen = [name for name in neue_namen if name not in bestehende_namen]
            
            # Finde Namen, die entfernt werden sollen (in der alten Liste aber nicht in der neuen)
            entfernte_namen = [name for name in bestehende_namen if name not in neue_namen]
            
            if not hinzugefuegte_namen and not entfernte_namen:
                # Keine Änderungen notwendig
                return
            
            # Erstelle neue Liste basierend auf aktuellen Namen
            new_lines = []
            
            # Füge alle Namen hinzu, die NICHT entfernt werden sollen
            for name in bestehende_namen:
                if name not in entfernte_namen:
                    new_lines.append(f"{name} {bestehende_status[name]}")
                    
            # Füge neue Namen mit X hinzu
            for name in hinzugefuegte_namen:
                new_lines.append(f"{name} ❌")
            
            # Aktualisiere den Cache mit aktuellen Namen
            alle_namen = [name for name in bestehende_namen if name not in entfernte_namen] + hinzugefuegte_namen
            message_cache[bot_message_id]["names"] = alle_namen
            
            # Aktualisiere die Bot-Nachricht
            await bot_message.edit(content="\n".join(new_lines))
            
            log_message = []
            if hinzugefuegte_namen:
                log_message.append(f"Hinzugefügt: {', '.join(hinzugefuegte_namen)}")
            if entfernte_namen:
                log_message.append(f"Entfernt: {', '.join(entfernte_namen)}")
                
            logger.info(f"Liste aktualisiert (Text) - {' | '.join(log_message)}")
    
    @bot.event
    async def on_raw_reaction_add(payload):
        if payload.user_id == bot.user.id:
            return

        if payload.message_id not in message_cache:
            return

        emoji = payload.emoji.name
        if emoji not in status_emojis:
            return

        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        entry = message_cache[payload.message_id]
        user_display = member.display_name

        # Prüfe, ob die Nachricht ein Embed ist
        if message.embeds:
            # Wir haben ein Embed
            embed = message.embeds[0]
            fields = embed.fields
            new_fields = []
            status_updated = False

            # Finde das Field mit dem passenden Namen
            for field in fields:
                field_name = field.name
                field_value = field.value
                
                # Prüfe, ob das Field zum aktuellen Benutzer gehört
                if field_name == user_display or any(
                    name == user_display for name in entry.get("names", [])
                ):
                    # Aktualisiere den Status mit dem neuen Emoji
                    new_value = f"{emoji} Status"
                    new_fields.append(
                        {'name': field_name, 'value': new_value, 'inline': field.inline}
                    )
                    status_updated = True
                    logger.info(f"Status für {field_name} geändert zu {emoji}")
                else:
                    # Behalte das bestehende Field bei
                    new_fields.append(
                        {'name': field_name, 'value': field_value, 'inline': field.inline}
                    )
            
            if status_updated:
                # Erstelle ein neues Embed mit den aktualisierten Fields
                new_embed = discord.Embed(
                    title=embed.title,
                    description=embed.description,
                    color=embed.color
                )
                
                # Füge die Fields hinzu
                for field in new_fields:
                    new_embed.add_field(
                        name=field['name'],
                        value=field['value'],
                        inline=field['inline']
                    )
                
                # Aktualisiere die Nachricht mit dem neuen Embed
                await message.edit(embed=new_embed)
        else:
            # Fallback für nicht-Embed-Nachrichten (altes Format)
            try:
                # Aktualisiere nur, wenn der Name in der Liste steht
                lines = message.content.split("\n")
                new_lines = []

                for line in lines:
                    if " " in line:  # Überprüfe, ob die Zeile ein Format "Name Status" hat
                        name, current_status = line.rsplit(" ", 1)
                        if name == user_display:
                            new_lines.append(f"{name} {emoji}")
                            logger.info(f"Status für {name} geändert zu {emoji}")
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)

                await message.edit(content="\n".join(new_lines))
            except Exception as e:
                logger.error(f"Fehler beim Aktualisieren der Nachricht: {e}")
    
    return bot

# ======================
# BOT AUSFÜHREN
# ======================

async def run_bot(bot, token):
    """Discord-Bot mit dem angegebenen Token ausführen"""
    try:
        logger.info("Versuche, Verbindung zu Discord herzustellen...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Ungültiges Discord-Token. Bitte überprüfe deine Umgebungsvariablen.")
    except Exception as e:
        logger.error(f"Fehler beim Starten des Bots: {e}")
        traceback.print_exc()

def disconnect_bot(bot):
    """Bot trennen und bereinigen"""
    if bot and bot.is_ready():
        logger.info("Trenne Bot...")
        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
        logger.info("Bot getrennt")

# ======================
# MONITOR-KLASSE
# ======================

class BotMonitor:
    """
    Überwacht den Discord-Bot und startet ihn neu, wenn er abstürzt.
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
        """Starte den Bot und das Überwachungssystem"""
        with self.lock:
            if self.running:
                logger.warning("Bot läuft bereits")
                return
            
            self.running = True
            self.start_time = datetime.datetime.now()
            self.start_bot()
            
            # Starte die Herzschlagprüfung
            self._start_heartbeat_check()
            
            # Starte den geplanten Neustart um 6:00 Uhr
            self._start_scheduled_restart()
    
    def start_bot(self):
        """Starte den Discord-Bot in einem neuen Thread"""
        if not self.token:
            logger.error("Bot kann nicht gestartet werden: Discord-Token ist nicht gesetzt")
            return
        
        logger.info("Starte Discord-Bot...")
        
        # Erstelle einen neuen Event-Loop für den Bot
        self.event_loop = asyncio.new_event_loop()
        
        def bot_worker():
            """Worker-Funktion für den Bot-Thread"""
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_until_complete(run_bot(self.bot, self.token))
        
        # Starte den Bot in einem neuen Thread
        self.bot_thread = threading.Thread(target=bot_worker)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        logger.info("Bot-Thread gestartet")
    
    def restart_bot(self):
        """Starte den Discord-Bot neu"""
        with self.lock:
            logger.info("Starte Discord-Bot neu...")
            self.restart_count += 1
            self.last_restart_time = datetime.datetime.now()
            
            # Trenne den Bot, wenn er läuft
            if self.bot_thread and self.bot_thread.is_alive():
                disconnect_bot(self.bot)
                
                # Warte, bis der Thread terminiert ist
                self.bot_thread.join(timeout=5)
            
            # Starte eine neue Bot-Instanz
            self.start_bot()
            logger.info("Bot erfolgreich neu gestartet")
    
    def _start_heartbeat_check(self):
        """Starte einen Thread zur regelmäßigen Überprüfung, ob der Bot noch läuft"""
        def heartbeat_worker():
            while self.running:
                time.sleep(30)  # Prüfe alle 30 Sekunden
                
                with self.lock:
                    # Prüfe, ob der Bot-Thread noch lebt
                    if not self.bot_thread or not self.bot_thread.is_alive():
                        logger.warning("Bot-Thread läuft nicht, versuche neu zu starten...")
                        self.restart_bot()
                    
                    # Prüfe, ob der Bot mit Discord verbunden ist
                    if not self.is_bot_running():
                        logger.warning("Bot ist nicht mit Discord verbunden, versuche neu zu starten...")
                        self.restart_bot()
        
        heartbeat_thread = threading.Thread(target=heartbeat_worker)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        logger.info("Herzschlag-Monitor gestartet")
    
    def _start_scheduled_restart(self):
        """Starte einen Thread, um den Bot jeden Tag um 6:00 Uhr neu zu starten"""
        def schedule_worker():
            while self.running:
                # Aktuelle Zeit holen
                now = datetime.datetime.now()
                
                # Zeit bis zum nächsten 6:00 Uhr berechnen
                if now.hour >= 6:
                    # Wenn es bereits nach 6 Uhr ist, für den nächsten Tag planen
                    next_run = now.replace(day=now.day+1, hour=6, minute=0, second=0, microsecond=0)
                else:
                    # Wenn es vor 6 Uhr ist, für heute planen
                    next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
                
                # Sekunden bis zum nächsten Lauf berechnen
                seconds_until_restart = (next_run - now).total_seconds()
                
                logger.info(f"Geplanter Neustart in {seconds_until_restart} Sekunden (um 6:00 Uhr)")
                
                # Schlafe bis zur geplanten Zeit
                time.sleep(seconds_until_restart)
                
                # Führe Neustart durch
                logger.info("Führe geplanten täglichen Neustart um 6:00 Uhr durch")
                self.restart_bot()
        
        schedule_thread = threading.Thread(target=schedule_worker)
        schedule_thread.daemon = True
        schedule_thread.start()
        logger.info("Geplanter Neustart um 6:00 Uhr konfiguriert")
    
    def stop(self):
        """Stoppe den Bot und das Überwachungssystem"""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            
            # Trenne den Bot
            disconnect_bot(self.bot)
            
            # Warte, bis der Thread terminiert ist
            if self.bot_thread:
                self.bot_thread.join(timeout=5)
            
            logger.info("Bot-Monitor gestoppt")
    
    def is_bot_running(self):
        """Prüfe, ob der Bot mit Discord verbunden ist"""
        return self.bot.is_ready() if hasattr(self.bot, 'is_ready') else False
    
    def get_uptime(self):
        """Erhalte die Uptime des Bots als formatierten String"""
        if not self.start_time:
            return "Nicht gestartet"
        
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    
    def get_last_restart_time(self):
        """Erhalte die Zeit des letzten Neustarts"""
        if not self.last_restart_time:
            return "Nie neu gestartet"
        return self.last_restart_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_restart_count(self):
        """Erhalte die Anzahl der Bot-Neustarts"""
        return self.restart_count
    
    def get_guild_count(self):
        """Erhalte die Anzahl der Server, mit denen der Bot verbunden ist"""
        if hasattr(self.bot, 'guilds'):
            return len(self.bot.guilds)
        return 0

# ======================
# HAUPTPROGRAMM
# ======================

# Wenn diese Datei direkt ausgeführt wird
if __name__ == "__main__":
    # Token aus Umgebungsvariablen verwenden
    TOKEN = os.environ.get("DISCORD_TOKEN")
    
    # Bot erstellen
    discord_bot = create_discord_bot()
    
    # Bot-Monitor erstellen und starten
    monitor = BotMonitor(discord_bot, TOKEN)
    
    try:
        print("Starte Discord Bot...")
        monitor.start()
        
        # Halte das Hauptprogramm am Leben
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Beende Bot...")
        monitor.stop()
        print("Bot beendet.")
    except Exception as e:
        print(f"Fehler: {e}")
        monitor.stop()