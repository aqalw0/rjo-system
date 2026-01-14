import discord
from discord.ext import commands
import asyncio

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        parts = content.split()

        # ============================
        #        أمر "مسح"
        # ============================
        if parts[0] == "مسح":
            author = message.author
            guild = message.guild

            if not (
                author.id == guild.owner_id or
                author.guild_permissions.administrator or
                author.guild_permissions.manage_messages
            ):
                return

            try:
                amount = int(parts[1]) if len(parts) >= 2 else 100
                amount = min(amount, 1000)
            except:
                return

            try:
                await message.channel.purge(limit=amount + 1)
                await message.add_reaction("✅")
            except:
                try:
                    await message.add_reaction("❌")
                except:
                    pass

            return

        # ============================
        #        أمر "رول"
        # ============================
        if parts[0] == "رول" and len(parts) >= 3:
            try:
                ctx = await self.bot.get_context(message)
                member = await commands.MemberConverter().convert(ctx, parts[1])
                role_name = " ".join(parts[2:])
                role = discord.utils.get(message.guild.roles, name=role_name)

                if not role:
                    return

                author = message.author
                guild = message.guild

                # 🔥 فقط اللي عنده manage_roles
                if not (
                    author.id == guild.owner_id or
                    author.guild_permissions.administrator or
                    author.guild_permissions.manage_roles
                ):
                    return

                # رتبة الشخص أعلى من الرتبة المطلوبة
                author_top = max((r.position for r in author.roles), default=0)
                if author_top <= role.position:
                    return

                # البوت يقدر يعطي/يشيل الرتبة
                bot_top = guild.me.top_role.position
                if role.position >= bot_top:
                    return

                # إضافة/إزالة الرتبة
                if role in member.roles:
                    await member.remove_roles(role, reason=f"تم إزالة الرتبة بواسطة {author}")
                else:
                    await member.add_roles(role, reason=f"تم إعطاء الرتبة بواسطة {author}")

                await message.add_reaction("✅")

            except Exception as e:
                print(f"❌ خطأ في أمر رول: {e}")
                try:
                    await message.add_reaction("❌")
                except:
                    pass

        # 👇 مهم جدًا — يسمح للأوامر العادية بالعمل
        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(Commands(bot))
