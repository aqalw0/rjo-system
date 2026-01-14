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

    # -----------------------------
    #  فحص إذا الاسم عربي أو لا
    # -----------------------------
    def is_arabic(self, text):
        return re.search(r'[\u0600-\u06FF]', text) is not None

    # -----------------------------
    #  اختيار الخط المناسب
    # -----------------------------
    def get_font(self, member_name):
        try:
            base_path = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")

            if self.is_arabic(member_name):
                font_path = os.path.join(base_path, "Amiri-Bold.ttf")
            else:
                font_path = os.path.join(base_path, "arialbd.ttf")

            return ImageFont.truetype(font_path, 40)

        except Exception as e:
            print(f"[ERROR] فشل تحميل الخط: {e}")
            return ImageFont.load_default()

    # -----------------------------
    #  الحدث الرئيسي
    # -----------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"[DEBUG] عضو جديد دخل: {member.name}")

        # -----------------------------
        #  إعطاء رتبة Member تلقائيًا
        # -----------------------------
        role = discord.utils.get(member.guild.roles, name="Member")
        if role:
            try:
                await member.add_roles(role, reason="Auto role on join")
            except Exception as e:
                print(f"[ERROR] فشل إعطاء الرتبة: {e}")

        # -----------------------------
        #  العثور على قناة الترحيب
        # -----------------------------
        channel = discord.utils.get(member.guild.text_channels, name=config.WELCOME_CHANNEL)
        if not channel:
            print("[ERROR] لم يتم العثور على قناة الترحيب")
            return

        try:
            # -----------------------------
            #  تحميل صورة العضو
            # -----------------------------
            avatar_url = member.display_avatar.replace(size=256).url
            response = requests.get(avatar_url)
            avatar_bytes = io.BytesIO(response.content)
            avatar = Image.open(avatar_bytes).convert("RGBA").resize((143, 140))

            # -----------------------------
            #  تحميل الخلفية
            # -----------------------------
            bg_path = os.path.join(os.path.dirname(__file__), "umbrella_card.png")
            background = Image.open(bg_path).convert("RGBA")

            # -----------------------------
            #  دمج الصورة
            # -----------------------------
            background.paste(avatar, (67, 110), avatar)

            # -----------------------------
            #  كتابة اسم العضو
            # -----------------------------
            draw = ImageDraw.Draw(background)
            font = self.get_font(member.name)
            draw.text((90, 290), member.name, font=font, fill=(255, 255, 255))

            # -----------------------------
            #  حفظ الصورة وإرسالها
            # -----------------------------
            output = io.BytesIO()
            background.save(output, format="PNG")
            output.seek(0)

            file = discord.File(fp=output, filename="welcome.png")
            await channel.send(
                content=f"**Welcome To Our Society** {member.mention}!",
                file=file
            )

        except Exception as e:
            print(f"[ERROR] WelcomeCard failed: {e}")

async def setup(bot):
    await bot.add_cog(WelcomeCard(bot))
