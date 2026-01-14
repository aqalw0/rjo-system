import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import config

class VoiceLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_disconnects = []
        self.cleanup_disconnects.start()

    def get_member_list(self, channel: discord.VoiceChannel):
        if not channel or not channel.members:
            return "No Members"
        lines = [f"{i+1}. {m.display_name}" for i, m in enumerate(channel.members)]
        return f"```\n" + "\n".join(lines) + "\n```"

    async def update_disconnect_log(self, guild):
        now = discord.utils.utcnow()
        async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.member_disconnect):
            if abs((now - entry.created_at).total_seconds()) < 5:
                self.recent_disconnects.append({
                    "executor": entry.user,
                    "time": entry.created_at
                })

    # ✅ النسخة الصحيحة 100% — إصلاح الميوت/دفن
    async def get_executor(self, member, attribute, expected_value):
        await asyncio.sleep(1)
        now = discord.utils.utcnow()

        async for entry in member.guild.audit_logs(limit=10, action=discord.AuditLogAction.member_update):
            if entry.target.id != member.id:
                continue

            before = entry.before
            after = entry.after

            # mute
            if attribute == "mute":
                if hasattr(before, "mute") and hasattr(after, "mute"):
                    if before.mute != after.mute and after.mute == expected_value:
                        if abs((now - entry.created_at).total_seconds()) < 10:
                            return entry.user

            # deaf
            if attribute == "deaf":
                if hasattr(before, "deaf") and hasattr(after, "deaf"):
                    if before.deaf != after.deaf and after.deaf == expected_value:
                        if abs((now - entry.created_at).total_seconds()) < 10:
                            return entry.user

        return None

    @tasks.loop(seconds=10)
    async def cleanup_disconnects(self):
        now = discord.utils.utcnow()
        self.recent_disconnects = [
            d for d in self.recent_disconnects
            if abs((now - d["time"]).total_seconds()) < 10
        ]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            log_channel = discord.utils.get(member.guild.text_channels, name=config.VOICE_LOG_CHANNEL)
            if not log_channel:
                return

            # دخول الروم
            if not before.channel and after.channel:
                embed = discord.Embed(
                    title="Joined Channel",
                    description=(
                        f"**To:** {member.mention}\n"
                        f"**In:** {after.channel.mention}\n"
                        f"**Members:**\n{self.get_member_list(after.channel)}"
                    ),
                    color=discord.Color.from_rgb(24, 57, 85)
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/JAdNhul.png")
                await log_channel.send(embed=embed)

            # خروج من الروم
            elif before.channel and not after.channel:
                await asyncio.sleep(1)
                await self.update_disconnect_log(member.guild)
                now = discord.utils.utcnow()
                executor = None
                for d in self.recent_disconnects:
                    if abs((now - d["time"]).total_seconds()) < 5:
                        executor = d["executor"]
                        break

                timestamp = now.strftime("%b %d, %Y %I:%M %p")

                if executor:
                    embed = discord.Embed(
                        title="Disconnected",
                        description=(
                            f"**User:** {member.mention}\n"
                            f"**Channel:** {before.channel.mention}\n"
                            f"**By:** {executor.mention}\n"
                            f"**Members:**\n```{self.get_member_list(before.channel)}```"
                        ),
                        color=discord.Color.red()
                    )
                    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                    embed.set_footer(text=f"{member.guild.name} • {timestamp}", icon_url=member.guild.icon.url if member.guild.icon else None)
                    embed.set_thumbnail(url="https://i.imgur.com/OHI7tI8.png")
                    await log_channel.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Left Channel",
                        description=(
                            f"**User:** {member.mention}\n"
                            f"**Channel:** {before.channel.mention}\n"
                            f"**Members:**\n```{self.get_member_list(before.channel)}```"
                        ),
                        color=discord.Color.from_rgb(24, 57, 85)
                    )
                    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                    embed.set_footer(text=f"{member.guild.name} • {timestamp}", icon_url=member.guild.icon.url if member.guild.icon else None)
                    embed.set_thumbnail(url="https://imgur.com/AcEAqFN.png")
                    await log_channel.send(embed=embed)

            # التنقل بين الرومات
            elif before.channel and after.channel and before.channel != after.channel:
                await asyncio.sleep(1)
                now = discord.utils.utcnow()
                executor = None
                async for entry in member.guild.audit_logs(limit=6, action=discord.AuditLogAction.member_move):
                    if abs((now - entry.created_at).total_seconds()) < 5:
                        executor = entry.user
                        break

                if executor:
                    embed = discord.Embed(
                        title="Moved Member",
                        description=(
                            f"**User:** {member.mention}\n"
                            f"**From:** {before.channel.mention}\n"
                            f"**By:** {executor.mention}\n"
                            f"**To:** {after.channel.mention}\n"
                            f"**Members in New Channel:**\n{self.get_member_list(after.channel)}"
                        ),
                        color=discord.Color.from_rgb(61, 24, 13)
                    )
                    embed.set_thumbnail(url="https://imgur.com/Ek5SgA8.png")
                else:
                    embed = discord.Embed(
                        title="Change Channel",
                        description=(
                            f"**User:** {member.mention}\n"
                            f"**From:** {before.channel.mention}\n"
                            f"**To:** {after.channel.mention}\n"
                            f"**Members in New Channel:**\n{self.get_member_list(after.channel)}"
                        ),
                        color=discord.Color.from_rgb(78, 156, 165)
                    )
                    embed.set_thumbnail(url="https://imgur.com/5q6mgu8.png")

                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                await log_channel.send(embed=embed)

            # ميوت صوتي
            if not before.mute and after.mute:
                executor = await self.get_executor(member, "mute", True)
                embed = discord.Embed(
                    title="Muted Member",
                    description=(
                        f"**To:** {member.mention}\n"
                        f"**In:** {after.channel.mention if after.channel else 'غير معروف'}\n"
                        + (f"**By:** {executor.mention}\n" if executor else "")
                        + f"**Members:**\n{self.get_member_list(after.channel)}"
                    ),
                    color=discord.Color.from_rgb(167, 180, 255)
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/js9smbQ.png")
                await log_channel.send(embed=embed)

            # فك الميوت
            if before.mute and not after.mute:
                executor = await self.get_executor(member, "mute", False)
                embed = discord.Embed(
                    title="UnMuted Member",
                    description=(
                        f"**To:** {member.mention}\n"
                        f"**In:** {after.channel.mention if after.channel else 'غير معروف'}\n"
                        + (f"**By:** {executor.mention}\n" if executor else "")
                        + f"**Members:**\n{self.get_member_list(after.channel)}"
                    ),
                    color=discord.Color.from_rgb(167, 180, 255)
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/rB4J6fA.png")
                await log_channel.send(embed=embed)

            # دفن صوتي
            if not before.deaf and after.deaf:
                executor = await self.get_executor(member, "deaf", True)
                embed = discord.Embed(
                    title="Deafened Member",
                    description=(
                        f"**To:** {member.mention}\n"
                        f"**In:** {after.channel.mention if after.channel else 'غير معروف'}\n"
                        + (f"**By:** {executor.mention}\n" if executor else "")
                        + f"**Members:**\n{self.get_member_list(after.channel)}"
                    ),
                    color=discord.Color.from_rgb(73, 30, 98)
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/Iijhg1G.png")
                await log_channel.send(embed=embed)

            # فك الدفن
            if before.deaf and not after.deaf:
                executor = await self.get_executor(member, "deaf", False)
                embed = discord.Embed(
                    title="Undeafened Member",
                    description=(
                        f"**To:** {member.mention}\n"
                        f"**In:** {after.channel.mention if after.channel else 'غير معروف'}\n"
                        + (f"**By:** {executor.mention}\n" if executor else "")
                        + f"**Members:**\n{self.get_member_list(after.channel)}"
                    ),
                    color=discord.Color.from_rgb(73, 30, 98)
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_thumbnail(url="https://imgur.com/1F41XCS.png")
                await log_channel.send(embed=embed)

        except Exception as e:
            print(f"[ERROR] {e}")

async def setup(bot):
    await bot.add_cog(VoiceLogger(bot))
