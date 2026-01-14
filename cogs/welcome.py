import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import config
import os
import re

class WelcomeCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_arabic(self, text):
        return re.search(r'[\u0600-\u06FF]', text) is not None

    def get_font(self, member_name):
        try:
            base_path = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
            if self.is_arabic(member_name):
                font_path = os.path.join(base_path, "Amiri-Bold.ttf")
                print("[DEBUG] استخدام خط Amiri للغة العربية")
            else:
                font_path = os.path.join(base_path, "arialbd.ttf")
                print("[DEBUG] استخدام خط Arial للغة الإنجليزية")

            print(f"[DEBUG] مسار الخط: {font_path}")
            return ImageFont.truetype(font_path, 40)

        except Exception as e:
            print(f"[ERROR] فشل تحميل الخط: {e}")
            return ImageFont.load_default()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"[DEBUG] عضو جديد دخل: {member.name}")

        # ✅ إعطاء رتبة Member تلقائيًا
        role = discord.utils.get(member.guild.roles, name="Member")
        if role:
            try:
                await member.add_roles(role, reason="Auto role on join")
                print(f"[DEBUG] تم إعطاء {member.name} رتبة Member")
            except Exception as e:
                print(f"[ERROR] فشل إعطاء الرتبة: {e}")
        else:
            print("[ERROR] لم يتم العثور على رتبة Member")

        # ✅ إرسال بطاقة الترحيب
        print("[DEBUG] محاولة العثور على قناة الترحيب...")
        channel = discord.utils.get(member.guild.text_channels, name=config.WELCOME_CHANNEL)
        print(f"[DEBUG] نتيجة البحث عن القناة: {channel}")
        if not channel:
            print("[DEBUG] لم يتم العثور على قناة الترحيب المحددة في config")
            return

        try:
            # تحميل صورة العضو
            avatar_url = member.display_avatar.replace(size=128).url
            print(f"[DEBUG] رابط الصورة: {avatar_url}")
            response = requests.get(avatar_url)
            avatar_bytes = io.BytesIO(response.content)
            avatar = Image.open(avatar_bytes).convert("RGBA").resize((143, 140))
            print("[DEBUG] تم تحميل صورة العضو")

            # تحميل صورة الخلفية
            background = Image.open("umbrella_card.png").convert("RGBA")
            print("[DEBUG] تم تحميل صورة الخلفية")

            # دمج الصورة داخل البطاقة
            background.paste(avatar, (67, 110), avatar)

            # كتابة اسم العضو
            draw = ImageDraw.Draw(background)
            font = self.get_font(member.name)
            draw.text((90, 290), member.name, font=font, fill=(255, 255, 255))
            print(f"[DEBUG] تم كتابة الاسم: {member.name}")

            # حفظ الصورة المؤقتة
            output = io.BytesIO()
            background.save(output, format="PNG")
            output.seek(0)

            # إرسال الصورة
            file = discord.File(fp=output, filename="welcome.png")
            await channel.send(content=f"**Welcome To Our Society** {member.mention}!", file=file)
            print("[DEBUG] تم إرسال الصورة بنجاح")

        except Exception as e:
            print(f"[ERROR] WelcomeCard failed: {e}")

async def setup(bot):
    await bot.add_cog(WelcomeCard(bot))
