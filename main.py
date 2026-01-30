import discord
import os
from discord import app_commands
from discord.ext import commands

# إعدادات الصلاحيات
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"تمت مزامنة جميع الأوامر بنجاح!")

bot = MyBot()

# --- 1. نافذة الـ Embed الاحترافية (Modal) ---
class EmbedModal(discord.ui.Modal, title="إنشاء رسالة إيمبد"):
    embed_title = discord.ui.TextInput(label="عنوان الرسالة", placeholder="اكتب العنوان هنا...", required=False)
    embed_description = discord.ui.TextInput(
        label="محتوى الرسالة", 
        style=discord.TextStyle.paragraph, 
        placeholder="اكتب رسالتك هنا.. يمكنك النزول لسطر جديد براحتك", 
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.embed_title.value,
            description=self.embed_description.value,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="embed", description="إرسال رسالة إيمبد عبر نافذة كتابة")
async def embed(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedModal())

# --- 2. أمر مسح الرسائل (Clear) ---
@bot.tree.command(name="clear", description="مسح عدد معين من الرسائل")
@app_commands.describe(amount="عدد الرسائل المراد مسحها")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم مسح {len(deleted)} رسالة!", ephemeral=True)

# --- 3. أمر معلومات السيرفر (Server) ---
@bot.tree.command(name="server", description="عرض معلومات وإحصائيات السيرفر")
async def server(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"📊 إحصائيات {guild.name}", color=discord.Color.gold())
    embed.add_field(name="👑 صاحب السيرفر", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 الأعضاء", value=str(guild.member_count), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)

# --- 4. الرد التلقائي القديم (اختياري) ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.content == "اهلا":
        await message.channel.send("🔱 إمبراطورية كراكن ترحب بك!")
    await bot.process_commands(message)

bot.run(os.environ.get('DISCORD_TOKEN'))
