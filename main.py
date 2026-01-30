import discord
import os
import random
from discord import app_commands
from discord.ext import commands

# 1. إعدادات الصلاحيات (ضرورية جداً لنظام الانفايت)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.invites = True 

class KrakenBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".", intents=intents)
        self.warns_data = {}
        self.invites_tracker = {} # مخزن بيانات الانفايت

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ تم تفعيل: الألعاب، التحذيرات، والـ Invite Tracker")

    # تحديث كاش الانفايت عند تشغيل البوت
    async def on_ready(self):
        for guild in self.guilds:
            try:
                self.invites_tracker[guild.id] = await guild.invites()
            except:
                pass

bot = KrakenBot()

# --- 2. نظام حساب الانفايت (Invite Tracker) ---

@bot.command(name="inv")
async def check_invites(ctx, member: discord.Member = None):
    member = member or ctx.author
    invites = await ctx.guild.invites()
    
    total_invites = 0
    for invite in invites:
        if invite.inviter == member:
            total_invites += invite.uses
    
    # ملاحظة: ديسكورد لا يعطي بيانات "من خرج" مباشرة بدقة 100% إلا بقاعدة بيانات
    # لكن سنظهر الإجمالي المتاح حالياً
    embed = discord.Embed(
        title=f"📊 سجل دعوات | {member.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="✅ إجمالي الدعوات", value=f"**{total_invites}** شخص", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"طلب بواسطة {ctx.author.name}")
    
    await ctx.send(embed=embed)

# --- 3. نظام الألعاب (.سؤال) ---
questions_list = [
    {"q": "ما هو أطول نهر في العالم؟", "a": "النيل"},
    {"q": "ما هي عاصمة مصر؟", "a": "القاهرة"},
    {"q": "ما هو الكوكب الأحمر؟", "a": "المريخ"},
    {"q": "أضخم حيوان في العالم؟", "a": "الحوت الازرق"}
]

@bot.command(name="سؤال")
async def ask_question(ctx):
    item = random.choice(questions_list)
    await ctx.send(f"**{item['q']}** 🤔 (لديك 15 ثانية)")

    def check(m):
        return m.content == item['a'] and m.channel == ctx.channel
    try:
        msg = await bot.wait_for('message', check=check, timeout=15.0)
        await ctx.send(f"🎉 كفو {msg.author.mention}! صح: **{item['a']}**")
    except:
        await ctx.send(f"⏳ انتهى الوقت! الإجابة: **{item['a']}**")

# --- 4. نظام الإدارة والتحذيرات (Slash Commands) ---

@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "غير محدد"):
    uid = str(user.id)
    if uid not in bot.warns_data: bot.warns_data[uid] = []
    bot.warns_data[uid].append(reason)
    
    embed = discord.Embed(title="⚠️ تحذير", color=discord.Color.red())
    embed.add_field(name="العضو", value=user.mention)
    embed.add_field(name="السبب", value=reason)
    embed.add_field(name="العدد الإجمالي", value=len(bot.warns_data[uid]))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="مسح الرسائل")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ تم مسح {amount} رسالة.")

# --- 5. نظام الـ Embed (Modal) ---
class EmbedCreator(discord.ui.Modal, title="إنشاء إيمبد"):
    t = discord.ui.TextInput(label="العنوان", required=False)
    d = discord.ui.TextInput(label="المحتوى", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title=self.t.value, description=self.d.value, color=discord.Color.green()))

@bot.tree.command(name="embed")
async def embed_modal(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedCreator())

bot.run(os.environ.get('DISCORD_TOKEN'))
