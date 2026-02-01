import discord
from discord.ext import commands, tasks
from discord import ui, app_commands
import asyncio, random, os, json
from datetime import datetime, timedelta

# --- 1. الإعدادات والبيانات ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

DATA_FILE = "kraken_master_data.json"
user_data = {}
auto_line_channels = []
user_messages = {} 
spam_warns = {}    

# ثوابت (تأكد من الـ IDs في سيرفرك)
LEVEL_CH_ID = 1454791056381186114
DAILY_ACTIVE_ROLE_ID = 1467539771692941535
LVL_30_ROLE_ID = 1466159040609521969
SUGGESTIONS_CH_ID = 1467618877990244520
LINE_URL = "https://media.discordapp.net/attachments/1465707929377443992/1465748212051611889/1769531918511.png"
GHOST_CHANNELS = [1467618877990244520, 1454565709400248538]
COLORS = {"احمر": 1466906222832652564, "ازرق": 1466906478534201354, "اسود": 1466906615990063111, "اخضر": 1466907188701433939}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"users": user_data, "line_channels": auto_line_channels}, f)

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

# --- 2. نافذة الاقتراحات (Modal) ---
class SuggestionModal(ui.Modal, title='تقديم اقتراح'):
    suggestion = ui.TextInput(label='اقتراحك', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, it: discord.Interaction):
        ch = bot.get_channel(SUGGESTIONS_CH_ID)
        emb = discord.Embed(title="💡 اقتراح جديد", description=self.suggestion.value, color=0x00ffcc)
        emb.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
        m = await ch.send(embed=emb)
        await m.add_reaction("✅"); await m.add_reaction("❌")
        await it.response.send_message("✅ تم إرسال اقتراحك!", ephemeral=True)

# --- 3. الأحداث الأساسية ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    if not update_daily_active.is_running(): update_daily_active.start()
    if not voice_points_tracker.is_running(): voice_points_tracker.start()
    print(f"✅ {bot.user} جاهز!")

@bot.event
async def on_member_join(member):
    for cid in GHOST_CHANNELS:
        ch = bot.get_channel(cid)
        if ch: m = await ch.send(member.mention); await m.delete()

@bot.event
async def on_message(message):
    if message.author.bot: return
    uid = message.author.id
    now = datetime.now()

    # نظام السبام والحماية
    if uid not in user_messages: user_messages[uid] = []
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < timedelta(seconds=5)]
    if len(user_messages[uid]) > 5:
        if uid not in spam_warns or (now - spam_warns[uid] > timedelta(minutes=1)):
            spam_warns[uid] = now
            await message.channel.send(f"⚠️ {message.author.mention} بطل سبام!", delete_after=5)
        else:
            try: await message.author.timeout(timedelta(minutes=10), reason="سبام")
            except: pass
        return

    # الخط التلقائي ونقاط التفاعل
    if message.channel.id in auto_line_channels and message.content != LINE_URL:
        await asyncio.sleep(0.5); await message.channel.send(LINE_URL)

    u = get_user(uid)
    u["xp"] += random.randint(2, 5); u["msg_count"] += 1
    if random.random() < 0.2: u["points"] += 1
    
    if u["msg_count"] == 150:
        u["points"] += 50
        await message.channel.send(f"🎉 {message.author.mention} كملت 150 رسالة وأخدت 50 نقطة!")

    save_data()
    await bot.process_commands(message)

# --- 4. أوامر المستخدمين (المتجر، توب، يومي) ---
@bot.command()
async def رتبتي(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    emb = discord.Embed(title=f"📊 ملف {m.display_name}", color=0x3498db)
    emb.add_field(name="المستوى", value=f"`{u['level']}`").add_field(name="النقاط", value=f"`{u['points']}`").add_field(name="رسائل اليوم", value=f"`{u['msg_count']}/150`")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    last = u.get("daily_claimed")
    if last and now - datetime.fromisoformat(last) < timedelta(days=1):
        return await ctx.send("❌ ارجع بعد 24 ساعة!")
    gift = random.randint(20, 50)
    u["points"] += gift; u["daily_claimed"] = now.isoformat()
    save_data(); await ctx.send(f"🎁 أخدت {gift} نقطة هدية!")

@bot.command()
async def توب(ctx):
    lb = sorted(user_data.items(), key=lambda x: x[1].get('points', 0), reverse=True)[:5]
    emb = discord.Embed(title="💰 أغنى 5 جبابرة", color=0xffd700)
    for i, (uid, d) in enumerate(lb):
        user = bot.get_user(int(uid))
        name = user.display_name if user else uid
        emb.add_field(name=f"#{i+1} {name}", value=f"النقاط: `{d.get('points',0)}`", inline=False)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def متجر(ctx):
    emb = discord.Embed(title="🏪 المتجر", description="`.شراء [الاسم]`\nالألوان: احمر، ازرق، اسود، اخضر (300ن)\nرتبة: legendary (500ن)", color=0x2ecc71)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str):
    u = get_user(ctx.author.id)
    item = item.lower()
    if item in COLORS and u["points"] >= 300:
        r = ctx.guild.get_role(COLORS[item])
        if r: await ctx.author.add_roles(r); u["points"] -= 300; await ctx.send(f"🎨 تم شراء لون {item}")
    elif item == "legendary" and u["points"] >= 500:
        r = ctx.guild.get_role(LVL_30_ROLE_ID)
        if r: await ctx.author.add_roles(r); u["points"] -= 500; await ctx.send("🔱 مبروك رتبة Legendary!")
    save_data()

@bot.command()
async def تحويل(ctx, m: discord.Member, amt: int):
    u1, u2 = get_user(ctx.author.id), get_user(m.id)
    if amt <= 0 or u1["points"] < amt: return await ctx.send("❌ رصيدك لا يكفي")
    u1["points"] -= amt; u2["points"] += amt
    save_data(); await ctx.send(f"✅ تم تحويل {amt} لـ {m.mention}")

# --- 5. أوامر الإدارة والاقتراحات ---
@bot.tree.command(name="اقتراح")
async def suggest_slash(it: discord.Interaction):
    await it.response.send_modal(SuggestionModal())

@bot.command()
@commands.has_permissions(manage_messages=True)
async def مسح(ctx, num: int):
    await ctx.channel.purge(limit=num+1)
    await ctx.send(f"✅ تم مسح {num}", delete_after=3)

@bot.command()
@commands.has_permissions(kick_members=True)
async def كيك(ctx, m: discord.Member, *, r="لا يوجد"):
    await m.kick(reason=r); await ctx.send(f"👤 تم طرد {m}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def بان(ctx, m: discord.Member, *, r="لا يوجد"):
    await m.ban(reason=r); await ctx.send(f"🚫 تم حظر {m}")

@bot.tree.command(name="embed")
async def embed_maker(it: discord.Interaction, title: str, desc: str):
    if not it.user.guild_permissions.administrator: return
    emb = discord.Embed(title=title, description=desc.replace("\\n", "\n"), color=0x00ffcc)
    await it.response.send_message(embed=emb)

@bot.command()
@commands.has_permissions(administrator=True)
async def خط_تلقائي(ctx, state: str):
    global auto_line_channels
    if state == "تشغيل": auto_line_channels.append(ctx.channel.id)
    elif state == "ايقاف": 
        if ctx.channel.id in auto_line_channels: auto_line_channels.remove(ctx.channel.id)
    save_data(); await ctx.send(f"📢 نظام الخط: {state}", delete_after=5)

# --- 6. المهام التلقائية ---
@tasks.loop(minutes=10)
async def voice_points_tracker():
    for g in bot.guilds:
        for vc in g.voice_channels:
            for m in vc.members:
                if not m.bot and not (m.voice.self_mute):
                    u = get_user(m.id); u["points"] += 2
    save_data()

@tasks.loop(hours=24)
async def update_daily_active():
    if not user_data: return
    top = max(user_data.items(), key=lambda x: x[1].get('msg_count', 0))
    guild = bot.guilds[0]
    r = guild.get_role(DAILY_ACTIVE_ROLE_ID)
    if r:
        for m in r.members: await m.remove_roles(r)
        win = guild.get_member(int(top[0]))
        if win: await win.add_roles(r)
    for uid in user_data: user_data[uid]["msg_count"] = 0
    save_data()

bot.run(os.environ.get('DISCORD_TOKEN'))
