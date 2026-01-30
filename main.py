import discord
import os
from discord import app_commands
from discord.ext import commands

# إعدادات الصلاحيات الأساسية
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة الأوامر لتظهر في قائمة الـ (/)
        await self.tree.sync()
        print(f"تمت مزامنة الأوامر: clear, server, embed")

bot = MyBot()

# --- 1. أمر مسح الرسائل (Clear) ---
@bot.tree.command(name="clear", description="مسح عدد معين من الرسائل من القناة")
@app_commands.describe(amount="اكتب عدد الرسائل (مثلاً: 10)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    # الرد المبدئي عشان البوت ما يعلقش أثناء المسح
    await interaction.response.defer(ephemeral=True) 
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم تنظيف القناة ومسح {len(deleted)} رسالة!", ephemeral=True)

# --- 2. أمر معلومات السيرفر (Server Info) ---
@bot.tree.command(name="server", description="عرض تفاصيل وإحصائيات السيرفر")
async def server_info(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"📊 إحصائيات سيرفر {guild.name}", 
        color=discord.Color.blue()
    )
    embed.add_field(name="👑 صاحب السيرفر", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 عدد الأعضاء", value=f"{guild.member_count} عضو", inline=True)
    embed.add_field(name="🆔 معرف السيرفر", value=guild.id, inline=False)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await interaction.response.send_message(embed=embed)

# --- 3. أمر الـ Embed (النسخة المختصرة) ---
@bot.tree.command(name="embed", description="إرسال نص داخل إطار ملون")
async def embed(interaction: discord.Interaction, message: str):
    new_embed = discord.Embed(description=message, color=discord.Color.green())
    await interaction.response.send_message(embed=new_embed)

# تشغيل البوت
bot.run(os.environ.get('DISCORD_TOKEN'))
