
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Speichert die zuletzt gesendete Liste zum Bearbeiten
message_cache = {}
status_emojis = {"✅", "❌"}

@bot.command()
async def liste(ctx, *namen):
    """Erstellt eine Teilnehmerliste mit X hinter jedem Namen"""
    if not namen:
        await ctx.send("Bitte gib mindestens einen Namen an! Beispiel: `!liste Felix Tom Justin`")
        return

    text = "\n".join(f"{name} ❌" for name in namen)
    message = await ctx.send(text)
    await message.add_reaction("✅")
    await message.add_reaction("❌")

    # Speichere die Nachricht und die Namen
    message_cache[message.id] = {
        "author_id": ctx.author.id,
        "names": list(namen),
    }

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

    # Aktualisiere nur, wenn der Name in der Liste steht
    lines = message.content.split("\n")
    new_lines = []

    for line in lines:
        name, current_status = line.rsplit(" ", 1)
        if name == user_display:
            new_lines.append(f"{name} {emoji}")
        else:
            new_lines.append(line)

    await message.edit(content="\n".join(new_lines))

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user.name}!")

# 👉 Hier DEIN Token eintragen
bot.run("MTM2MzYxMzY0MjI2MzYyOTkzNQ.GRSjNI.QntZsQCxucN7z_jyl7ViPSEeq5Xf6jBiPhhGsw")
