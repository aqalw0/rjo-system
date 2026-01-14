import discord
from discord.ext import commands
import asyncio

ALLOWED_CLEAR_ROLES = ["Superior", "Sentinal", "Admins"]
ALLOWED_ROLE_ROLES = ["Superior", "Sentinal"]

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        parts = content.split()

        # ✅ أمر "مسح"
        if parts[0] == "مسح":
            author = message.author
            guild = message.guild

            if not (
                author.id == guild.owner_id or
                author.guild_permissions.manage_messages or
                any(role.name in ALLOWED_CLEAR_ROLES for role in author.roles)
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

        # ✅ أمر "رول"
        if parts[0] == "رول" and len(parts) >= 3:
            ctx = await self.bot.get_context(message)
            try:
                member = await commands.MemberConverter().convert(ctx, parts[1])
                role_name = " ".join(parts[2:])
                role = discord.utils.get(message.guild.roles, name=role_name)

                if not role:
                    return

                author = message.author
                guild = message.guild

                # تحقق من صلاحية الشخص اللي يطلب
                has_permission = (
                    author.id == guild.owner_id or
                    author.guild_permissions.administrator or
                    any(r.name in ALLOWED_ROLE_ROLES for r in author.roles)
                )
                if not has_permission:
                    return

                # تحقق من أن رتبته أعلى من الرتبة المطلوبة
                author_top = max((r.position for r in author.roles), default=0)
                if author_top <= role.position:
                    return

                # تحقق من أن البوت يقدر يعطي أو يشيل الرتبة
                bot_top = guild.me.top_role.position
                if role.position >= bot_top:
                    return

                # ✅ إذا العضو عنده الرتبة → نشيلها
                member_roles = [r.id for r in member.roles]
                if role.id in member_roles:
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

async def setup(bot):
    await bot.add_cog(Commands(bot))
