import discord
from discord.ext import commands
import config
import datetime

ALLOWED_ROLES = ["Admins"]  # الرتب المسموح لها بالميوت

class MuteReasonSelect(discord.ui.Select):
    def __init__(self, ctx, member):
        self.ctx = ctx
        self.member = member

        options = [
            discord.SelectOption(label="مشاكل", description="1h"),
            discord.SelectOption(label="ديني", description="1h"),
            discord.SelectOption(label="سب", description="2h"),
            discord.SelectOption(label="سبام", description="30m"),
            discord.SelectOption(label="مخل", description="1h")
        ]

        super().__init__(placeholder="اختر سبب الميوت...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ هذا الخيار مو لك.", ephemeral=True)
            return

        reason = self.values[0]
        duration_str = {
            "مشاكل": "1h",
            "ديني": "1h",
            "سب": "2h",
            "سبام": "30m",
            "مخل": "1h"
        }[reason]

        now = datetime.datetime.utcnow()
        duration_map = {
            "30m": datetime.timedelta(minutes=30),
            "1h": datetime.timedelta(hours=1),
            "2h": datetime.timedelta(hours=2)
        }
        mute_duration = duration_map.get(duration_str, datetime.timedelta(hours=1))
        unmute_time = now + mute_duration
        formatted_unmute = unmute_time.strftime("%I:%M:%S %p – %Y/%m/%d")

        mute_role = discord.utils.get(self.ctx.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await self.ctx.guild.create_role(name="Muted")
            for channel in self.ctx.guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)

        await self.member.add_roles(mute_role, reason=reason)

        message_link = f"https://discord.com/channels/{self.ctx.guild.id}/{self.ctx.channel.id}/{self.ctx.message.id}"
        log_channel = discord.utils.get(self.ctx.guild.text_channels, name=config.MUTE_LOG_CHANNEL)

        if log_channel:
            embed = discord.Embed(
                title="Text Mute",
                description=(
                    f"**To:** {self.member.mention}\n"
                    f"**By:** {self.ctx.author.mention}\n"
                    f"**Message:** [Click Here]({message_link})\n"
                    f"**Time:** {duration_str.replace('m', ' minutes').replace('h', ' hours')}\n"
                    f"**Un Mute At:** {formatted_unmute}\n"
                    f"**Reason:**\n```{reason}```"
                ),
                color=discord.Color.from_rgb(49,46,93)
            )
            embed.set_author(name=str(self.member), icon_url=self.member.display_avatar.url)
            embed.set_footer(text=str(self.ctx.author), icon_url=self.ctx.author.display_avatar.url)
            embed.set_thumbnail(url="https://i.imgur.com/9OlCVuc.png")
            await log_channel.send(embed=embed)

        await interaction.message.delete()
        await self.ctx.message.add_reaction("✅")

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="إلغاء", style=discord.ButtonStyle.danger, emoji="❌")

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()

class MuteReasonView(discord.ui.View):
    def __init__(self, ctx, member):
        super().__init__(timeout=15)
        self.add_item(MuteReasonSelect(ctx, member))
        self.add_item(CancelButton())
        self.message = None

    async def on_timeout(self):
        try:
            if self.message:
                await self.message.delete()
        except:
            pass

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        print(f"[DEBUG] mute command triggered by {ctx.author} (ID: {ctx.author.id})")

        # تحقق من صلاحية المنفذ
        if (
            ctx.author.id != ctx.guild.owner_id and
            not ctx.author.guild_permissions.administrator and
            not any(role.name in ALLOWED_ROLES for role in ctx.author.roles)
        ):
            print("[DEBUG] mute blocked: sender lacks permission")
            return

        # منع الميوت عن الأونر أو الرتب الأعلى (إلا إذا المنفذ هو الأونر)
        if ctx.author.id != ctx.guild.owner_id:
            if member.id == ctx.guild.owner_id:
                print("[DEBUG] mute blocked: target is owner")
                return

            if member.top_role.position == ctx.author.top_role.position:
                print("[DEBUG] mute blocked: target has same role")
                await ctx.reply("**لايمكنك اعطاء اسكات لعضو نفس رتبتك**", mention_author=False)
                return

            if member.top_role.position > ctx.author.top_role.position:
                print("[DEBUG] mute blocked: target has higher role")
                await ctx.reply("**لا يمكنك اعطاء اسكات لعضو اعلى منك**", mention_author=False)
                return


        print(f"[DEBUG] mute allowed: proceeding with view for {member}")
        view = MuteReasonView(ctx, member)
        msg = await ctx.reply(
            content=f"يرجى تحديد سبب العقوبة.\n• {member.mention}",
            view=view,
            mention_author=False
        )
        view.message = msg

    @commands.command()
    async def unmute(self, ctx, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role or mute_role not in member.roles:
            return

        await member.remove_roles(mute_role, reason="فك الميوت يدويًا")

        message_link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}"
        log_channel = discord.utils.get(ctx.guild.text_channels, name=config.MUTE_LOG_CHANNEL)

        if log_channel:
            embed = discord.Embed(
                title="UnMute Member",
                description=f"**To:** {member.mention}\n**By:** {ctx.author.mention}\n**Message:** [Click Here]({message_link})",
                color=discord.Color.from_rgb(49,46,93)
            )
            embed.set_footer(text=str(ctx.author), icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url="https://i.imgur.com/SCooUrj.png")
            await log_channel.send(embed=embed)

        await ctx.message.add_reaction("✅")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        content = message.content.strip().lower()
        parts = content.split()
        
        # "تنبيه أمر" اسكت 
        if content == "اسكت":
            embed = discord.Embed(
                description="**يرجى استعمال الأمر بالطريقة الصحيحة.** \n **اسكت @mention**",
                color=discord.Color.from_rgb(128, 128, 128)
            )
            msg = await message.channel.send(embed=embed)
            await asyncio.sleep(15)
            try:
                await msg.delete()
            except:
                pass
            return

        # ✅ تنبيه أمر "تكلم"
        if content == "تكلم":
            embed = discord.Embed(
                description="**يرجى استعمال الأمر بالطريقة الصحيحة.** \n **تكلم @mention**",
                color=discord.Color.from_rgb(128, 128, 128)
            )
            msg = await message.channel.send(embed=embed)
            await asyncio.sleep(15)
            try:
                await msg.delete()
            except:
                pass
            return


        # تنفيذ أمر الميوت وتكلم إذا فيه منشن
        if content.startswith("اسكت") and len(parts) >= 2:
            try:
                member = await commands.MemberConverter().convert(ctx, parts[1])
                await self.mute(ctx, member)
            except Exception as e:
                print(f"[ERROR] mute command failed: {e}")

        elif content.startswith("تكلم") and len(parts) >= 2:
            try:
                member = await commands.MemberConverter().convert(ctx, parts[1])
                await self.unmute(ctx, member)
            except Exception as e:
                print(f"[ERROR] unmute command failed: {e}")

async def setup(bot):
    await bot.add_cog(Mute(bot))
