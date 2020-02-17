from os.path import exists

import discord
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


def write_option(key, value):
    config['OPTIONS'][key] = value
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello {}!".format(ctx.message.author.name))

@bot.command()
@commands.has_any_role("Mods", "Admin")
async def enabletwitchannouncement(ctx, arg):
    print(ctx.message.channel.__repr__)
    if isinstance(ctx.message.channel, discord.TextChannel):
        write_option("AnnouncementChannel", ctx.message.channel.id.__str__())
        write_option("TwitchChannel", arg)
        await ctx.send("Successfully set the announcement channel to: {}, I will post here when user {} comes online.".format(ctx.message.channel.name, arg))
    else:
        await ctx.send("Needs to be done in a regular channel")
        return

@enabletwitchannouncement.error
async def enabletwitchannouncement_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send('Usage: `{}enabletwitchannouncement <twitch_channel_id>` \nIt must be used in a regular channel so it knows where to post announcements.'.format(CALL_CHARACTER))

@bot.command()
@commands.has_any_role("Mods", "Admin")
async def makepoll(ctx):
    await ctx.send("makepoll: Not implemented yet")

@bot.command()
async def addoption(ctx):
    await ctx.send("addoption: Not implemented yet")

@bot.command()
@commands.has_any_role("Mods", "Admin")
async def forceaddoption(ctx):
    await ctx.send("forceaddoption: Not implemented yet")

@bot.command()
@commands.has_any_role("Mods", "Admin")
async def removeoption(ctx):
    await ctx.send("forceaddoption: Not implemented yet")

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


bot.run(TOKEN)
