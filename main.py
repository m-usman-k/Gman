import discord
from discord.ext import commands

from config import BOT_TOKEN

from functions.database import *



bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"🟩 | Bot loaded as {bot.user.name}")

    setup_tables()
    print(f"🟩 | Setup all tables")

    # await bot.load_extension("extensions.ping")
    print(f"🟩 | Loaded all extensions")

    await bot.tree.sync()
    print("🟩 | Synced all commands")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("pong")



if __name__ == "__main__":
    bot.run(BOT_TOKEN)