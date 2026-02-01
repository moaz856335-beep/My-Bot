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
SUGGESTIONS_CH_ID = 1467618877990244520 # روم الاقتراحات
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
user_messages = {} 
spam_warns = {}    

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
        user_data[uid] = {"points": 0, "xp": 0, "level": 1, "msg_count": 0, "daily_claimed": None}
    return user_data[uid]

async def send_log(title, description, color=0xff0000):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        emb = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now())
        await log_ch.send(embed=emb)

# --- 4. نظام الاقتراحات (Modal) ---
class SuggestionModal(ui.Modal, title='💡 تقديم اقتراح جديد'):
    s_title = ui.TextInput(label='موضوع الاقتراح', placeholder='اكتب عنوان قصير...')
    s_desc = ui.TextInput(label='تفاصيل الاقتراح', style=discord.TextStyle.paragraph, placeholder='اشرح اقتراحك بالتفصيل...')

    async def on_submit(self, it: discord.Interaction):
        ch = bot.get_channel(SUGGESTIONS_CH_ID)
        if ch:
            emb = discord.Embed(title=f"📌 {self.s_title.value}", description=self.s_desc.value, color=0x00ffcc)
            emb.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
            emb.set_footer(text=f"User ID: {it.user.id}")
            msg = await ch.send(embed=emb)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            await it.response.send_message("✅ تم إرسال اقتراحك للإدارة ولن يتم مسحه!", ephemeral=True)

# --- 5. الأحداث (Events) ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    if not update_daily_active.is_running(): update_daily_active.start()
    if not voice_points_tracker.is_running(): voice_points_tracker.start()
    print(f"✅ {bot.user} Online & Ready!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    u = get_user(message.author.id)
    uid, now = message.author.id, datetime.now()

    # نظام السبام
    if uid not in user_messages: user_messages[uid] = []
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < timedelta(seconds=5)]
    if len(user_messages[uid]) > 5:
        if uid not in spam_warns or (now - spam_warns[uid] > timedelta(minutes=1)):
            spam_warns[uid] = now
            await message.channel.send(f"⚠️ {message.author.mention} خفف سبام!", delete_after=5)
            await send_log("⚠️ تحذير سبام", f"العضو: {message.author.mention}\nالروم: {message.channel.mention}", 0xffaa00)
        else:
            try:
                await message.author.timeout(timedelta(minutes=10), reason="سبام متكرر")
                await message.channel.send(f"🚫 تم إسكات {message.author.mention} 10 دقائق.")
                await send_log("🚫 تايم أوت (سبام)", f"العضو: {message.author.mention}\nالمدة: 10 دقائق", 0xff0000)
            except: pass
        return

    # XP والنقاط
    u["xp"] += random.randint(2, 5)
    if random.random() < 0.3: u["points"] += 1 
    u["msg_count"] += 1
    
    # ليفل أب
    if u["xp"] >= u["level"] * 200:
        u["level"] += 1
        lvl_ch = bot.get_channel(LEVEL_CH_ID)
        if lvl_ch: await lvl_ch.send(f"🆙 مبروك {message.author.mention} مستوى **{u['level']}**!")

    save_data()
    await bot.process_commands(message)

# --- 6. الأوامر الإدارية ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def مسح(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم مسح {amount} رسالة", delete_after=3)
    await send_log("🧹 عملية مسح", f"المشرف: {ctx.author.mention}\nالعدد: {amount}\nالروم: {ctx.channel.mention}", 0x3498db)

@bot.command()
@commands.has_permissions(kick_members=True)
async def كيك(ctx, member: discord.Member, *, reason="بدون سبب"):
    await member.kick(reason=reason)
    await ctx.send(f"👤 تم طرد {member.display_name}")
    await send_log("👤 طرد (Kick)", f"العضو: {member.mention}\nبواسطة: {ctx.author.mention}\nالسبب: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def بان(ctx, member: discord.Member, *, reason="بدون سبب"):
    await member.ban(reason=reason)
    await ctx.send(f"🚫 تم حظر {member.display_name}")
    await send_log("🚫 حظر (Ban)", f"العضو: {member.mention}\nبواسطة: {ctx.author.mention}\nالسبب: {reason}")

# --- 7. أوامر المستخدمين ---
@bot.command()
async def اقتراح(ctx):
    await ctx.send("يرجى استخدام أمر السلاش `/اقتراح` لتقديم اقتراحك بنظام النافذة!")

@bot.tree.command(name="اقتراح", description="فتح نافذة تقديم اقتراح جديد")
async def suggestion_slash(interaction: discord.Interaction):
    await interaction.response.send_modal(SuggestionModal())

@bot.command()
async def تحويل(ctx, member: discord.Member, amount: int):
    u1, u2 = get_user(ctx.author.id), get_user(member.id)
    if amount <= 0 or u1["points"] < amount: return await ctx.send("❌ رصيد غير كافٍ!")
    u1["points"] -= amount; u2["points"] += amount
    save_data(); await ctx.send(f"✅ تم تحويل {amount} نقطة إلى {member.mention}")

@bot.command()
async def رتبتي(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    emb = discord.Embed(title=f"📊 ملف {m.display_name}", color=0x3498db)
    emb.add_field(name="المستوى", value=f"`{u['level']}`").add_field(name="النقاط", value=f"`{u['points']}`")
    emb.set_thumbnail(url=m.display_avatar.url)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    if u.get("daily_claimed") and now - datetime.fromisoformat(u["daily_claimed"]) < timedelta(days=1):
        return await ctx.send("❌ ارجع بكرة!")
    gift = random.randint(10, 30)
    u["points"] += gift; u["daily_claimed"] = now.isoformat()
    save_data(); await ctx.send(f"🎁 مبروك {gift} نقطة!")

@bot.command()
async def متجر(ctx):
    emb = discord.Embed(title="🏪 متجر الإمبراطورية", description="`.شراء [الاسم]`", color=0x2ecc71)
    emb.add_field(name="🎨 الألوان (300)", value="احمر، ازرق، اسود، بني، اصفر، اخضر...").add_field(name="🔱 رتب", value="Legendary (500)")
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str):
    u = get_user(ctx.author.id)
    item = item.lower()
    if item in COLORS and u["points"] >= 300:
        await ctx.author.add_roles(ctx.guild.get_role(COLORS[item]))
        u["points"] -= 300; await ctx.send("🎨 تم شراء اللون!")
    elif item == "legendary" and u["points"] >= 500:
        await ctx.author.add_roles(ctx.guild.get_role(LEGENDARY_ROLE))
        u["points"] -= 500; await ctx.send("🔱 مبروك رتبة Legendary!")
    save_data()

@bot.tree.command(name="embed", description="صنع إيمبد احترافي")
async def embed_slash(it: discord.Interaction, title: str, desc: str):
    if not it.user.guild_permissions.administrator: return await it.response.send_message("❌ للإدارة فقط")
    emb = discord.Embed(title=title, description=desc.replace("\\n", "\n"), color=0x00ffcc)
    await it.response.send_message(embed=emb)

# --- 8. المهام التلقائية ---
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
    for uid in user_data: user_data[uid]["msg_count"] = 0
    save_data()

bot.run(os.environ.get('DISCORD_TOKEN'))
