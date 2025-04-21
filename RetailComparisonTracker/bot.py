import discord
import logging
from discord.ext import commands
import asyncio
import traceback
import sys

logger = logging.getLogger(__name__)

# Speichert die zuletzt gesendete Liste zum Bearbeiten
message_cache = {}
status_emojis = {"✅", "❌"}

def create_discord_bot():
    """Factory function to create a new Discord bot instance"""
    
    # Create a bot instance with command prefix '!'
    intents = discord.Intents.default()
    intents.message_content = True  # Required to receive message content
    intents.reactions = True  # Required for reaction handling
    intents.messages = True   # Required for message events
    intents.members = True    # Required for member access 
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        """Event that triggers when the bot is connected and ready"""
        logger.info(f'Bot connected as {bot.user.name} (ID: {bot.user.id})')
        logger.info(f'Connected to {len(bot.guilds)} guilds')
        
        # Set bot activity status
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Teilnehmerlisten | !liste"
        ))
    
    @bot.event
    async def on_guild_join(guild):
        """Event that triggers when the bot joins a new server"""
        logger.info(f'Bot joined new guild: {guild.name} (ID: {guild.id})')
    
    @bot.event
    async def on_command_error(ctx, error):
        """Event that triggers when a command raises an error"""
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
        """Simple command to check if the bot is responsive"""
        latency = round(bot.latency * 1000)
        await ctx.send(f"Pong! Latenz: {latency}ms")
    
    @bot.command(name="status")
    async def status(ctx):
        """Command to show bot status information"""
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
        """Erstellt eine Dienstübersicht mit Status-Emoji hinter jedem Namen (durch Kommas getrennt)"""
        # Entferne führende/nachfolgende Leerzeichen und teile nach Kommas
        namen = [name.strip() for name in text.split(",") if name.strip()]
        
        if not namen:
            await ctx.send("Bitte gib mindestens einen Namen an! Beispiel: `!liste Felix Westfield, Mirella Sterling, John Paul Jones`")
            return
        
        # Erstelle ein Embed für die Dienstübersicht
        embed = discord.Embed(
            title="Dienstübersicht",
            description="Reagiere mit ✅ oder ❌ um deinen Status zu ändern",
            color=discord.Color.blue()
        )
        
        # Definiere die Rollenreihenfolge
        rollen_reihenfolge = ["Chefarzt", "Praxisleitung", "Arzt", "Ausbildung", "Praktikant"]
        
        # Initialisiere ein Dictionary für die Kategorisierung nach Rollen
        rollen_kategorien = {rolle: [] for rolle in rollen_reihenfolge}
        andere_kategorie = []  # Für Mitglieder ohne spezifische Rolle
        
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
                # Bestimme die höchste Rolle des Mitglieds aus unserer Reihenfolge
                member_rolle = None
                for rolle in rollen_reihenfolge:
                    if any(r.name == rolle for r in member.roles):
                        member_rolle = rolle
                        break
                
                # Nutze die Hauptrolle des Mitglieds für die Farbe
                role_color = member.color.value if member.color.value != 0 else None
                
                # Füge das Mitglied zur entsprechenden Kategorie hinzu
                member_info = {
                    "name": name, 
                    "member_id": member.id, 
                    "color": role_color,
                    "status": "❌"
                }
                status_list.append(member_info)
                
                if member_rolle:
                    rollen_kategorien[member_rolle].append(member_info)
                else:
                    andere_kategorie.append(member_info)
            else:
                # Kein passendes Mitglied gefunden
                member_info = {
                    "name": name, 
                    "member_id": None, 
                    "color": None,
                    "status": "❌"
                }
                status_list.append(member_info)
                andere_kategorie.append(member_info)
        
        # Füge die Namen nach Kategorien sortiert hinzu
        for rolle in rollen_reihenfolge:
            mitglieder = rollen_kategorien[rolle]
            if mitglieder:
                # Füge eine Überschrift für die Rollenkategorie hinzu
                embed.add_field(
                    name=f"__**{rolle}**__",
                    value="\u200b",  # Zero-width space als Platzhalter
                    inline=False
                )
                
                # Füge die Mitglieder dieser Kategorie hinzu
                for member_info in mitglieder:
                    name = member_info["name"]
                    status = member_info["status"]
                    embed.add_field(
                        name=f"{name} {status}",
                        value="\u200b",  # Zero-width space als Platzhalter
                        inline=True
                    )
        
        # Füge Mitglieder ohne spezifische Rolle hinzu
        if andere_kategorie:
            embed.add_field(
                name="__**Andere**__",
                value="\u200b",  # Zero-width space als Platzhalter
                inline=False
            )
            
            for member_info in andere_kategorie:
                name = member_info["name"]
                status = member_info["status"]
                embed.add_field(
                    name=f"{name} {status}",
                    value="\u200b",  # Zero-width space als Platzhalter
                    inline=True
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
            "status_list": status_list,  # Speichere die Liste mit Farben
            "rollen_kategorien": rollen_kategorien,
            "andere_kategorie": andere_kategorie
        }
        logger.info(f"Neue Dienstübersicht erstellt von {ctx.author.name} mit {len(namen)} Namen")

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
            
            # Definiere die Rollenreihenfolge
            rollen_reihenfolge = ["Chefarzt", "Praxisleitung", "Arzt", "Ausbildung", "Praktikant"]
            
            # Prüfe, ob wir das neue kategorisierte Format haben
            is_categorized = any(field.name.startswith("__**") and field.name.endswith("**__") for field in embed.fields)
            
            if is_categorized:
                # Wir haben das kategorisierte Format
                # Sammle alle Namen und deren Status/Kategorie
                all_entries = []
                category = None
                
                for field in embed.fields:
                    if field.name.startswith("__**") and field.name.endswith("**__"):
                        # Das ist eine Kategorie-Überschrift
                        category = field.name.strip("_*")
                    elif field.value == "\u200b":  # Zero-width space
                        # Das ist ein Mitglied
                        name = field.name
                        
                        # Extrahiere Name und Status
                        if " " in name and name.split(" ")[-1] in status_emojis:
                            name_parts = name.split(" ")
                            status = name_parts[-1]
                            name_without_status = " ".join(name_parts[:-1])
                        else:
                            name_without_status = name
                            status = "❌"  # Standard-Status, falls keiner vorhanden
                        
                        all_entries.append({
                            'name': name_without_status,
                            'status': status,
                            'category': category,
                            'inline': field.inline
                        })
                
                # Extrahiere alle Namen ohne Status
                bestehende_namen = [entry['name'] for entry in all_entries]
                
                # Finde Namen, die hinzugefügt werden sollen
                hinzugefuegte_namen = [name for name in neue_namen if name not in bestehende_namen]
                
                # Finde Namen, die entfernt werden sollen
                entfernte_namen = [name for name in bestehende_namen if name not in neue_namen]
                
                if not hinzugefuegte_namen and not entfernte_namen:
                    # Keine Änderungen notwendig
                    return
                
                # Entferne die zu entfernenden Namen aus der Liste
                all_entries = [entry for entry in all_entries if entry['name'] not in entfernte_namen]
                
                # Füge neue Namen hinzu
                guild = channel.guild
                
                for name in hinzugefuegte_namen:
                    # Versuche den Benutzer zu finden
                    member = None
                    for m in guild.members:
                        if m.display_name.lower() == name.lower() or m.name.lower() == name.lower():
                            member = m
                            break
                    
                    if member:
                        # Bestimme die höchste Rolle des Mitglieds aus unserer Reihenfolge
                        member_rolle = None
                        for rolle in rollen_reihenfolge:
                            if any(r.name == rolle for r in member.roles):
                                member_rolle = rolle
                                break
                        
                        all_entries.append({
                            'name': name,
                            'status': "❌",
                            'category': member_rolle or "Andere",
                            'inline': True
                        })
                    else:
                        # Kein passendes Mitglied gefunden
                        all_entries.append({
                            'name': name,
                            'status': "❌",
                            'category': "Andere",
                            'inline': True
                        })
                
                # Erstelle ein neues Embed mit den aktualisierten Einträgen
                new_embed = discord.Embed(
                    title=embed.title,
                    description=embed.description,
                    color=embed.color
                )
                
                # Gruppiere Einträge nach Kategorie
                entries_by_category = {}
                for entry in all_entries:
                    category = entry['category']
                    if category not in entries_by_category:
                        entries_by_category[category] = []
                    entries_by_category[category].append(entry)
                
                # Füge Kategorien und Einträge hinzu
                # Zunächst die definierten Rollen in der richtigen Reihenfolge
                for rolle in rollen_reihenfolge:
                    if rolle in entries_by_category and entries_by_category[rolle]:
                        # Füge die Kategorie-Überschrift hinzu
                        new_embed.add_field(
                            name=f"__**{rolle}**__",
                            value="\u200b",  # Zero-width space als Platzhalter
                            inline=False
                        )
                        
                        # Füge alle Einträge dieser Kategorie hinzu
                        for entry in entries_by_category[rolle]:
                            new_embed.add_field(
                                name=f"{entry['name']} {entry['status']}",
                                value="\u200b",  # Zero-width space als Platzhalter
                                inline=entry['inline']
                            )
                
                # Dann alle anderen Kategorien
                for category, entries in entries_by_category.items():
                    if category not in rollen_reihenfolge and entries:
                        # Füge die Kategorie-Überschrift hinzu
                        new_embed.add_field(
                            name=f"__**{category}**__",
                            value="\u200b",  # Zero-width space als Platzhalter
                            inline=False
                        )
                        
                        # Füge alle Einträge dieser Kategorie hinzu
                        for entry in entries:
                            new_embed.add_field(
                                name=f"{entry['name']} {entry['status']}",
                                value="\u200b",  # Zero-width space als Platzhalter
                                inline=entry['inline']
                            )
            else:
                # Wir haben das alte Format (ohne Kategorien)
                
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
            
            # Definiere die Rollenreihenfolge für die Neuorganisation
            rollen_reihenfolge = ["Chefarzt", "Praxisleitung", "Arzt", "Ausbildung", "Praktikant"]
            
            # Prüfe, ob wir das neue oder alte Embed-Format haben
            if "__**Chefarzt**__" in [field.name for field in embed.fields]:
                # Wir haben das neue kategorisierte Format
                
                # Sammle alle Namen und ihre Werte
                all_entries = []
                category = None
                
                for field in embed.fields:
                    if field.name.startswith("__**") and field.name.endswith("**__"):
                        # Das ist eine Kategorie-Überschrift
                        category = field.name.strip("_*")
                    elif field.value == "\u200b":  # Zero-width space
                        # Das ist ein Mitglied
                        name = field.name
                        
                        # Extrahiere Name und aktuellen Status
                        name_parts = name.split(" ")
                        if len(name_parts) > 1 and name_parts[-1] in status_emojis:
                            name_without_status = " ".join(name_parts[:-1])
                            current_status = name_parts[-1]
                        else:
                            name_without_status = name
                            current_status = "❌"
                            
                        # Prüfe, ob dieser Name zum aktuellen Benutzer gehört
                        if name_without_status == user_display:
                            # Nur für den reagierenden Benutzer Status ändern
                            all_entries.append({
                                'name': name_without_status,
                                'status': emoji,
                                'category': category,
                                'inline': field.inline
                            })
                            logger.info(f"Status für {name_without_status} geändert zu {emoji}")
                        else:
                            # Für alle anderen den aktuellen Status beibehalten
                            all_entries.append({
                                'name': name_without_status,
                                'status': current_status,
                                'category': category,
                                'inline': field.inline
                            })
                
                # Nur fortfahren, wenn wir Einträge haben
                if all_entries:
                    # Erstelle ein neues Embed mit dem aktualisierten Status
                    new_embed = discord.Embed(
                        title=embed.title,
                        description=embed.description,
                        color=embed.color
                    )
                    
                    # Gruppiere Einträge nach Kategorie
                    entries_by_category = {}
                    for entry in all_entries:
                        category = entry['category']
                        if category not in entries_by_category:
                            entries_by_category[category] = []
                        entries_by_category[category].append(entry)
                    
                    # Füge Kategorien und Einträge hinzu
                    # Zunächst die definierten Rollen in der richtigen Reihenfolge
                    for rolle in rollen_reihenfolge:
                        if rolle in entries_by_category:
                            # Füge die Kategorie-Überschrift hinzu
                            new_embed.add_field(
                                name=f"__**{rolle}**__",
                                value="\u200b",  # Zero-width space als Platzhalter
                                inline=False
                            )
                            
                            # Füge alle Einträge dieser Kategorie hinzu
                            for entry in entries_by_category[rolle]:
                                new_embed.add_field(
                                    name=f"{entry['name']} {entry['status']}",
                                    value="\u200b",  # Zero-width space als Platzhalter
                                    inline=entry['inline']
                                )
                    
                    # Dann alle anderen Kategorien
                    for category, entries in entries_by_category.items():
                        if category not in rollen_reihenfolge:
                            # Füge die Kategorie-Überschrift hinzu
                            new_embed.add_field(
                                name=f"__**{category}**__",
                                value="\u200b",  # Zero-width space als Platzhalter
                                inline=False
                            )
                            
                            # Füge alle Einträge dieser Kategorie hinzu
                            for entry in entries:
                                new_embed.add_field(
                                    name=f"{entry['name']} {entry['status']}",
                                    value="\u200b",  # Zero-width space als Platzhalter
                                    inline=entry['inline']
                                )
                    
                    # Aktualisiere die Nachricht mit dem neuen Embed
                    await message.edit(embed=new_embed)
            else:
                # Wir haben das alte Embed-Format ohne Kategorien
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
                        # Aktualisiere den Status im Namen
                        if " " in field_name and field_name.split(" ")[-1] in status_emojis:
                            name_without_status = " ".join(field_name.split(" ")[:-1])
                            new_name = f"{name_without_status} {emoji}"
                        else:
                            new_name = f"{field_name} {emoji}"
                            
                        new_fields.append(
                            {'name': new_name, 'value': field_value, 'inline': field.inline}
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
            # Fallback für nicht-Embed-Nachrichten (altes Text-Format)
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

async def run_bot(bot, token):
    """Run the Discord bot with the given token"""
    try:
        logger.info("Attempting to connect to Discord...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token. Please check your environment variables.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        traceback.print_exc()

def disconnect_bot(bot):
    """Disconnect the bot and clean up"""
    if bot and bot.is_ready():
        logger.info("Disconnecting bot...")
        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
        logger.info("Bot disconnected")
