import discord
from discord.ext import commands, tasks
import asyncio
import random
import os
from datetime import datetime, timedelta

# --- 1. الإعدادات والـ Intents ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

# تخزين البيانات
user_data = {} 
server_configs = {} 
active_color_subs = {} 
spam_control = {}

# الثوابت (الأيديات والروابط)
LINE_URL = "https://media.discordapp.net/attachments/1465707929377443992/1465748212051611889/1769531918511.png?ex=697e3066&is=697cdee6&hm=95a652e620de5863021e4a6c93034d8d1e6fabe64164621569f4ffbc456188e3&=&format=webp&quality=lossless&width=1632&height=241"
LOG_CH = 1466903846612635882
SUGGEST_CH = 1466905596732113224
SHOP_CH = 1466905919865753682
EVENT_CH = 1454787783070716025
MENTION_CHANNELS = [1454565709400248538, 1454787783070716025]
AUTO_ROLE = 1460326577727471742
TOP_ROLE = 1466903177801760873
SPECIAL_ROLE = 1466159241537655049
GAME_ROLE_ID = 1466159040609521969
WIN_THRESHOLD = 25

COLORS = {
    "احمر": 1466906222832652564, "ازرق": 1466906478534201354, 
    "اسود": 1466906615990063111, "بني": 1466906757358944297,
    "اصفر": 1466906955615568005, "اورنج": 1466907014700466280,
    "اخضر": 1466907188701433939, "بنفسجي": 1466907386974572706
}

BAD_WORDS = ["كلمة1", "كلمة2"] # أضف كلماتك هنا

@bot.event
async def on_ready():
    print(f'👑 Kraken System Active: {bot.user.name}')
    check_color_expiry.start()
    auto_event_spawner.start()
    update_top_role.start()

# دالة مساعدة للحصول على بيانات المستخدم
def get_user(u_id):
    if u_id not in user_data:
        user_data[u_id] = {"points": 0, "last_daily": None, "warnings": 0}
    return user_data[u_id]

# --- 2. نظام الدخول والحماية والمنشن ---
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(AUTO_ROLE)
    if role: await member.add_roles(role)
    for ch_id in MENTION_CHANNELS:
        channel = member.guild.get_channel(ch_id)
        if channel:
            tmp = await channel.send(member.mention)
            await asyncio.sleep(1)
            await tmp.delete()

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # حماية السبام (10 رسائل = تايم ساعة)
    u_id = message.author.id
    if u_id not in spam_control: spam_control[u_id] = []
    spam_control[u_id].append(message.content)
    if len(spam_control[u_id]) >= 10:
        if len(set(spam_control[u_id][-10:])) == 1:
            await message.author.timeout(discord.utils.utcnow() + timedelta(hours=1))
            await message.channel.send(f"⏳ {message.author.mention} تم إعطاؤك تايم ساعة بسبب السبام.")
            spam_control[u_id] = []

    # الخط التلقائي
    if message.guild.id in server_configs:
        cfg = server_configs[message.guild.id]
        if message.channel.id == cfg["channel_id"]:
            await message.channel.send(LINE_URL)

    await bot.process_commands(message)

# --- 3. أوامر المتجر والإنفايت (بنظام الإيمبد) ---
@bot.command(name="تحديث_المتجر")
@commands.has_permissions(administrator=True)
async def update_shop(ctx):
    await ctx.message.delete()
    await ctx.channel.purge(limit=5)
    embed = discord.Embed(title="🛒 متجر إمبراطورية كراكن", color=0x2b2d31)
    embed.add_field(name="🎨 الألوان", value="• يوم: `2 نقطة`\n• شهر: `40 نقطة`", inline=False)
    embed.add_field(name="📜 الرتب", value="• رتبة خاصة: `30 نقطة`", inline=False)
    embed.set_footer(text="للشراء: .شراء [اللون] [يوم/شهر]")
    await ctx.send(embed=embed)
    await ctx.send(LINE_URL)

@bot.command()
async def انفايت(ctx, member: discord.Member = None):
    member = member or ctx.author
    invites = await ctx.guild.invites()
    count = sum(i.uses for i in invites if i.inviter == member)
    embed = discord.Embed(title="📊 إحصائيات الدعوات", description=f"العضو: {member.mention}\nعدد الدعوات: `{count}`", color=0x2b2d31)
    await ctx.send(embed=embed)
    await ctx.send(LINE_URL)

@bot.command()
async def شراء(ctx, item: str, period: str = "يوم"):
    u = get_user(ctx.author.id)
    if item == "رتبة":
        if u["points"] < 30: return await ctx.send("❌ رصيدك لا يكفي")
        await ctx.author.add_roles(ctx.guild.get_role(SPECIAL_ROLE))
        u["points"] -= 30
        await ctx.send(f"✅ مبروك {ctx.author.mention} اشتريت الرتبة!\n{LINE_URL}")
    elif item in COLORS:
        cost = 2 if period == "يوم" else 40
        if u["points"] < cost: return await ctx.send("❌ رصيدك لا يكفي")
        role = ctx.guild.get_role(COLORS[item])
        await ctx.author.add_roles(role)
        active_color_subs[ctx.author.id] = {"role_id": COLORS[item], "expiry": datetime.now() + (timedelta(days=1) if period == "يوم" else timedelta(days=30))}
        u["points"] -= cost
        await ctx.send(f"🎨 {ctx.author.mention} تم تفعيل لون {item} لـ {period}!\n{LINE_URL}")

# --- 4. أوامر الإدارة والألعاب والفعاليات ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def تحذير(ctx, member: discord.Member):
    u = get_user(member.id)
    u["warnings"] += 1
    embed = discord.Embed(description=f"⚠️ {member.mention} تم تحذيرك! تحذيراتك: `{u['warnings']}`", color=0xff0000)
    await ctx.send(embed=embed)
    await ctx.send(LINE_URL)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def الخط(ctx):
    server_configs[ctx.guild.id] = {"channel_id": ctx.channel.id}
    await ctx.send("✅ تم تفعيل الخط التلقائي في هذه الروم.")

@tasks.loop(minutes=25)
async def auto_event_spawner():
    ch = bot.get_channel(EVENT_CH)
    q, a = random.choice([("فكك (كراكن)", "ك ر ا ك ن"), ("جمع (س ي ر ف ر)", "سيرفر")])
    msg = await ch.send(f"🎊 **فعالية!** أسرع إجابة لـ: `{q}`")
    try:
        w = await bot.wait_for('message', check=lambda m: m.channel == ch and m.content == a, timeout=60.0)
        u = get_user(w.author.id)
        u["points"] += 5
        await ch.send(f"🎉 كفو {w.author.mention} (+5 نقاط)\n{LINE_URL}")
        if u["points"] >= WIN_THRESHOLD:
            r = w.guild.get_role(GAME_ROLE_ID)
            if r: await w.author.add_roles(r)
    except: await msg.delete()

@tasks.loop(minutes=5)
async def update_top_role():
    if not user_data: return
    top_u = max(user_data, key=lambda x: user_data[x]['points'])
    for g in bot.guilds:
        r = g.get_role(TOP_ROLE)
        if r:
            for m in r.members:
                if m.id != top_u: await m.remove_roles(r)
            tm = g.get_member(top_u)
            if tm and r not in tm.roles: await tm.add_roles(r)

@tasks.loop(minutes=10)
async def check_color_expiry():
    now = datetime.now()
    for u_id, d in list(active_color_subs.items()):
        if now > d["expiry"]:
            for g in bot.guilds:
                m = g.get_member(u_id)
                if m: await m.remove_roles(g.get_role(d["role_id"]))
            del active_color_subs[u_id]
            # --- تحديث إيمبد المتجر ---
@bot.command(name="تحديث_المتجر")
@commands.has_permissions(administrator=True)
async def update_shop(ctx):
    await ctx.message.delete()
    await ctx.channel.purge(limit=5)
    embed = discord.Embed(title="🛒 متجر إمبراطورية كراكن", color=0x2b2d31)
    embed.add_field(name="🎨 ألوان الشات", value="• سعر اليوم الواحد: `1 نقطة`\n• اشتراك شهري (30 يوم): `40 نقطة`", inline=False)
    embed.add_field(name="📜 الرتب الخاصة", value="• رتبة مميزة: `30 نقطة`", inline=False)
    embed.add_field(name="🛠️ طريقة الشراء", value="`.شراء [اللون] [عدد الأيام]`\nمثال: `.شراء احمر 5` (لشراء 5 أيام بـ 5 نقاط)", inline=False)
    embed.set_footer(text="نظام إمبراطورية كراكن التلقائي")
    await ctx.send(embed=embed)
    await ctx.send(LINE_URL)

# --- تحديث أمر الشراء الذكي ---
@bot.command()
async def شراء(ctx, item: str, days: str = "1"):
    u = get_user(ctx.author.id)
    
    # 1. شراء الرتبة الخاصة
    if item == "رتبة":
        if u["points"] < 30: return await ctx.send("❌ رصيدك لا يكفي (مطلوب 30 نقطة)")
        await ctx.author.add_roles(ctx.guild.get_role(SPECIAL_ROLE))
        u["points"] -= 30
        await ctx.send(f"✅ مبروك {ctx.author.mention} اشتريت الرتبة الخاصة!\n{LINE_URL}")

    # 2. شراء الألوان بعدد الأيام
    elif item in COLORS:
        try:
            # التحقق إذا كان المستخدم كتب "شهر" أو رقم
            if days == "شهر":
                num_days = 30
                cost = 40 # سعر خاص للشهر
            else:
                num_days = int(days)
                cost = num_days * 1 # اليوم بـ 1 نقطة
            
            if u["points"] < cost:
                return await ctx.send(f"❌ رصيدك لا يكفي، تكلفة {num_days} يوم هي {cost} نقطة.")
            
            role = ctx.guild.get_role(COLORS[item])
            await ctx.author.add_roles(role)
            
            # حساب وقت الانتهاء
            expiry = datetime.now() + timedelta(days=num_days)
            active_color_subs[ctx.author.id] = {"role_id": COLORS[item], "expiry": expiry}
            
            u["points"] -= cost
            await ctx.send(f"🎨 {ctx.author.mention} تم تفعيل لون **{item}** لمدة **{num_days}** يوم!\n{LINE_URL}")
            
        except ValueError:
            await ctx.send("❌ يرجى كتابة عدد الأيام بشكل صحيح (مثال: .شراء احمر 7)")

bot.run(os.environ.get('DISCORD_TOKEN'))



