import discord
from discord.ext import commands


class Deposit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()

        self.bot = bot


async def setup(bot: commands.Bot):
    await bot.add_cog(Deposit(bot=bot))