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

# رومات المنشن السريع عند دخول الأعضاء
GHOST_CHANNELS = [1467618877990244520, 1454565709400248538]

COLORS = {
    "احمر": 1466906222832652564, "ازرق": 1466906478534201354, 
    "اسود": 1466906615990063111, "بني": 1466906757358944297,
    "اصفر": 1466906955615568005, "اورنج": 1466907014700466280,
    "اخضر": 1466907188701433939, "بنفسجي": 1466907386974572706
}

# --- 3. إدارة البيانات ---
DATA_FILE = "kraken_master_data.json"
user_data = {}
auto_line_channels = []

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

# --- 4. الأحداث (Events) ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    if not update_daily_active.is_running(): update_daily_active.start()
    if not voice_points_tracker.is_running(): voice_points_tracker.start()
    print(f"✅ {bot.user} is Ready and Kraken is Awake!")

@bot.event
async def on_member_join(member):
    # منشن سريع في الرومات المحددة ثم مسحه
    for ch_id in GHOST_CHANNELS:
        channel = bot.get_channel(ch_id)
        if channel:
            try:
                msg = await channel.send(f"{member.mention}")
                await msg.delete()
            except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # ميزة الخط التلقائي
    if message.channel.id in auto_line_channels:
        if message.content != LINE_URL:
            await asyncio.sleep(0.5)
            await message.channel.send(LINE_URL)

    u = get_user(message.author.id)
    u["xp"] += random.randint(2, 5)
    if random.random() < 0.3: u["points"] += 1 
    
    # ليفل أب
    next_lvl = u["level"] * 200
    if u["xp"] >= next_lvl:
        u["level"] += 1
        lvl_ch = bot.get_channel(LEVEL_CH_ID)
        if lvl_ch: await lvl_ch.send(f"🆙 مبروك {message.author.mention} وصولك لليفل **{u['level']}**!")

    save_data()
    await bot.process_commands(message)

# --- 5. الأوامر الأساسية ---
@bot.command()
@commands.has_permissions(administrator=True)
async def خط_تلقائي(ctx, state: str = None):
    global auto_line_channels
    if state == "تشغيل":
        if ctx.channel.id not in auto_line_channels:
            auto_line_channels.append(ctx.channel.id)
            save_data()
            await ctx.send("✅ تم تفعيل الخط التلقائي هنا", delete_after=5)
    elif state == "ايقاف":
        if ctx.channel.id in auto_line_channels:
            auto_line_channels.remove(ctx.channel.id)
            save_data()
            await ctx.send("❌ تم إيقاف الخط التلقائي", delete_after=5)
    try: await ctx.message.delete()
    except: pass

@bot.command()
async def توب(ctx):
    if not user_data: return await ctx.send("❌ لا توجد بيانات")
    lb = sorted(user_data.items(), key=lambda x: x[1].get('points', 0), reverse=True)[:5]
    emb = discord.Embed(title="💰 أغنى 5 جبابرة في الكراكن", color=0xffd700)
    for i, (uid, data) in enumerate(lb):
        user = bot.get_user(int(uid))
        name = user.display_name if user else uid
        emb.add_field(name=f"#{i+1}", value=f"**{name}**: `{data.get('points', 0)}`", inline=False)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def رتبتي(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    emb = discord.Embed(title=f"📊 ملف {m.display_name}", color=0x3498db)
    emb.add_field(name="المستوى", value=f"`{u['level']}`")
    emb.add_field(name="النقاط", value=f"`{u['points']}`")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

# --- 6. مهام الوقت ---
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
