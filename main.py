import discord
from discord.ext import commands, tasks
import asyncio
import random
import os
import json
from datetime import datetime, timedelta

# --- 1. الإعدادات ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# --- 2. الثوابت والـ IDs ---
LINE_URL = "https://media.discordapp.net/attachments/1465707929377443992/1465748212051611889/1769531918511.png"
LOG_CH_ID = 1466903846612635882
LEVEL_CH_ID = 1454791056381186114
CMD_CH_ID = 1454790883923853484
EVENT_CH_ID = 1454787783070716025
AUTO_ROLE_ID = 1460326577727471742
TOP_ROLE_ID = 1466903177801760873
LEVEL_30_ROLE = 1466158338902458368

COLORS = {
    "احمر": 1466906222832652564, "ازرق": 1466906478534201354, 
    "اسود": 1466906615990063111, "بني": 1466906757358944297,
    "اصفر": 1466906955615568005, "اورنج": 1466907014700466280,
    "اخضر": 1466907188701433939, "بنفسجي": 1466907386974572706
}

# --- 3. نظام البيانات ---
DATA_FILE = "kraken_data.json"
user_data = {}
active_color_subs = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"user_data": user_data, "subs": active_color_subs}, f, default=str)

def load_data():
    global user_data, active_color_subs
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                user_data = data.get("user_data", {})
                active_color_subs = data.get("subs", {})
        except: pass

load_data()

def get_user(u_id):
    uid = str(u_id)
    if uid not in user_data:
        user_data[uid] = {
            "points": 0, "warnings": 0, "invites": 0, 
            "xp": 0, "level": 1, "msg_count": 0, "quest_done": False
        }
    return user_data[uid]

# --- 4. الأحداث (Events) ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'👑 Kraken Empire is Online')
    if not auto_event_spawner.is_running(): auto_event_spawner.start()
    if not check_color_expiry.is_running(): check_color_expiry.start()

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    u = get_user(message.author.id)
    
    # نظام اللفل والـ XP
    u["xp"] += random.randint(5, 15)
    u["msg_count"] += 1
    
    # نظام المهمات (150 رسالة)
    if u["msg_count"] >= 150 and not u.get("quest_done", False):
        u["points"] += 50
        u["quest_done"] = True
        await message.channel.send(f"🎊 كفو {message.author.mention}! أنجزت مهمة الـ 150 رسالة وحصلت على 50 نقطة!")
        save_data()

    # الترقية لفل
    next_lvl = u["level"] * 100
    if u["xp"] >= next_lvl:
        u["level"] += 1
        save_data()
        ch = bot.get_channel(LEVEL_CH_ID)
        if ch:
            await ch.send(f"🆙 مبروك {message.author.mention}! وصلت ليفل **{u['level']}**")
        
        # رتبة لفل 30
        if u["level"] >= 30:
            role = message.guild.get_role(LEVEL_30_ROLE)
            if role and role not in message.author.roles:
                await message.author.add_roles(role)

    await bot.process_commands(message)

# --- 5. أوامر الألعاب (Games) ---
@bot.command()
async def رياضيات(ctx):
    if ctx.channel.id != CMD_CH_ID: return
    n1, n2 = random.randint(1, 50), random.randint(1, 50)
    ans = n1 + n2
    await ctx.send(f"🧠 كم ناتج: `{n1} + {n2}` ؟")
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.content == str(ans), timeout=20)
        u = get_user(ctx.author.id); u["points"] += 5; save_data()
        await ctx.send(f"✅ وحش! +5 نقاط"); await ctx.send(LINE_URL)
    except: await ctx.send(f"⏰ خلص الوقت! الإجابة هي {ans}")

@bot.command()
async def عكس(ctx):
    if ctx.channel.id != CMD_CH_ID: return
    word = random.choice(["كراكن", "إمبراطورية", "ديسكورد", "مملكة"])
    await ctx.send(f"🔄 اكتب الكلمة بالعكس: `{word}`")
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.content == word[::-1], timeout=20)
        u = get_user(ctx.author.id); u["points"] += 5; save_data()
        await ctx.send(f"✅ إجابة صحيحة! +5 نقاط"); await ctx.send(LINE_URL)
    except: await ctx.send("⏰ خلص الوقت!")

# --- 6. البنك والحظ ---
@bot.command()
async def حظ(ctx, amount: int):
    if ctx.channel.id != CMD_CH_ID: return
    u = get_user(ctx.author.id)
    if u["points"] < amount: return await ctx.send("❌ نقاطك لا تكفي!")
    
    if random.choice([True, False]):
        u["points"] += amount
        await ctx.send(f"💰 كسبت! رصيدك زاد `{amount}`")
    else:
        u["points"] -= amount
        await ctx.send(f"📉 خسرت! خصمنا منك `{amount}`")
    save_data(); await ctx.send(LINE_URL)

@bot.command()
async def تحويل(ctx, member: discord.Member, amount: int):
    if amount <= 0: return
    u1 = get_user(ctx.author.id)
    u2 = get_user(member.id)
    if u1["points"] < amount: return await ctx.send("❌ رصيدك غير كافٍ")
    u1["points"] -= amount
    u2["points"] += amount
    save_data()
    await ctx.send(f"✅ تم تحويل `{amount}` نقطة إلى {member.mention}")

# --- 7. الإدارة واللوج ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def كيك(ctx, member: discord.Member):
    await member.kick()
    log_ch = bot.get_channel(LOG_CH_ID)
    emb = discord.Embed(title="👞 طرد", description=f"العضو: {member.mention}\nبواسطة: {ctx.author.mention}", color=0xff0000)
    await ctx.send("✅ تم الطرد"); await log_ch.send(embed=emb)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def مسح(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 تم مسح {amount} رسالة", delete_after=5)

# --- 8. المتجر والبروفايل ---
@bot.command()
async def رتبتي(ctx):
    u = get_user(ctx.author.id)
    emb = discord.Embed(title=f"📊 ملف {ctx.author.name}", color=0x3498db)
    emb.add_field(name="المستوى (Level)", value=f"`{u['level']}`")
    emb.add_field(name="النقاط", value=f"`{u['points']}`")
    emb.add_field(name="الرسائل", value=f"`{u['msg_count']}/150` لليوم")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str, duration: str = "1"):
    u = get_user(ctx.author.id)
    if item in COLORS:
        cost = 30 if duration == "شهر" else 300 if duration == "سنة" else 5
        if u["points"] < cost: return await ctx.send("❌ نقاطك لا تكفي")
        role = ctx.guild.get_role(COLORS[item])
        await ctx.author.add_roles(role)
        u["points"] -= cost
        save_data()
        await ctx.send(f"🎨 تم شراء لون {item} بنجاح!")

# --- 9. المهام التلقائية ---
@tasks.loop(hours=1)
async def auto_event_spawner():
    ch = bot.get_channel(EVENT_CH_ID)
    if ch:
        q, a = random.choice([("فكك (كراكن)", "ك ر ا ك ن"), ("جمع (س ي ر ف ر)", "سيرفر")])
        await ch.send(f"🎮 **أسرع شخص يكتب:** {q}")

@tasks.loop(minutes=30)
async def check_color_expiry():
    # نظام بسيط لمسح عداد الرسائل يومياً (تقريبي)
    if datetime.now().hour == 0:
        for uid in user_data:
            user_data[uid]["msg_count"] = 0
            user_data[uid]["quest_done"] = False
        save_data()

# تشغيل
token = os.environ.get('DISCORD_TOKEN')
bot.run(token)
