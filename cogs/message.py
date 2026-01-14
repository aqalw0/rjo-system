import discord
from discord.ext import commands
import config

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        log_channel = discord.utils.get(before.guild.text_channels, name=config.MESSAGE_LOG_CHANNEL)
        if not log_channel:
            return
        message_link = f"https://discord.com/channels/{before.guild.id}/{before.channel.id}/{before.id}"
        embed = discord.Embed(
            title="**Message Edited**",
            description=f"**From:** {before.author.mention}\n**Channel:** {before.channel.mention}\n**Message:** [**Click Here**]({message_link})",
            color=discord.Color.from_rgb(14,74,72)
        )
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        embed.add_field(name="**Before**", value=f"```{before.content}```", inline=False)
        embed.add_field(name="**After**", value=f"```{after.content}```", inline=False)
        embed.set_thumbnail(url="https://imgur.com/yw9qW6h.png") 
        embed.set_footer(text="Message Log System")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        log_channel = discord.utils.get(message.guild.text_channels, name=config.MESSAGE_LOG_CHANNEL)
        if not log_channel:
            return
        deleter = None
        async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
            if entry.target.id == message.author.id and abs((entry.created_at - discord.utils.utcnow()).total_seconds()) < 5:
                deleter = entry.user
                break
        embed = discord.Embed(
            title="**Message Deleted**",
            description=f"**From:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Deleted By:** {deleter.mention if deleter else 'Self-deleted'}",
            color=discord.Color.from_rgb(14,74,72)
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        if message.content:
            embed.add_field(name="**Content**", value=f"```{message.content}```", inline=False)
            embed.set_thumbnail(url="https://imgur.com/drt57GW.png") 
        embed.set_footer(text="Message Log System")
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MessageLogger(bot))
