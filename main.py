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

# --- 2. حفظ البيانات (JSON) ---
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
        except: user_data, active_color_subs = {}, {}
    else: user_data, active_color_subs = {}, {}

load_data()

# --- 3. الثوابت ---
LINE_URL = "https://media.discordapp.net/attachments/1465707929377443992/1465748212051611889/1769531918511.png"
LOG_CH_ID = 1466903846612635882
SUGGEST_CH_ID = 1466905596732113224
EVENT_CH_ID = 1454787783070716025
MENTION_CHANNELS = [1454565709400248538, 1454787783070716025]
AUTO_ROLE_ID = 1460326577727471742
TOP_ROLE_ID = 1466903177801760873

COLORS = {
    "احمر": 1466906222832652564, "ازرق": 1466906478534201354, 
    "اسود": 1466906615990063111, "بني": 1466906757358944297,
    "اصفر": 1466906955615568005, "اورنج": 1466907014700466280,
    "اخضر": 1466907188701433939, "بنفسجي": 1466907386974572706
}

@bot.event
async def on_ready():
    await bot.tree.sync() 
    print(f'👑 Kraken Empire is Online')
    check_color_expiry.start()
    auto_event_spawner.start()
    update_top_role.start()

def get_user(u_id):
    uid = str(u_id)
    if uid not in user_data:
        user_data[uid] = {"points": 0, "warnings": 0, "invites": 0}
    return user_data[uid]

@bot.event
async def on_member_join(member):
    r = member.guild.get_role(AUTO_ROLE_ID)
    if r: await member.add_roles(r)
    for cid in MENTION_CHANNELS:
        ch = member.guild.get_channel(cid)
        if ch:
            m = await ch.send(member.mention); await asyncio.sleep(1); await m.delete()

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# --- 4. أوامر الإدارة ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def كيك(ctx, member: discord.Member):
    await member.kick()
    emb = discord.Embed(title="👞 طرد عضو", description=f"تم طرد {member.mention} بنجاح", color=0xe74c3c)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def تايم(ctx, member: discord.Member, minutes: int):
    await member.timeout(timedelta(minutes=minutes))
    emb = discord.Embed(title="⏳ إسكات عضو", description=f"تم إعطاء تايم لـ {member.mention} لمدة {minutes} دقيقة", color=0xf1c40f)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def مسح(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    emb = discord.Embed(title="🧹 تنظيف الشات", description=f"تم مسح `{amount}` رسالة بنجاح", color=0x3498db)
    await ctx.send(embed=emb, delete_after=5)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def تحذير(ctx, member: discord.Member):
    u = get_user(member.id)
    u["warnings"] += 1
    save_data()
    await ctx.send(f"⚠️ {member.mention} تم تحذيرك. عدد تحذيراتك: {u['warnings']}")
    await ctx.send(LINE_URL)

# --- 5. نظام الشوب والانفايت ---
@bot.command()
async def شراء(ctx, item: str, duration: str = "1"):
    u = get_user(ctx.author.id)
    emb = discord.Embed(color=0x3498db)
    if item in COLORS:
        try:
            days = 30 if duration == "شهر" else 365 if duration == "سنة" else int(duration)
            cost = 30 if duration == "شهر" else 300 if duration == "سنة" else days
            if u["points"] < cost: 
                emb.description = f"❌ نقاطك لا تكفي (التكلفة: {cost})"
                return await ctx.send(embed=emb)
            await ctx.author.add_roles(ctx.guild.get_role(COLORS[item]))
            active_color_subs[str(ctx.author.id)] = {"role_id": COLORS[item], "expiry": (datetime.now() + timedelta(days=days)).isoformat()}
            u["points"] -= cost
            emb.description = f"🎨 تم تفعيل لون {item} لـ {duration}!"
            save_data()
        except: emb.description = "❌ خطأ في المدة"
    else:
        emb.description = "❌ المنتج غير موجود"
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command(name="البيست")
async def leaderboard(ctx):
    top_users = sorted(user_data.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    emb = discord.Embed(title="🏆 قائمة أساطير الإمبراطورية", color=0xffd700)
    desc = ""
    for i, (uid, data) in enumerate(top_users, 1):
        m = ctx.guild.get_member(int(uid))
        name = m.display_name if m else f"عضو ({uid})"
        desc += f"**#{i}** | {name} - `{data['points']}` نقطة\n"
    emb.description = desc
    await ctx.send(embed=emb)

@bot.command()
async def انفايت(ctx, m: discord.Member = None):
    m = m or ctx.author; invs = await ctx.guild.invites()
    count = sum(i.uses for i in invs if i.inviter == m)
    emb = discord.Embed(title="📊 الدعوات", description=f"العضو: {m.mention}\nالدعوات: `{count}`", color=0x9b59b6)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id); u["points"] += 3; save_data()
    await ctx.send(f"💰 {ctx.author.mention} حصلت على 3 نقاط!"); await ctx.send(LINE_URL)

# --- 6. المهام التلقائية ---
@tasks.loop(hours=1)
async def auto_event_spawner():
    ch = bot.get_channel(EVENT_CH_ID)
    if ch:
        q, a = random.choice([("فكك (كراكن)", "ك ر ا ك ن"), ("جمع (س ي ر ف ر)", "سيرفر")])
        await ch.send(f"🎮 **أسرع شخص يكتب:** {q}")
        def check(m): return m.channel == ch and m.content == a
        try:
            w = await bot.wait_for('message', check=check, timeout=60)
            u = get_user(w.author.id); u["points"] += 5; save_data()
            await ch.send(f"🎉 كفو {w.author.mention}! (+5 نقاط)")
        except: pass

@tasks.loop(minutes=10)
async def check_color_expiry():
    now = datetime.now()
    for uid, d in list(active_color_subs.items()):
        if now > datetime.fromisoformat(d["expiry"]):
            for g in bot.guilds:
                m = g.get_member(int(uid))
                if m: 
                    r = g.get_role(d["role_id"])
                    if r: await m.remove_roles(r)
            del active_color_subs[uid]; save_data()

@tasks.loop(minutes=5)
async def update_top_role():
    if not user_data: return
    top_id = max(user_data, key=lambda x: user_data[x].get('points', 0))
    for g in bot.guilds:
        r = g.get_role(TOP_ROLE_ID)
        if r:
            tm = g.get_member(int(top_id))
            if tm and r not in tm.roles: await tm.add_roles(r)

# --- 7. الأوامر السلاش (Slash) ---
@bot.tree.command(name="clear", description="مسح الرسائل")
async def clear_slash(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 تم مسح {amount} رسالة", ephemeral=True)

# تشغيل البوت
token = os.environ.get('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ التوكن ناقص في Variables!")
