import discord
from discord.ext import commands
import config
import datetime

class TimeoutLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.TIMEOUT_LOG_CHANNEL)
        if not log_channel:
            return

        # إضافة تايم أوت
        if before.timed_out_until != after.timed_out_until and after.timed_out_until is not None:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                if entry.target.id != after.id or entry.user.bot:
                    continue

                moderator = entry.user
                reason = entry.reason or "بدون سبب"
                timeout_until = after.timed_out_until.strftime("%A, %B %d, %Y, %I:%M %p")
                timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

                embed = discord.Embed(
                    title="# Timeout Add",
                    description=(
                        f"**To:**\n{after.mention} ``({after.id})``\n\n"
                        f"**By:**\n{moderator.mention} ``({moderator.id})``\n\n"
                        f"**Until:**\n`{timeout_until}`\n\n"
                        f"**Reason:**\n```{reason}```"
                    ),
                    color=discord.Color.from_rgb(122,0,0)
                )
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                embed.set_footer(text=f"{moderator} • {timestamp}", icon_url=moderator.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/CtIHmFw.png")
                await log_channel.send(embed=embed)
                break

        # إزالة التايم أوت
        elif before.timed_out_until is not None and after.timed_out_until is None:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                if entry.target.id != after.id or entry.user.bot:
                    continue

                moderator = entry.user
                reason = entry.reason or "انتهاء أو إزالة التايم أوت"
                timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

                embed = discord.Embed(
                    title="# Timeout Removed",
                    description=(
                        f"**To:**\n{after.mention} ``({after.id})``\n\n"
                        f"**By:**\n{moderator.mention} ``({moderator.id})``\n\n"
                        f"**Reason:**\n```{reason}```"
                    ),
                    color=discord.Color.from_rgb(122,0,0)
                )
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                embed.set_footer(text=f"{moderator} • {timestamp}", icon_url=moderator.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/CtIHmFw.png")
                await log_channel.send(embed=embed)
                break

async def setup(bot):
    await bot.add_cog(TimeoutLogger(bot))
