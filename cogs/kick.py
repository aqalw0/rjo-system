import discord
from discord.ext import commands
import config
import datetime
import asyncio

class KickReasonSelect(discord.ui.Select):
    def __init__(self, ctx, member):
        self.ctx = ctx
        self.member = member

        options = [
            discord.SelectOption(label="ديني - سياسي", description="طرد مباشر"),
            discord.SelectOption(label="سب", description="طرد مباشر"),
            discord.SelectOption(label="سبام", description="طرد مباشر"),
            discord.SelectOption(label="No Reason", description="طرد بدون سبب")
        ]

        super().__init__(placeholder="اختر سبب الطرد...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return  # يسحب عليه → Discord يعرض "This interaction failed"

        reason = self.values[0]
        ctx = self.ctx
        member = self.member
        timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")

        embed = discord.Embed(
            title="Kick Member",
            description=(
                f"**To:**\n{member.mention}\n"
                f"**By:**\n{ctx.author.mention}\n"
                f"**Reason:**\n```{reason}```"
            ),
            color=discord.Color.from_rgb(136,0,19)
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_footer(text=f"{ctx.author} • {timestamp}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url="https://i.imgur.com/F3nkbCV.png")

        log_channel = discord.utils.get(ctx.guild.text_channels, name=config.KICK_LOG_CHANNEL)
        if log_channel:
            await log_channel.send(embed=embed)

        try:
            await member.kick(reason=reason)
        except Exception as e:
            await ctx.send(f"❌ فشل الطرد: {e}")

        await ctx.message.add_reaction("✅")
        await interaction.message.delete()

class CancelButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(label="❌ إلغاء", style=discord.ButtonStyle.danger)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return  # يسحب عليه → Discord يعرض "This interaction failed"
        await interaction.message.delete()

class KickView(discord.ui.View):
    def __init__(self, ctx, member):
        super().__init__(timeout=15)
        self.ctx = ctx
        self.member = member
        self.message = None
        self.add_item(KickReasonSelect(ctx, member))
        self.add_item(CancelButton(ctx))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except:
                pass

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kick(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.kick_members:
            return

        if member.id in [ctx.guild.owner_id, ctx.author.id, ctx.bot.user.id]:
            return

        if ctx.author.id != ctx.guild.owner_id:
            if member.top_role.position == ctx.author.top_role.position:
                await ctx.reply("**لا يمكنك طرد شخص نفس رتبتك.**", mention_author=False)
                return
            if member.top_role.position > ctx.author.top_role.position:
                await ctx.reply("**لا يمكنك طرد شخص اعلى منك.**", mention_author=False)
                return

        if ctx.me.top_role.position <= member.top_role.position:
            return

        view = KickView(ctx, member)
        msg = await ctx.reply(
            content=f"**يرجى تحديد سبب العقوبة.**\n• {member.mention}",
            view=view,
            mention_author=False
        )
        view.message = msg

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        content = message.content.strip().lower()
        parts = content.split()

        #رد تنبيهي إذا كتب "كيك" لحاله بدون منشن
        if content == "كيك":
            embed = discord.Embed(
                description="**يرجى استعمال الأمر بالطريقة الصحيحة.** \n **كيك @mention**",
                color=discord.Color.from_rgb(128, 128, 128)
            )
            msg = await message.channel.send(embed=embed)
            await asyncio.sleep(15)
            try:
                await msg.delete()
            except:
                pass
            return

        # تنفيذ أمر الكيك إذا فيه منشن
        if content.startswith("كيك") and len(parts) >= 2:
            if not message.author.guild_permissions.kick_members:
                return

            try:
                member = await commands.MemberConverter().convert(ctx, parts[1])
                await self.kick(ctx, member)
            except Exception as e:
                print(f"[ERROR] kick command failed: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        audit_logs = member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick)
        async for entry in audit_logs:
            if entry.target.id == member.id:
                timestamp = datetime.datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
                embed = discord.Embed(
                    title="Kick Member (Manual)",
                    description=(
                        f"**To:**\n{member.mention}\n"
                        f"**By:**\n{entry.user.mention}\n"
                        f"**Reason:**\n```{entry.reason or 'بدون سبب'}```"
                    ),
                    color=discord.Color.from_rgb(136,0,19)
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_footer(text=f"{entry.user} • {timestamp}", icon_url=entry.user.display_avatar.url)
                embed.set_thumbnail(url="https://i.imgur.com/F3nkbCV.png")

                log_channel = discord.utils.get(member.guild.text_channels, name=config.KICK_LOG_CHANNEL)
                if log_channel:
                    await log_channel.send(embed=embed)
                break

async def setup(bot):
    await bot.add_cog(Kick(bot))
