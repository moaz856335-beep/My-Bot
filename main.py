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

user_data, active_color_subs = {}, {}
load_data()

# --- 3. الثوابت ---
LINE_URL = "https://media.discordapp.net/attachments/1465707929377443992/1465748212051611889/1769531918511.png"
LOG_CH_ID = 1466903846612635882
SUGGEST_CH_ID = 1466905596732113224
EVENT_CH_ID = 1454787783070716025
MENTION_CHANNELS = [1454565709400248538, 1454787783070716025]
AUTO_ROLE_ID = 1460326577727471742
TOP_ROLE_ID = 1466903177801760873
SPECIAL_ROLE_ID = 1466159241537655049
GAME_ROLE_ID = 1466159040609521969

COLORS = {
    "احمر": 1466906222832652564, "ازرق": 1466906478534201354, 
    "اسود": 1466906615990063111, "بني": 1466906757358944297,
    "اصفر": 1466906955615568005, "اورنج": 1466907014700466280,
    "اخضر": 1466907188701433939, "بنفسجي": 1466907386974572706
}

@bot.event
async def on_ready():
    await bot.tree.sync() # <--- ضيف السطر ده هنا بالظبط
    print(f'👑 Kraken Empire is Online')
    check_color_expiry.start()
    auto_event_spawner.start()
    update_top_role.start()
    
def get_user(u_id):
    uid = str(u_id)
    if uid not in user_data:
        user_data[uid] = {"points": 0, "warnings": 0}
    return user_data[uid]

# --- 4. اللوج والمنشن ---
@bot.event
async def on_member_join(member):
    r = member.guild.get_role(AUTO_ROLE_ID)
    if r: await member.add_roles(r)
    for cid in MENTION_CHANNELS:
        ch = member.guild.get_channel(cid)
        if ch:
            m = await ch.send(member.mention); await asyncio.sleep(1); await m.delete()
    l_ch = bot.get_channel(LOG_CH_ID)
    if l_ch:
        emb = discord.Embed(title="📥 عضو جديد", description=f"{member.mention} انضم إلينا", color=0x2ecc71)
        emb.set_thumbnail(url=member.display_avatar.url)
        await l_ch.send(embed=emb)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    l_ch = bot.get_channel(LOG_CH_ID)
    if l_ch:
        emb = discord.Embed(title="🗑️ رسالة محذوفة", color=0xe74c3c)
        emb.add_field(name="المرسل:", value=message.author.mention)
        emb.add_field(name="المحتوى:", value=message.content or "لا يوجد نص")
        await l_ch.send(embed=emb)

# --- 5. أوامر الإدارة الفخمة ---
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
    u["warnings"] += 1; save_data()
    emb = discord.Embed(title="⚠️ تحذير", description=f"تم تحذير {member.mention}\nإجمالي تحذيراته: `{u['warnings']}`", color=0xf1c40f)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

# --- 6. المتجر والإنفايت والاقتراح ---
@bot.command()
async def شراء(ctx, item: str, duration: str = "1"):
    u = get_user(ctx.author.id); emb = discord.Embed(color=0x3498db)
    if item == "رتبة":
        if u["points"] < 30: emb.description = "❌ نقاطك لا تكفي (30 مطلوب)"; return await ctx.send(embed=emb)
        await ctx.author.add_roles(ctx.guild.get_role(SPECIAL_ROLE_ID)); u["points"] -= 30
        emb.description = "✅ مبروك الرتبة الخاصة!"
    elif item in COLORS:
        try:
            days = 30 if duration == "شهر" else 365 if duration == "سنة" else int(duration)
            cost = 30 if duration == "شهر" else 300 if duration == "سنة" else days
            if u["points"] < cost: emb.description = f"❌ نقاطك لا تكفي (التكلفة: {cost})"; return await ctx.send(embed=emb)
            await ctx.author.add_roles(ctx.guild.get_role(COLORS[item]))
            active_color_subs[str(ctx.author.id)] = {"role_id": COLORS[item], "expiry": (datetime.now() + timedelta(days=days)).isoformat()}
            u["points"] -= cost; emb.description = f"🎨 تم تفعيل لون {item} لـ {duration}!"
        except: emb.description = "❌ خطأ في المدة"
    await ctx.send(embed=emb); await ctx.send(LINE_URL); save_data()

@bot.command()
async def انفايت(ctx, m: discord.Member = None):
    m = m or ctx.author; invs = await ctx.guild.invites()
    count = sum(i.uses for i in invs if i.inviter == m)
    emb = discord.Embed(title="📊 الدعوات", description=f"العضو: {m.mention}\nالدعوات: `{count}`", color=0x9b59b6)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def اقتراح(ctx, *, text):
    if ctx.channel.id != SUGGEST_CH_ID: return
    await ctx.message.delete()
    emb = discord.Embed(title="💡 اقتراح جديد", description=text, color=0xffff00)
    emb.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=emb)
    for r in ["✅", "❌"]: await msg.add_reaction(r)
    await ctx.send(LINE_URL)

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id); u["points"] += 3; save_data()
    emb = discord.Embed(description=f"💰 {ctx.author.mention} حصلت على 3 نقاط!", color=0x2ecc71)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

# --- 7. المهام التلقائية (كل ساعة) ---
@tasks.loop(hours=1) # الفعاليات كل ساعة
async def auto_event_spawner():
    ch = bot.get_channel(EVENT_CH_ID)
    if not ch: return
    q, a = random.choice([("فكك (كراكن)", "ك ر ا ك ن"), ("جمع (س ي ر ف ر)", "سيرفر")])
    emb = discord.Embed(title="🎮 فعالية الساعة", description=f"أسرع شخص يكتب: **{q}**", color=0xe67e22)
    m = await ch.send(embed=emb)
    try:
        w = await bot.wait_for('message', check=lambda x: x.channel == ch and x.content == a, timeout=60)
        u = get_user(w.author.id); u["points"] += 5; save_data()
        await ch.send(f"🎉 كفو {w.author.mention}! (+5 نقاط)"); await ch.send(LINE_URL)
    except: await m.delete()

@tasks.loop(minutes=5)
async def update_top_role():
    if not user_data: return
    top_id = max(user_data, key=lambda x: user_data[x]['points'])
    for g in bot.guilds:
        r = g.get_role(TOP_ROLE_ID)
        if r:
            for m in r.members:
                if str(m.id) != top_id: await m.remove_roles(r)
            tm = g.get_member(int(top_id))
            if tm and r not in tm.roles: await tm.add_roles(r)

@tasks.loop(minutes=10)
async def check_color_expiry():
    now = datetime.now()
    for uid, d in list(active_color_subs.items()):
        if now > datetime.fromisoformat(d["expiry"]):
            for g in bot.guilds:
                m = g.get_member(int(uid))
                if m: await m.remove_roles(g.get_role(d["role_id"]))
            del active_color_subs[uid]; save_data()

# 1. تعريف النافذة اللي بتفتح لك لما تكتب الأمر
class EmbedModal(discord.ui.Modal, title='إنشاء إيمبد الإمبراطورية'):
    # خانة العنوان
    عنوان = discord.ui.TextInput(label='عنوان الإيمبد', placeholder='اكتب العنوان هنا...', required=True)
    # خانة المحتوى (paragraph عشان تسمح بالنزول لتحت Enter)
    المحتوى = discord.ui.TextInput(
        label='محتوى الرسالة', 
        style=discord.TextStyle.paragraph, 
        placeholder='اكتب رسالتك هنا.. تقدر تنزل سطور براحتك بالـ Enter', 
        required=True, 
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # بناء شكل الإيمبد
        emb = discord.Embed(title=self.عنوان.value, description=self.المحتوى.value, color=0x2b2d31)
        
        # الرد اللي بيظهر لك أنت بس إن العملية تمت
        await interaction.response.send_message("✅ تم نشر الإيمبد بنجاح!", ephemeral=True)
        
        # إرسال الإيمبد في الروم وتحته الخط الملكي
        await interaction.channel.send(embed=emb)
        await interaction.channel.send(LINE_URL)

# 2. تسجيل الأمر في قائمة الـ Slash Commands باسم /embed
@bot.tree.command(name="embed", description="فتح نافذة كتابة إيمبد احترافية")
@commands.has_permissions(administrator=True)
async def embed_slash(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedModal())
    
bot.run(os.environ.get('DISCORD_TOKEN'))


