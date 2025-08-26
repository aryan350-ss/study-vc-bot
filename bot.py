import discord
from discord.ext import commands
import asyncio
import os
import json
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Study roles mapping (hours : role_name)
role_levels = [
    (0, "🍟 Chill Maaru"),
    (1, "😓 Thoda Padhta Hai"),
    (2, "📖 Padhaku Aadmi"),
    (6, "⚡ Ghissu Machine"),
    (10, "💡 Exam Fighter"),
    (11, "👑 Topper Baap")
]

# File to store study times
DATA_FILE = "study_data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")


# Track when someone joins VC
user_join_times = {}

@bot.event
async def on_voice_state_update(member, before, after):
    data = load_data()

    if after.channel is not None and before.channel is None:  # Joined VC
        user_join_times[member.id] = datetime.utcnow()

    elif before.channel is not None and after.channel is None:  # Left VC
        if member.id in user_join_times:
            join_time = user_join_times.pop(member.id)
            duration = (datetime.utcnow() - join_time).total_seconds() / 3600  # in hours

            # Add to total
            user_id = str(member.id)
            data[user_id] = data.get(user_id, 0) + duration
            save_data(data)

            # Check role upgrade
            await update_role(member, data[user_id])


async def update_role(member, hours):
    guild = member.guild
    assigned_role = None

    for req_hours, role_name in reversed(role_levels):
        if hours >= req_hours:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                assigned_role = role
                break

    if assigned_role:
        # Remove lower roles
        for req_hours, role_name in role_levels:
            role = discord.utils.get(guild.roles, name=role_name)
            if role in member.roles:
                await member.remove_roles(role)

        await member.add_roles(assigned_role)
        print(f"Gave {assigned_role.name} to {member.display_name}")


# Command to check study hours
@bot.command()
async def studytime(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    data = load_data()
    hours = data.get(str(member.id), 0)
    await ctx.send(f"📊 {member.display_name} ne total {hours:.2f} ghante study kiya hai VC me.")


bot.run(TOKEN)
