import discord
from discord.ext import commands
import config
import datetime

class ServerLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            invites = await guild.invites()
            self.invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = after.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
        if not log_channel:
            return

        timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

        if before.nick != after.nick:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id != after.id:
                    continue
                actor = entry.user
                embed = discord.Embed(
                    title="**Nickname Updated**",
                    description=(
                        f"**User:** {after.mention} ({after.id})\n"
                        f"**Before:** {before.nick or before.name}\n"
                        f"**After:** {after.nick or after.name}"
                    ),
                    color=discord.Color.from_rgb(192,55,209)
                )
                embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
                embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
                embed.set_thumbnail(url="https://i.imgur.com/DxgqucH.png")
                await log_channel.send(embed=embed)
                break

        if before.roles != after.roles:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                if entry.target.id != after.id:
                    continue

                actor = entry.user
                added_roles = [r.name for r in after.roles if r not in before.roles and r.name != "@everyone"]
                removed_roles = [r.name for r in before.roles if r not in after.roles and r.name != "@everyone"]

                added_text = "\n".join([f"✅ + {r}" for r in added_roles]) if added_roles else ""
                removed_text = "\n".join([f"❌ - {r}" for r in removed_roles]) if removed_roles else ""
                role_changes = f"{added_text}\n{removed_text}".strip() or "لا يوجد تغيير"
                formatted_changes = f"```{role_changes}\n```"

                embed = discord.Embed(
                    title="**Roles Changed**",
                    description=(
                        f"**To:** {after.mention} `{after.id}`\n"
                        f"**By:** {actor.mention} `{after.id}`\n"
                        f"{formatted_changes}"
                    ),
                    color=discord.Color.from_rgb(73,61,93)
                )
                embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
                embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
                embed.set_thumbnail(url="https://imgur.com/966rxwD.png")
                await log_channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
        if not log_channel:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            actor = entry.user
            timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

            channel_type = "Text" if isinstance(channel, discord.TextChannel) else \
                           "Voice" if isinstance(channel, discord.VoiceChannel) else \
                           "Category" if isinstance(channel, discord.CategoryChannel) else "Unknown"

            embed = discord.Embed(
                title="Channel Created",
                description=(
                    f"**To:** {channel.name}\n"
                    f"**By:** {actor.mention}\n"
                    f"```fix\nType: {channel_type}\n```"
                ),
                color=discord.Color.from_rgb(133,127,153)
            )
            embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
            embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url="https://imgur.com/WG1hvQG.png")
            await log_channel.send(embed=embed)
            break

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
        if not log_channel:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            actor = entry.user
            timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

            channel_type = "Text" if isinstance(channel, discord.TextChannel) else \
                           "Voice" if isinstance(channel, discord.VoiceChannel) else \
                           "Category" if isinstance(channel, discord.CategoryChannel) else "Unknown"

            embed = discord.Embed(
                title="Channel Deleted",
                description=(
                    f"**To:** {channel.name}\n"
                    f"**By:** {actor.mention}\n"
                    f"```fix\nType: {channel_type}\n```"
                ),
                color=discord.Color.from_rgb(133,127,153)
            )
            embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
            embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url="https://imgur.com/Nl3y0rm.png")
            await log_channel.send(embed=embed)
            break

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        guild = after.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
        if not log_channel:
            return

        timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

        changes = []

        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")

        if before.category != after.category:
            before_cat = before.category.name if before.category else "بدون"
            after_cat = after.category.name if after.category else "بدون"
            changes.append(f"**Category:** `{before_cat}` → `{after_cat}`")

        if before.overwrites != after.overwrites:
            changes.append("**Permissions:** تم تعديل الصلاحيات")

        if not changes:
            return

        channel_type = "Text" if isinstance(after, discord.TextChannel) else \
                       "Voice" if isinstance(after, discord.VoiceChannel) else \
                       "Category" if isinstance(after, discord.CategoryChannel) else "Unknown"

        embed = discord.Embed(
            title="Channel Updated",
            description=(
                f"**To:** {after.name}\n"
                f"```fix\nType: {channel_type}\n```"
                f"\n" + "\n".join(changes)
            ),
            color=discord.Color.from_rgb(109,88,115)
        )
        embed.set_thumbnail(url="https://imgur.com/jGCQyQm.png")
        embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
        if not log_channel:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            actor = entry.user
            timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
            embed = discord.Embed(
                title="**Role Created**",
                description=f"**Role:** {role.name} ({role.id})",
                color=discord.Color.from_rgb(73,61,93)
            )
            embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
            embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url="https://i.imgur.com/kJqZmT5.png")
            await log_channel.send(embed=embed)
            break

@commands.Cog.listener()
async def on_guild_role_delete(self, role):
    guild = role.guild
    log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
    if not log_channel:
        return

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        actor = entry.user
        timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

        embed = discord.Embed(
            title="**Role Deleted**",
            description=f"**Role:** {role.name} ({role.id})",
            color=discord.Color.from_rgb(73,61,93)
        )
        embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
        embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
        embed.set_thumbnail(url="https://i.imgur.com/kJqZmT5.png")
        await log_channel.send(embed=embed)
        break


    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild = after.guild
        log_channel = discord.utils.get(guild.text_channels, name=config.SERVER_LOG_CHANNEL)
        if not log_channel:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            actor = entry.user
            timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
            embed = discord.Embed(
                title="**Role Permissions Changed**",
                description=f"**Role:** {after.name} ({after.id})",
                color=discord.Color.from_rgb(73,61,93)
            )
            embed.set_author(name=str(actor), icon_url=actor.display_avatar.url)
            embed.set_footer(text=f"{guild.name} • {timestamp}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url="https://i.imgur.com/kJqZmT5.png")
            await log_channel.send(embed=embed)
            break

# ✅ دالة التحميل
async def setup(bot):
    await bot.add_cog(ServerLogger(bot))
