import discord
from discord.ext import commands
import datetime
import asyncio

ALLOWED_ROLES = ["Superior", "Sentinal"]
JAIL_ROLE_NAME = "Prison"
JAIL_CHANNEL_NAME = "السجن"
PRISON_LOG_CHANNEL = "prison-logs"
JAIL_REASONS = ["ديني", "سياسي", "سب", "سبام", "No Reason", "تحقيق"]


# ==========================
#  UI ELEMENTS (Select + Buttons)
# ==========================

class JailReasonSelect(discord.ui.Select):
    def __init__(self, ctx, member, message):
        self.ctx = ctx
        self.member = member
        self.message = message
        options = [discord.SelectOption(label=reason) for reason in JAIL_REASONS]
        super().__init__(placeholder="اختر سبب السجن...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ هذا الخيار مو لك.", ephemeral=True)
            return

        reason = self.values[0]
        await self.ctx.message.add_reaction("✅")
        await interaction.message.delete()

        await jail_logic(self.ctx, self.member, reason)


class CancelButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(label="❌ إلغاء", style=discord.ButtonStyle.danger)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ هذا الخيار مو لك.", ephemeral=True)
            return
        await interaction.message.delete()


class JailView(discord.ui.View):
    def __init__(self, ctx, member):
        super().__init__(timeout=20)
        self.ctx = ctx
        self.member = member
        self.message = None

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except:
                pass


# ==========================
#  JAIL LOGIC
# ==========================

async def jail_logic(ctx, member: discord.Member, reason: str):
    guild = ctx.guild

    # 🔥 إصلاح مشكلة عدم إيجاد الكوغ
    cog = ctx.bot.get_cog("Jail")
    if cog is None:
        for loaded in ctx.bot.cogs.values():
            if isinstance(loaded, Jail):
                cog = loaded
                break

    if cog is None:
        print("[ERROR] Jail cog not found")
        return

    # صلاحيات
    if not (
        ctx.author.id == guild.owner_id or
        ctx.author.guild_permissions.administrator or
        any(role.name in ALLOWED_ROLES for role in ctx.author.roles)
    ):
        return

    # منع سجن نفسك أو البوت أو المالك
    if member.id in [guild.owner_id, ctx.author.id, ctx.bot.user.id]:
        return

    # 🔥 إصلاح شرط الرتبة
    if member.top_role.position >= ctx.author.top_role.position and ctx.author.id != guild.owner_id:
        await ctx.reply("❌ لا يمكنك سجن عضو نفس أو أعلى منك.", mention_author=False)
        return

    # إنشاء رتبة السجن إذا غير موجودة
    prison_role = discord.utils.get(guild.roles, name=JAIL_ROLE_NAME)
    if not prison_role:
        prison_role = await guild.create_role(
            name=JAIL_ROLE_NAME,
            color=discord.Color.red(),
            reason="إنشاء رتبة السجن"
        )
        for channel in guild.channels:
            await channel.set_permissions(
                prison_role,
                view_channel=False,
                send_messages=False,
                connect=False,
                speak=False
            )

    # حفظ الرتب
    roles_to_remove = [role for role in member.roles if role != guild.default_role and role != prison_role]
    cog.previous_roles[member.id] = roles_to_remove
    cog.previous_reasons[member.id] = reason

    # إزالة الرتب وإضافة السجن
    await member.remove_roles(*roles_to_remove, reason="سجن العضو")
    await member.add_roles(prison_role, reason="سجن العضو")

    # طرده من الروم الصوتي
    if member.voice and member.voice.channel:
        try:
            await member.move_to(None)
        except Exception as e:
            print(f"[ERROR] فشل طرد العضو من الروم الصوتي: {e}")

    # إنشاء روم السجن إذا غير موجود
    jail_channel = discord.utils.get(guild.text_channels, name=JAIL_CHANNEL_NAME)
    if not jail_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            prison_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        jail_channel = await guild.create_text_channel(JAIL_CHANNEL_NAME, overwrites=overwrites)

    # إرسال لوق السجن
    log_channel = discord.utils.get(guild.text_channels, name=PRISON_LOG_CHANNEL)
    if log_channel:
        message_link = f"https://discord.com/channels/{guild.id}/{ctx.channel.id}/{ctx.message.id}"
        timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

        embed = discord.Embed(
            title="Jail Member",
            description=(
                f"**To:** {member.mention}\n"
                f"**By:** {ctx.author.mention}\n"
                f"**Message:** [Click Here]({message_link})\n"
                f"**Time:** Permanent\n"
                f"**Reason:**\n```{reason}```"
            ),
            color=discord.Color.red()
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_footer(text=f"{ctx.author} • {timestamp}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url="https://imgur.com/L7Ihh12.png")

        await log_channel.send(embed=embed)


# ==========================
#  COG CLASS
# ==========================

class Jail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.previous_roles = {}
        self.previous_reasons = {}

    async def release_logic(self, ctx, member: discord.Member):
        guild = ctx.guild
        prison_role = discord.utils.get(guild.roles, name=JAIL_ROLE_NAME)

        if not prison_role or prison_role not in member.roles:
            await ctx.reply("❌ العضو غير مسجون.", mention_author=False)
            return

        if ctx.me.top_role.position <= member.top_role.position:
            await ctx.reply("❌ لا يمكنني الإفراج عن عضو رتبته أعلى مني.", mention_author=False)
            return

        await member.remove_roles(prison_role, reason="إفراج")

        old_roles = self.previous_roles.get(member.id)
        if old_roles:
            try:
                await member.add_roles(*old_roles, reason="استرجاع الرتب")
            except:
                pass
            del self.previous_roles[member.id]

        reason = self.previous_reasons.get(member.id, "Unknown")
        del self.previous_reasons[member.id]

        log_channel = discord.utils.get(guild.text_channels, name=PRISON_LOG_CHANNEL)
        if log_channel:
            message_link = f"https://discord.com/channels/{guild.id}/{ctx.channel.id}/{ctx.message.id}"
            timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

            embed = discord.Embed(
                title="Unjail Member",
                description=(
                    f"**To:** {member.mention}\n"
                    f"**By:** {ctx.author.mention}\n"
                    f"**Message:** [Click Here]({message_link})\n"
                    f"**Previous Reason:**\n```{reason}```"
                ),
                color=discord.Color.red()
            )
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.set_footer(text=f"{ctx.author} • {timestamp}", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url="https://imgur.com/oIb4K7N.png")

            await log_channel.send(embed=embed)

    @commands.command(name="jail")
    async def jail_command(self, ctx, member: discord.Member):
        view = JailView(ctx, member)
        msg = await ctx.send(
            content=f"**يرجى تحديد سبب السجن.**\n• {member.mention}",
            view=view
        )
        view.message = msg
        view.add_item(JailReasonSelect(ctx, member, msg))
        view.add_item(CancelButton(ctx))
        await msg.edit(view=view)

    @commands.command(name="unjail")
    async def unjail_command(self, ctx, member: discord.Member):
        await self.release_logic(ctx, member)
        await ctx.message.add_reaction("✅")


async def setup(bot):
    await bot.add_cog(Jail(bot))
