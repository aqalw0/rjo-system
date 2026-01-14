import discord
from discord.ext import commands
import config
import asyncio
import datetime

class BanReasonSelect(discord.ui.Select):
    def __init__(self, ctx, member):
        self.ctx = ctx
        self.member = member

        options = [
            discord.SelectOption(label="سياسي - ديني", description="باند دائم"),
            discord.SelectOption(label="قذف", description="باند دائم"),
            discord.SelectOption(label="سبام", description="باند لمدة أسبوع"),
            discord.SelectOption(label="No reason", description="باند دائم")
        ]

        super().__init__(placeholder="اختر سبب الباند...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return  # يسحب عليه → Discord يعرض "This interaction failed"
        
        reason = self.values[0]
        duration = {
            "سبام": 7 * 24 * 60 * 60  # أسبوع
        }.get(reason)

        now = datetime.datetime.utcnow()
        unban_time = now + datetime.timedelta(seconds=duration) if duration else None
        formatted_unban = unban_time.strftime("%I:%M:%S %p – %Y/%m/%d") if unban_time else "غير محدد"

        if not self.ctx.author.guild_permissions.ban_members:
            return
        if self.member.id in [self.ctx.guild.owner_id, self.ctx.author.id, self.ctx.bot.user.id]:
            return
        if self.ctx.author.id != self.ctx.guild.owner_id:
            if self.member.top_role.position >= self.ctx.author.top_role.position:
                return
        if self.ctx.me.top_role.position <= self.member.top_role.position:
            return

        try:
            await self.ctx.guild.ban(self.member, reason=reason, delete_message_days=0)
        except discord.Forbidden:
            return

        message_link = f"https://discord.com/channels/{self.ctx.guild.id}/{self.ctx.channel.id}/{self.ctx.message.id}"
        log_channel = discord.utils.get(self.ctx.guild.text_channels, name=config.BAN_LOG_CHANNEL)

        embed = discord.Embed(
            title="#**Ban Member**",
            description=(
                f"**To:** {self.member.mention}\n"
                f"**By:** {self.ctx.author.mention}\n"
                f"**Message:** [Click Here]({message_link})\n"
                f"**Time:** {'`أسبوع`' if duration else '`دائم`'}\n"
                f"**Un Ban At:** {formatted_unban}\n"
                f"**Reason:**\n```{reason}```"
            ),
            color=discord.Color.from_rgb(136,0,19)
        )
        embed.set_author(name=str(self.member), icon_url=self.member.display_avatar.url)
        embed.set_footer(text=str(self.ctx.author), icon_url=self.ctx.author.display_avatar.url)
        embed.set_thumbnail(url="https://imgur.com/F3nkbCV.png")

        if log_channel:
            await log_channel.send(embed=embed)

        await interaction.message.delete()
        await self.ctx.message.add_reaction("✅")

        if duration:
            await asyncio.sleep(duration)
            try:
                await self.ctx.guild.unban(self.member)
                unban_embed = discord.Embed(
                    title="#**Unban Member**",
                    description=(
                        f"**To:** {self.member.mention}\n"
                        f"**Reason:** انتهاء مدة الباند المؤقت\n"
                        f"**Time:** `أسبوع`\n"
                        f"**Unban At:** {formatted_unban}"
                    ),
                    color=discord.Color.from_rgb(136,0,19)
                )
                unban_embed.set_footer(text="Ban Log System")
                unban_embed.set_thumbnail(url="https://imgur.com/F3nkbCV.png")
                if log_channel:
                    await log_channel.send(embed=unban_embed)
            except:
                pass

class CancelButton(discord.ui.Button):
    def __init__(self, ctx):
        super().__init__(label="إلغاء", style=discord.ButtonStyle.danger, emoji="❌")
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return  # يسحب عليه → Discord يعرض "This interaction failed"
        await interaction.message.delete()

class BanReasonView(discord.ui.View):
    def __init__(self, ctx, member):
        super().__init__(timeout=15)
        self.add_item(BanReasonSelect(ctx, member))
        self.add_item(CancelButton(ctx))
        self.message = None

    async def on_timeout(self):
        try:
            if self.message:
                await self.message.delete()
        except:
            pass

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ban(self, ctx, member: discord.Member):
        if not ctx.author.guild_permissions.ban_members:
            return
        if member.id in [ctx.guild.owner_id, ctx.author.id, ctx.bot.user.id]:
            return
        if ctx.author.id != ctx.guild.owner_id:
            if member.top_role.position >= ctx.author.top_role.position:
                return
        if ctx.me.top_role.position <= member.top_role.position:
            return

        view = BanReasonView(ctx, member)
        msg = await ctx.reply(
            content=f"**يرجى تحديد سبب العقوبة.**\n**•** {member.mention}",
            view=view,
            mention_author=False
        )
        view.message = msg

    @commands.command()
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason"):
        try:
            user = await ctx.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
        except discord.NotFound:
            return
        except discord.Forbidden:
            return
        except Exception:
            return

        log_channel = discord.utils.get(ctx.guild.text_channels, name=config.BAN_LOG_CHANNEL)
        if log_channel:
            embed = discord.Embed(
                title="#**Unban Member**",
                description=(
                    f"**User:** {user.mention if hasattr(user, 'mention') else str(user)}\n"
                    f"**By:** {ctx.author.mention}\n"
                    f"**Time:** `غير محددة (يدوي)`\n"
                    f"**Reason:**\n```{reason}```\n"
                ),
                color=discord.Color.from_rgb(136,0,19)
            )
            embed.set_footer(text="Ban Log System")
            embed.set_thumbnail(url="https://imgur.com/F3nkbCV.png")
            await log_channel.send(embed=embed)

        await ctx.message.add_reaction("✅")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        content = message.content.strip()
        parts = content.split()

        # ✅ إذا كتب "باند" لحاله بدون منشن
        if content == "باند":
            embed = discord.Embed(
                description="**يرجى استعمال الأمر بالطريقة الصحيحة.** \n **باند @mention**",
                color=discord.Color.from_rgb(128, 128, 128)
            )
            msg = await message.channel.send(embed=embed)
            await asyncio.sleep(15)
            try:
                await msg.delete()
            except:
                pass
            return

        # ✅ تنفيذ أمر الباند إذا فيه منشن
        if content.startswith("باند") and len(parts) >= 2:
            ctx = await self.bot.get_context(message)
            try:
                member = await commands.MemberConverter().convert(ctx, parts[1])
            except:
                return

            if not message.author.guild_permissions.ban_members:
                return
            if member.id in [message.guild.owner_id, message.author.id, self.bot.user.id]:
                return
            if message.author.id != message.guild.owner_id:
                if member.top_role.position >= message.author.top_role.position:
                    return
            if message.guild.me.top_role.position <= member.top_role.position:
                return

            view = BanReasonView(ctx, member)
            msg = await message.channel.send(
                content=f"**يرجى تحديد سبب الباند.**\n**•** {member.mention}",
                view=view
            )
            view.message = msg

async def setup(bot):
    await bot.add_cog(Ban(bot))
