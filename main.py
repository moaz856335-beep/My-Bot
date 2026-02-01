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
LOG_CH_ID = 1466903846612635882
LEVEL_CH_ID = 1454791056381186114
AUTO_ROLE_ID = 1460326577727471742
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
user_messages = {} # للسبام
spam_warns = {}    # تحذيرات السبام

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                user_data = json.load(f)
        except: pass

load_data()

def get_user(u_id):
    uid = str(u_id)
    if uid not in user_data:
        user_data[uid] = {
            "points": 0, "xp": 0, "level": 1, 
            "msg_count": 0, "daily_claimed": None,
            "voice_start": None
        }
    return user_data[uid]

# --- 4. المهام التلقائية (Daily Active & Voice) ---

@tasks.loop(hours=24)
async def update_daily_active():
    guild = bot.get_guild(your_guild_id_here) # ضع ID سيرفرك هنا
    if not guild: return
    
    # البحث عن الأكثر تفاعلاً
    top_user = None
    max_msgs = -1
    for uid, data in user_data.items():
        if data.get("msg_count", 0) > max_msgs:
            max_msgs = data["msg_count"]
            top_user = uid
            
    role = guild.get_role(DAILY_ACTIVE_ROLE)
    if role:
        # سحب الرتبة من الجميع
        for member in role.members:
            await member.remove_roles(role)
        # إعطاؤها للفائز
        winner = guild.get_member(int(top_user))
        if winner:
            await winner.add_roles(role)
            await guild.system_channel.send(f"👑 **ملك التفاعل اليوم:** {winner.mention} بـ {max_msgs} رسالة!")
    
    # تصفير العداد لليوم الجديد
    for uid in user_data:
        user_data[uid]["msg_count"] = 0
    save_data()

@tasks.loop(minutes=10)
async def voice_points_tracker():
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if not member.bot and not (member.voice.self_deaf or member.voice.self_mute):
                    u = get_user(member.id)
                    u["points"] += 2 # نقطتين كل 10 دقائق فويس
    save_data()

# --- 5. الأحداث (Anti-Spam & XP) ---

@bot.event
async def on_message(message):
    if message.author.bot: return
    u = get_user(message.author.id)

    # --- نظام السبام المتدرج ---
    uid = message.author.id
    now = datetime.now()
    if uid not in user_messages: user_messages[uid] = []
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < timedelta(seconds=5)]

    if len(user_messages[uid]) > 5:
        if uid not in spam_warns:
            spam_warns[uid] = now
            await message.channel.send(f"⚠️ {message.author.mention} خفف سبام عشان ما تاخد تايم أوت!", delete_after=5)
        else:
            if now - spam_warns[uid] < timedelta(minutes=1): # لو كمل في أقل من دقيقة
                await message.author.timeout(timedelta(minutes=10), reason="سبام متكرر")
                await message.channel.send(f"🚫 تم إسكات {message.author.mention} لمدة 10 دقائق بسبب السبام.")
                del spam_warns[uid]
                return
    
    # --- زيادة الـ XP والنقاط ---
    u["xp"] += random.randint(2, 5)
    if random.random() < 0.3: u["points"] += 1 # صعوبة في النقاط
    u["msg_count"] += 1
    
    save_data()
    await bot.process_commands(message)

# --- 6. الأوامر (المتجر، اليومي، البروفايل) ---

@bot.command()
async def متجر(ctx):
    emb = discord.Embed(title="🏪 متجر إمبراطورية كراكن", description="اشتري رتبتك بالنقاط اللي جمعتها من تفاعلك!", color=0x2ecc71)
    emb.add_field(name="🎨 الألوان", value="`.شراء اسم_اللون` \nالسعر: **300 نقطة**", inline=False)
    emb.add_field(name="🔱 رتب فخمة", value=f"**Legendary**: 500 نقطة (`.شراء legendary`)\n**Kraken Elite**: 1000 نقطة (`.شراء elite`)", inline=False)
    emb.set_footer(text="طريقة الشراء: .شراء [الاسم]")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str):
    u = get_user(ctx.author.id)
    item = item.lower()
    
    # شراء الألوان
    if item in COLORS:
        cost = 300
        if u["points"] < cost: return await ctx.send("❌ نقاطك لا تكفي (300 نقطة)")
        role = ctx.guild.get_role(COLORS[item])
        await ctx.author.add_roles(role); u["points"] -= cost
        await ctx.send(f"✅ مبروك! اشتريت لون {item}")
    
    # شراء الرتب الخاصة
    elif item == "legendary":
        if u["points"] < 500: return await ctx.send("❌ تحتاج 500 نقطة")
        await ctx.author.add_roles(ctx.guild.get_role(LEGENDARY_ROLE))
        u["points"] -= 500; await ctx.send("🔥 أصبحت الآن Legendary!")
        
    elif item == "elite":
        if u["points"] < 1000: return await ctx.send("❌ تحتاج 1000 نقطة")
        await ctx.author.add_roles(ctx.guild.get_role(ELITE_ROLE))
        u["points"] -= 1000; await ctx.send("👑 كفو! وصلت لرتبة Kraken Elite")
    
    save_data()

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    last_claim = u.get("daily_claimed")
    
    if last_claim and now - datetime.fromisoformat(last_claim) < timedelta(days=1):
        return await ctx.send("❌ أخذت هديتك اليوم، ارجع بكرة!")
    
    gift = random.randint(10, 30)
    u["points"] += gift
    u["daily_claimed"] = now.isoformat()
    save_data()
    await ctx.send(f"🎁 فتحت الصندوق اليومي ولقيت فيه **{gift}** نقطة!")

@bot.command()
async def رتبتي(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    emb = discord.Embed(title=f"📊 ملف {m.display_name}", color=0x3498db)
    emb.add_field(name="المستوى 🆙", value=f"`{u['level']}`", inline=True)
    emb.add_field(name="النقاط 💰", value=f"`{u['points']}`", inline=True)
    emb.set_thumbnail(url=m.display_avatar.url)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    update_daily_active.start()
    voice_points_tracker.start()

token = os.environ.get('DISCORD_TOKEN')
bot.run(token)
