import discord
import os
import random
import asyncio
from discord import app_commands
from discord.ext import commands

# 1. إعدادات الصلاحيات
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.invites = True 

class KrakenBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", intents=intents)
        # تخزين الإعدادات (في الذاكرة حالياً)
        self.auto_replies = {} # {channel_id: "الرسالة"}
        self.invites_cache = {}

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ تم تفعيل نظام التحكم بالردود التلقائية!")

bot = KrakenBot()

# --- 2. أمر ضبط الرد التلقائي (Slash Command) ---
@bot.tree.command(name="set_auto_reply", description="ضبط رسالة رد تلقائي لروم محدد")
@app_commands.describe(channel="اختر الروم", message="اكتب الرسالة التي سيقولها البوت بعد كل كلمة")
@app_commands.checks.has_permissions(manage_channels=True)
async def set_auto(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    # حفظ الروم والرسالة في ذاكرة البوت
    bot.auto_replies[channel.id] = message
    
    embed = discord.Embed(title="✅ تم الضبط بنجاح", color=discord.Color.green())
    embed.add_field(name="الروم", value=channel.mention)
    embed.add_field(name="الرسالة", value=message)
    await interaction.response.send_message(embed=embed)

# أمر لإلغاء الرد التلقائي من روم
@bot.tree.command(name="remove_auto_reply", description="إلغاء الرد التلقائي من روم معين")
@app_commands.describe(channel="اختر الروم لإلغاء الرد منه")
@app_commands.checks.has_permissions(manage_channels=True)
async def remove_auto(interaction: discord.Interaction, channel: discord.TextChannel):
    if channel.id in bot.auto_replies:
        del bot.auto_replies[channel.id]
        await interaction.response.send_message(f"🗑️ تم إلغاء الرد التلقائي من روم {channel.mention}")
    else:
        await interaction.response.send_message(f"❌ هذا الروم ليس به رد تلقائي مبرمج.")

# --- 3. مراقب الرسائل للرد التلقائي ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # التأكد لو الروم الحالي مسجل في الردود التلقائية
    if message.channel.id in bot.auto_replies:
        reply_text = bot.auto_replies[message.channel.id]
        await message.channel.send(reply_text)

    await bot.process_commands(message)

# --- 4. أوامر الإدارة (Kick, Mute, Clear) ---
@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "غير محدد"):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"✅ تم طرد {user.name}")

@bot.tree.command(name="mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, user: discord.Member, minutes: int):
    await user.timeout(asyncio.timedelta(minutes=minutes))
    await interaction.response.send_message(f"🔇 تم إسكات {user.mention} لمدة {minutes} دقيقة.")

@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم مسح {amount} رسالة.")

# --- 5. أمر .inv ونظام الانفايت ---
# --- 5. نظام الانفايت (inv) وأحداث الأعضاء ---

@bot.command(name="inv")
async def inv_check(ctx, member: discord.Member = None):
    member = member or ctx.author
    invites = await ctx.guild.invites()
    total = sum(i.uses for i in invites if i.inviter == member)
    await ctx.send(f"📊 عدد دعوات {member.mention} هو: **{total}**")

@bot.event
async def on_member_join(member):
    # الجزء بتاع المنشن السريع
    # استبدل الأرقام دي بـ IDs الرومات الحقيقية من سيرفرك
    important_channels = [ 1454565709400248538 , 1454787783070716025 ] 
    
    for channel_id in important_channels:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                temp_msg = await channel.send(f"شيك هنا {member.mention}")
                await asyncio.sleep(1)
                await temp_msg.delete()
            except:
                pass

    # تسجيل دخول العضو في الكونسول
    print(f"عضو جديد دخل السيرفر: {member.name}")

# سطر تشغيل البوت (يجب أن يكون دائماً آخر سطر في الملف)
bot.run(os.environ.get('DISCORD_TOKEN'))
