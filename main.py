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
    import discord
from discord.ext import commands
import random
import asyncio
import os

# إعدادات البوت والبريفكس الجديد
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

user_scores = {} 
WIN_THRESHOLD = 5 
ROLE_ID = 1466159040609521969 

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} Is Online!')

# --- نظام الألعاب ---

import discord
from discord.ext import commands
import random
import asyncio
import os

# --- إعدادات البوت والبريفكس ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# --- نظام النقاط والرتبة ---
user_scores = {} 
WIN_THRESHOLD = 25 # الفوز من 25 مرة كما طلبت
ROLE_ID = 1466159040609521969 # ايدي الرتبة الخاصة بك

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} Is Online and Ready!')

# دالة إضافة النقاط والتحقق من الرتبة
# قائمة الكلمات التحفيزية
motivational_words = ["كفو يا بطل! 🔥", "عاش يا أسطورة! 👑", "وحش الإمبراطورية! ✨", "إجابة ذكية! 🧠", "استمر يا مبدع! ⭐"]

async def add_score(ctx, user):
    user_scores[user.id] = user_scores.get(user.id, 0) + 1
    points = user_scores[user.id]
    
    # اختيار كلمة تحفيزية عشوائية
    cheer = random.choice(motivational_words)
    
    await ctx.send(f"{cheer} {user.mention}\nنقاطك الحالية: **{points}/{WIN_THRESHOLD}**")
    
    if points >= WIN_THRESHOLD:
        role = ctx.guild.get_role(ROLE_ID)
        if role and role not in user.roles:
            await user.add_roles(role)
            await ctx.send(f"🎊 **إنجاز عظيم!** {user.mention} وصل لـ 25 فوز وحصل على الرتبة الملكية! 👑")# --- قائمة الألعاب الشاملة ---
@bot.command(name="العاب")
async def games_list(ctx):
    embed = discord.Embed(title="🎮 إمبراطورية الألعاب - كراكن", color=0x2b2d31)
    embed.add_field(name=".خمن", value="خمن الرقم (تلميحات ذكية)", inline=True)
    embed.add_field(name=".فكك", value="جمع الكلمات المبعثرة", inline=True)
    embed.add_field(name=".ترتيب", value="رتب حروف الكلمة", inline=True)
    embed.add_field(name=".عكس", value="اكتب الكلمة بالمقلوب", inline=True)
    embed.add_field(name=".عاصمة", value="أسئلة العواصم العربية", inline=True)
    embed.add_field(name=".علم", value="خمن الدولة من العلم", inline=True)
    embed.add_field(name=".احسب", value="مسائل رياضية سريعة", inline=True)
    embed.add_field(name=".ايموجي", value="خمن الشيء من الايموجي", inline=True)
    embed.add_field(name=".توب", value="قائمة المتصدرين 🏆", inline=False)
    embed.add_field(name=".نقاطي", value="رصيدك الحالي 👤", inline=True)
    embed.set_footer(text=f"اجمع {WIN_THRESHOLD} نقطة لتحصل على الرتبة الملكية! 👑")
    await ctx.send(embed=embed)

# --- الألعاب الذكية ---

@bot.command(name="خمن")
async def guess(ctx):
    number = random.randint(1, 100)
    await ctx.send("🔢 خمنت رقم من **1 لـ 100**، معك 5 محاولات!")
    for i in range(5):
        try:
            msg = await bot.wait_for('message', timeout=20.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            user_guess = int(msg.content)
            if user_guess == number:
                await ctx.send(f"🎯 مبروك! الرقم صحيح وهو **{number}**")
                await add_score(ctx, msg.author)
                return
            elif user_guess < number:
                await ctx.send("↑ **أكبر!**")
            else:
                await ctx.send("↓ **أصغر!**")
        except (ValueError, asyncio.TimeoutError): continue
    await ctx.send(f"📉 انتهت المحاولات! الرقم كان **{number}**")

@bot.command(name="فكك")
async def unwrap(ctx):
    word = random.choice(["كراكن", "ديسكورد", "موز", "سيرفر", "إمبراطورية"])
    await ctx.send(f"🧩 فكك الكلمة: **{' - '.join(list(word))}**")
    try:
        msg = await bot.wait_for('message', timeout=15.0, check=lambda m: m.content == word and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ الوقت خلص، الكلمة هي {word}")

@bot.command(name="ترتيب")
async def scramble(ctx):
    word = random.choice(["بوت", "برمجة", "تفاعل", "العاب", "نظام"])
    scrambled = "".join(random.sample(word, len(word)))
    await ctx.send(f"🔀 رتب الكلمة: **{scrambled}**")
    try:
        msg = await bot.wait_for('message', timeout=20.0, check=lambda m: m.content == word and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ انتهى الوقت! الكلمة: {word}")

@bot.command(name="عكس")
async def reverse(ctx):
    word = random.choice(["كراكن", "مبدع", "أسطورة", "سيرفر"])
    await ctx.send(f"🔄 اكتب الكلمة بالعكس: **{word}**")
    try:
        msg = await bot.wait_for('message', timeout=15.0, check=lambda m: m.content == word[::-1] and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ بطيء! العكس هو {word[::-1]}")

@bot.command(name="عاصمة")
async def capital(ctx):
    data = {"فلسطين": "القدس", "مصر": "القاهرة", "السعودية": "الرياض", "المغرب": "الرباط"}
    country, city = random.choice(list(data.items()))
    await ctx.send(f"🌍 ما عاصمة **{country}**؟")
    try:
        msg = await bot.wait_for('message', timeout=15.0, check=lambda m: m.content == city and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ العاصمة هي {city}")

@bot.command(name="علم")
async def flag(ctx):
    flags = {"🇪🇬": "مصر", "🇸🇦": "السعودية", "🇵🇸": "فلسطين", "🇩🇿": "الجزائر"}
    emoji, country = random.choice(list(flags.items()))
    await ctx.send(f"🚩 صاحب العلم: {emoji} ؟")
    try:
        msg = await bot.wait_for('message', timeout=15.0, check=lambda m: m.content == country and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ الدولة هي {country}")

@bot.command(name="احسب")
async def math(ctx):
    a, b = random.randint(1, 30), random.randint(1, 30)
    res = a + b
    await ctx.send(f"⚡ أسرع حساب: **{a} + {b} = ؟**")
    try:
        msg = await bot.wait_for('message', timeout=10.0, check=lambda m: m.content == str(res) and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ النتيجة هي {res}")

@bot.command(name="ايموجي")
async def emoji_game(ctx):
    quizzes = {"🍎🥧": "فطيرة تفاح", "🦁👑": "الاسد الملك", "🎥🍿": "سينما"}
    emo, ans = random.choice(list(quizzes.items()))
    await ctx.send(f"🤔 خمن من الايموجي: {emo}")
    try:
        msg = await bot.wait_for('message', timeout=20.0, check=lambda m: m.content == ans and m.channel == ctx.channel)
        await add_score(ctx, msg.author)
    except asyncio.TimeoutError:
        await ctx.send(f"⌛ الإجابة هي: {ans}")

# --- الأوامر العامة والـ Leaderboard ---

@bot.command(name="توب")
async def leaderboard(ctx):
    if not user_scores: return await ctx.send("🚫 لا يوجد متصدرين حالياً.")
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 قائمة متصدري كراكن", color=0x2b2d31)
    desc = ""
    for i, (u_id, score) in enumerate(sorted_scores, 1):
        u = bot.get_user(u_id)
        name = u.name if u else f"مستخدم {u_id}"
        desc += f"**#{i}** | {name} - `{score}` نقطة\n"
    embed.description = desc
    await ctx.send(embed=embed)

@bot.command(name="نقاطي")
async def my_score(ctx):
    p = user_scores.get(ctx.author.id, 0)
    await ctx.send(f"👤 {ctx.author.mention} نقاطك: **{p}**")

# قاموس لتخزين إعدادات كل سيرفر (الروم ورابط الخط)
server_configs = {} 

@bot.command(name="الخط")
@commands.has_permissions(manage_channels=True)
async def set_line(ctx, url: str):
    """يحدد الروم ورابط الخط للسيرفر الحالي"""
    server_configs[ctx.guild.id] = {
        "channel_id": ctx.channel.id,
        "line_url": url
    }
    await ctx.send(f"✅ **تم الإعداد بنجاح!**\n📍 الروم: {ctx.channel.mention}\n🖼️ رابط الخط: {url}")

@bot.command(name="حذف_الخط")
@commands.has_permissions(manage_channels=True)
async def remove_line(ctx):
    """إيقاف ميزة الخط في السيرفر"""
    if ctx.guild.id in server_configs:
        del server_configs[ctx.guild.id]
        await ctx.send("🛑 تم إيقاف ميزة الخط التلقائي.")

@bot.event
async def on_message(message):
    # تجاهل رسائل البوتات عشان ما يحصلش تكرار نهائي
    if message.author.bot:
        return

    # التحقق إذا كان السيرفر مفعل الميزة وفي الروم الصحيح
    if message.guild and message.guild.id in server_configs:
        config = server_configs[message.guild.id]
        if message.channel.id == config["channel_id"]:
            # إرسال رابط الخط اللي اتخزن بواسطة الأمر .الخط
            await message.channel.send(config["line_url"])

    # ضروري جداً عشان باقي الأوامر (.العاب، .توب) تفضل شغالة
    await bot.process_commands(message)
    
# سطر التشغيل النهائي
bot.run(os.environ.get('DISCORD_TOKEN'))


