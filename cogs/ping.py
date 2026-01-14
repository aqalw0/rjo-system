import discord
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        latency = round(ctx.bot.latency * 1000)
        await ctx.send(f"$ma")

async def setup(bot):
    await bot.add_cog(Ping(bot))
