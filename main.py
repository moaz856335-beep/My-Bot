import discord
import os
from discord import app_commands
from discord.ext import commands

# 1. إعدادات الصلاحيات
intents = discord.Intents.default()
intents.message_content = True

# 2. تعريف البوت (بناء كلاس عشان مزامنة الأوامر)
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة أوامر الـ Slash مع سيرفرات ديسكورد
        await self.tree.sync()
        print(f"تمت مزامنة الأوامر بنجاح!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"البوت {bot.user} شغال وجاهز!")

# 3. الأمر القديم (الرد التلقائي)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == "اهلا":
        await message.channel.send("🔱 أهلاً بك! إمبراطورية كراكن ترحب بك، كيف أخدمك؟")
    
    await bot.process_commands(message)

# 4. الأمر الجديد (Slash Command الـ Embed)
@bot.tree.command(name="embed", description="اصنع رسالة احترافية مع اختيار اللون")
@app_commands.describe(
    message="اكتب النص الذي تريده داخل المربع",
    color="اختر لون الشريط الجانبي"
)
@app_commands.choices(color=[
    app_commands.Choice(name="بنفسجي (كراكن)", value="purple"),
    app_commands.Choice(name="أحمر", value="red"),
    app_commands.Choice(name="أخضر", value="green"),
    app_commands.Choice(name="أزرق", value="blue"),
    app_commands.Choice(name="ذهبي", value="gold")
])
async def embed(interaction: discord.Interaction, message: str, color: app_commands.Choice[str]):
    # خريطة الألوان بناءً على اختيارك
    colors_map = {
        "purple": discord.Color.from_str("#7e22ce"),
        "red": discord.Color.red(),
        "green": discord.Color.green(),
        "blue": discord.Color.blue(),
        "gold": discord.Color.gold()
    }
    
    selected_color = colors_map.get(color.value)

    custom_embed = discord.Embed(
        description=f"**{message}**", 
        color=selected_color
    )
    # إرسال الرسالة الاحترافية
    await interaction.response.send_message(embed=custom_embed)

# 5. تشغيل البوت بالتوكن السري
bot.run(os.environ.get('DISCORD_TOKEN'))
