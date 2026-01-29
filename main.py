import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت شغال دلوقتي باسم: {bot.user}") #

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # الرد على كلمة اهلا بدون !
    if message.content == "اهلا":
        await message.channel.send("أهلاً بك!  إمبراطورية كراكن ترحب بك، كيف أخدمك؟ 🔱") #

    await bot.process_commands(message)

# التوكن بتاعك
bot.run('MTQ2NjQ5NTc0NTI4ODA0NDY3Nw.GxbVrW.IwyqK5GtFOlYzkxXmsFwHTa-nnC5F4f5tjU2rg') #