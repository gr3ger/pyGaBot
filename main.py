from os.path import exists

from discord.ext import commands
import configparser

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['DEFAULT']['Token']
CALL_CHARACTER = config['DEFAULT']['CallCharacter']
bot = commands.Bot(command_prefix=CALL_CHARACTER)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello {}!".format(ctx.message.author.name))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


bot.run(TOKEN)
