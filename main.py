import discord
from discord.ext import commands, tasks
from discord import ui
import asyncio
import random
import os
import json
from datetime import datetime, timedelta

# --- 1. الإعدادات والـ Intents ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# --- 2. الثوابت والـ IDs ---
LOG_CH_ID = 1466903846612635882
LEVEL_CH_ID = 1454791056381186114
DAILY_ACTIVE_ROLE = 1467539771692941535
LEGENDARY_ROLE = 1466159040609521969
ELITE_ROLE = 1466159241537655049
LINE_URL = "https://media.discordapp.net/attachments/1465707929377443992/1465748212051611889/1769531918511.png"

COLORS = {
    "احمر": 1466906222832652564, "ازرق": 1466906478534201354, 
    "اسود": 1466906615990063111, "بني": 1466906757358944297,
    "اصفر": 1466906955615568005, "اورنج": 1466907014700466280,
    "اخضر": 1466907188701433939, "بنفسجي": 1466907386974572706
}

# --- 3. إدارة البيانات ---
DATA_FILE = "kraken_master_data.json"
user_data = {}
auto_line_channels = [] # تم إضافة قائمة رومات الخط هنا
user_messages = {} 
spam_warns = {}    

def save_data():
    data = {"users": user_data, "line_channels": auto_line_channels}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    global user_data, auto_line_channels
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                content = json.load(f)
                user_data = content.get("users", {})
                auto_line_channels = content.get("line_channels", [])
        except: pass

load_data()

def get_user(u_id):
    uid = str(u_id)
    if uid not in user_data:
        user_data[uid] = {"points": 0, "xp": 0, "level": 1, "msg_count": 0, "daily_claimed": None}
    return user_data[uid]

# --- 4. معالجة الأخطاء ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ ناقص بيانات! تأكد من كتابة الأمر صح.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ مش لاقي العضو ده.")

# --- 5. الأحداث (On Message) ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    if not update_daily_active.is_running(): update_daily_active.start()
    if not voice_points_tracker.is_running(): voice_points_tracker.start()
    print(f"✅ {bot.user} is Ready!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # --- ميزة الخط التلقائي ---
    if message.channel.id in auto_line_channels:
        if message.content != LINE_URL:
            await asyncio.sleep(0.5)
            await message.channel.send(LINE_URL)

    u = get_user(message.author.id)
    uid = message.author.id
    now = datetime.now()

    # نظام السبام
    if uid not in user_messages: user_messages[uid] = []
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < timedelta(seconds=5)]
    if len(user_messages[uid]) > 5: return # تجاهل الرسائل لو سبام

    # حساب النقاط
    u["xp"] += random.randint(2, 5)
    if random.random() < 0.3: u["points"] += 1 
    u["msg_count"] += 1
    
    # ليفل أب
    next_lvl = u["level"] * 200
    if u["xp"] >= next_lvl:
        u["level"] += 1
        lvl_ch = bot.get_channel(LEVEL_CH_ID)
        if lvl_ch: await lvl_ch.send(f"🆙 مبروك {message.author.mention} وصولك لليفل **{u['level']}**!")

    save_data()
    await bot.process_commands(message)

# --- 6. الأوامر ---
@bot.command()
async def تحويل(ctx, member: discord.Member, amount: int):
    u1, u2 = get_user(ctx.author.id), get_user(member.id)
    if amount <= 0 or u1["points"] < amount: return await ctx.send("❌ رصيدك لا يكفي")
    u1["points"] -= amount; u2["points"] += amount
    save_data(); await ctx.send(f"✅ تم تحويل `{amount}` إلى {member.mention}")

@bot.command()
async def رتبتي(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    emb = discord.Embed(title=f"📊 ملف {m.display_name}", color=0x3498db)
    emb.add_field(name="المستوى 🆙", value=f"`{u['level']}`")
    emb.add_field(name="النقاط 💰", value=f"`{u['points']}`")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    last = u.get("daily_claimed")
    if last and now - datetime.fromisoformat(last) < timedelta(days=1):
        return await ctx.send("❌ ارجع بكرة!")
    gift = random.randint(10, 30)
    u["points"] += gift; u["daily_claimed"] = now.isoformat()
    save_data(); await ctx.send(f"🎁 حصلت على {gift} نقطة")

@bot.command()
async def متجر(ctx):
    emb = discord.Embed(title="🏪 المتجر", description="`.شراء [الاسم]`", color=0x2ecc71)
    emb.add_field(name="🎨 الألوان (300)", value="احمر، ازرق، اسود، بني، اصفر")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str):
    u = get_user(ctx.author.id)
    if item in COLORS and u["points"] >= 300:
        await ctx.author.add_roles(ctx.guild.get_role(COLORS[item]))
        u["points"] -= 300; save_data(); await ctx.send(f"🎨 تم الشراء")

@bot.command()
@commands.has_permissions(administrator=True)
async def خط_تلقائي(ctx, state: str = None):
    global auto_line_channels
    if state == "تشغيل":
        if ctx.channel.id not in auto_line_channels:
            auto_line_channels.append(ctx.channel.id)
            save_data()
            await ctx.send("✅ تم التفعيل", delete_after=5)
    elif state == "ايقاف":
        if ctx.channel.id in auto_line_channels:
            auto_line_channels.remove(ctx.channel.id)
            save_data()
            await ctx.send("❌ تم الإيقاف", delete_after=5)
    else:
        await ctx.send("❓ `.خط_تلقائي تشغيل` أو `ايقاف`", delete_after=5)
    try: await ctx.message.delete()
    except: pass

@bot.command()
async def توب(ctx):
    if not user_data: return await ctx.send("❌ لا بيانات")
    lb = sorted(user_data.items(), key=lambda x: x[1].get('points', 0), reverse=True)[:5]
    emb = discord.Embed(title="💰 قائمة الأغنياء", color=0xffd700)
    for i, (uid, data) in enumerate(lb):
        user = bot.get_user(int(uid))
        name = user.display_name if user else uid
        emb.add_field(name=f"#{i+1}", value=f"**{name}**: `{data.get('points', 0)}`", inline=False)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

# --- 7. مهام الوقت ---
@tasks.loop(minutes=10)
async def voice_points_tracker():
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for m in vc.members:
                if not m.bot and not (m.voice.self_deaf or m.voice.self_mute):
                    u = get_user(m.id); u["points"] += 2
    save_data()

@tasks.loop(hours=24)
async def update_daily_active():
    for uid in user_data:
        if isinstance(user_data[uid], dict): user_data[uid]["msg_count"] = 0
    save_data()

token = os.environ.get('DISCORD_TOKEN')
bot.run(token)
