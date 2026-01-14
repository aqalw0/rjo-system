import discord
from discord.ext import commands
import os
import config
import asyncio
import threading
import socket

# 🔧 Fake TCP server for Koyeb health check
def fake_server():
    s = socket.socket()
    s.bind(('0.0.0.0', 8000))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        conn.close()

threading.Thread(target=fake_server, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    print("🚀 Bot is now running!")

async def load_extensions():
    print("📦 Loading modules...")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

async def main():
    await load_extensions()
    await bot.start(config.TOKEN)

asyncio.run(main())
