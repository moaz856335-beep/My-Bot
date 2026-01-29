import discord
import os
from discord.ext import commands

# إعدادات الصلاحيات
intents = discord.Intents.default()
intents.message_content = True

# تعريف البوت بالبادئة "!"
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # الرسالة اللي بتظهر في الـ Logs لما البوت يفتح
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")

@bot.event
async def on_message(message):
    # عشان البوت ميردش على نفسه
    if message.author == bot.user:
        return

    # الرد على كلمة "اهلا" بنفس نص الصورة بالظبط
    if message.content == "اهلا":
        await message.channel.send("🔱 أهلاً بك! إمبراطورية كراكن ترحب بك، كيف أخدمك؟")

    # تشغيل الأوامر الأخرى لو أضفتها مستقبلاً
    await bot.process_commands(message)

# تشغيل البوت باستخدام التوكن السري من إعدادات Railway
bot.run(os.environ.get('DISCORD_TOKEN'))
