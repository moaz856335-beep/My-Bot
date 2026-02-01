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

# --- 2. الثوابت والـ IDs (تأكد من صحتها) ---
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

# --- 4. معالجة الأخطاء الذكية (Error Handling) ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        if ctx.command.name == "تحويل":
            await ctx.send("⚠️ الطريقة الصح: `.تحويل @العضو المبلغ`")
        elif ctx.command.name == "شراء":
            await ctx.send("⚠️ اكتب اسم الحاجة! مثال: `.شراء احمر`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ مش لاقي العضو ده، تأكد إنك منشنته صح.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ فيه غلط في البيانات (تأكد إن المبلغ رقم صحيح).")
    elif isinstance(error, commands.CommandNotFound):
        pass # لا يرد على الأوامر غير الموجودة لتجنب الإزعاج

# --- 5. الأحداث الأساسية (On Message) ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    update_daily_active.start()
    voice_points_tracker.start()
    print(f"✅ {bot.user} is Ready!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    u = get_user(message.author.id)
    uid = message.author.id
    now = datetime.now()

    # --- نظام السبام المتدرج ---
    if uid not in user_messages: user_messages[uid] = []
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < timedelta(seconds=5)]

    if len(user_messages[uid]) > 5:
        if uid not in spam_warns or (now - spam_warns[uid] > timedelta(minutes=1)):
            spam_warns[uid] = now
            await message.channel.send(f"⚠️ {message.author.mention} خفف سبام عشان ما تاخد تايم أوت!", delete_after=5)
        else:
            try:
                await message.author.timeout(timedelta(minutes=10), reason="سبام متكرر")
                await message.channel.send(f"🚫 تم إسكات {message.author.mention} 10 دقائق بسبب السبام.")
            except: pass
            return

    # --- حساب النقاط والـ XP ---
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

# --- 6. أوامر الأعضاء والتحويل الذكي ---
@bot.command()
async def تحويل(ctx, member: discord.Member = None, amount: int = None):
    if member is None or amount is None:
        return await ctx.send("⚠️ الطريقة: `.تحويل @العضو المبلغ`")
    if member.bot:
        return await ctx.send("🤖 البوتات ملهاش رصيد يا ملك، إحنا شغالين بالكهرباء!")
    if member == ctx.author:
        return await ctx.send("🤡 بتحول لنفسك؟ بطل استهبال يا بطل!")
    
    u1, u2 = get_user(ctx.author.id), get_user(member.id)
    if amount <= 0: return await ctx.send("🚫 المبلغ لازم يكون أكبر من صفر.")
    if u1["points"] < amount:
        return await ctx.send(f"❌ رصيدك `{u1['points']}` بس، ناقصك `{amount - u1['points']}`.")
    
    u1["points"] -= amount
    u2["points"] += amount
    save_data()
    await ctx.send(f"✅ تم تحويل `{amount}` نقطة إلى {member.mention}")

@bot.command()
async def رتبتي(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    emb = discord.Embed(title=f"📊 ملف {m.display_name}", color=0x3498db)
    emb.add_field(name="المستوى 🆙", value=f"`{u['level']}`", inline=True)
    emb.add_field(name="النقاط 💰", value=f"`{u['points']}`", inline=True)
    emb.set_thumbnail(url=m.display_avatar.url)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def يومي(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    last = u.get("daily_claimed")
    if last and now - datetime.fromisoformat(last) < timedelta(days=1):
        return await ctx.send("❌ أخذت هديتك، ارجع بكرة!")
    gift = random.randint(10, 30)
    u["points"] += gift
    u["daily_claimed"] = now.isoformat()
    save_data()
    await ctx.send(f"🎁 مبروك! حصلت على **{gift}** نقطة.")

# --- 7. المتجر والشراء ---
@bot.command()
async def متجر(ctx):
    emb = discord.Embed(title="🏪 متجر الإمبراطورية", description="استخدم `.شراء [الاسم]`", color=0x2ecc71)
    emb.add_field(name="🎨 الألوان (300 نقطة)", value="احمر، ازرق، اسود، بني، اصفر، اورنج، اخضر، بنفسجي", inline=False)
    emb.add_field(name="🔱 رتب ملكية", value="**Legendary** (500)\n**Elite** (1000)", inline=False)
    await ctx.send(embed=emb); await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str):
    u = get_user(ctx.author.id)
    item = item.lower()
    if item in COLORS:
        if u["points"] < 300: return await ctx.send("❌ نقاطك لا تكفي (300)")
        await ctx.author.add_roles(ctx.guild.get_role(COLORS[item]))
        u["points"] -= 300; await ctx.send(f"🎨 تم تفعيل لون **{item}**")
    elif item == "legendary":
        if u["points"] < 500: return await ctx.send("❌ رصيدك ناقص (500 مطلوب)")
        await ctx.author.add_roles(ctx.guild.get_role(LEGENDARY_ROLE))
        u["points"] -= 500; await ctx.send("🔱 مبروك رتبة Legendary!")
    save_data()

# --- 8. صانع الإيمبد ومهام الفويس ---
@bot.tree.command(name="embed", description="تصميم إيمبد احترافي")
async def embed_maker(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ للإدارة فقط", ephemeral=True)
    
    class MyModal(ui.Modal, title='🎨 صانع الإيمبدات الملكي'):
        t = ui.TextInput(label='العنوان', placeholder='عنوان المنشور...')
        d = ui.TextInput(label='الوصف', style=discord.TextStyle.paragraph, placeholder='اكتب المحتوى هنا...')
        i = ui.TextInput(label='رابط الصورة (اختياري)', required=False)
        async def on_submit(self, it: discord.Interaction):
            emb = discord.Embed(title=self.t.value, description=self.d.value, color=0x00ffcc)
            if self.i.value: emb.set_image(url=self.i.value)
            await it.response.send_message(embed=emb)
            await it.followup.send(LINE_URL)
    await interaction.response.send_modal(MyModal())

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
    # هنا يتم تصفير الرسائل لاختيار ملك التفاعل الجديد
    for uid in user_data: user_data[uid]["msg_count"] = 0
    save_data()

@bot.command()
async def توب(ctx):
    if not user_data:
        return await ctx.send("❌ مفيش بيانات لسه، ابدأوا تفاعل!")

    # ترتيب المستخدمين بناءً على النقاط (من الأعلى للأقل)
    # بناخد أول 5 أعضاء بس عشان الإيمبد ميبقاش طويل
    leaderboard = sorted(user_data.items(), key=lambda x: x[1].get('points', 0), reverse=True)[:5]
    
    emb = discord.Embed(
        title="💰 قائمة أغنى 5 جبابرة في الكراكن",
        description="هؤلاء هم ملوك الثروة في الإمبراطورية حالياً:",
        color=0xffd700 # لون ذهبي
    )
    
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    
    for index, (uid, data) in enumerate(leaderboard):
        user = bot.get_user(int(uid))
        name = user.display_name if user else f"عضو غادر ({uid})"
        points = data.get('points', 0)
        level = data.get('level', 1)
        
        emb.add_field(
            name=f"{medals[index]} المركز {index+1}",
            value=f"**الاسم:** {name}\n**النقاط:** `{points}` | **الليفل:** `{level}`",
            inline=False
        )
    
    emb.set_footer(text="استمر في التفاعل لتدخل القائمة!", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    await ctx.send(embed=emb)
    await ctx.send(LINE_URL)
    # --- نظام الخط التلقائي (Auto Line) ---

# مخزن للرومات المفعول فيها الخط (يفضل حفظها في الـ JSON لو عايزها دايمة)
auto_line_channels = [] 

@bot.command()
@commands.has_permissions(administrator=True)
async def خط_تلقائي(ctx, state: str = None):
    """تشغيل أو إطفاء الخط التلقائي في الروم الحالي"""
    global auto_line_channels
    
    if state == "تشغيل":
        if ctx.channel.id not in auto_line_channels:
            auto_line_channels.append(ctx.channel.id)
            await ctx.send(f"✅ تم تفعيل الخط التلقائي في روم: {ctx.channel.mention}")
        else:
            await ctx.send("⚠️ الخط التلقائي مفعل بالفعل هنا.")
            
    elif state == "ايقاف":
        if ctx.channel.id in auto_line_channels:
            auto_line_channels.remove(ctx.channel.id)
            await ctx.send(f"❌ تم إيقاف الخط التلقائي في روم: {ctx.channel.mention}")
        else:
            await ctx.send("⚠️ الخط التلقائي غير مفعل هنا.")
    else:
        await ctx.send("❓ الطريقة: `.خط_تلقائي تشغيل` أو `.خط_تلقائي ايقاف`")

# --- تعديل حدث on_message عشان يبعت الخط ---
# (تأكد إنك بتضيف السطور دي جوه الـ on_message الموجود عندك أصلاً)

@bot.event
async def on_message(message):
    if message.author.bot and message.author != bot.user: return # تجاهل البوتات التانية
    
    # 1. إذا كان الروم مفعل فيه الخط التلقائي
    if message.channel.id in auto_line_channels:
        # لو الرسالة هي الخط نفسه، نتجاهلها عشان ما يحصلش Loop (تكرار نهائي)
        if message.content != LINE_URL:
            # ننتظر ثانية بسيطة عشان الرسالة تنزل الأول
            await asyncio.sleep(0.5)
            await message.channel.send(LINE_URL)

    # ... كمل باقي كود النقاط والسبام والـ process_commands ...
    await bot.process_commands(message)
    

# --- التشغيل ---
token = os.environ.get('DISCORD_TOKEN')
bot.run(token)



