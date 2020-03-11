import asyncio
import sys
from os.path import exists

import jsonpickle
from discord.ext import commands

import settings
from poll_cog import PollCog
from twitch_cog import TwitchCog

if sys.version_info < (3, 7):
    print("You are using Python version {major}.{minor}.{micro}, you need at least Python 3.7".format(
        major=sys.version_info.major, minor=sys.version_info.minor, micro=sys.version_info.micro))
    exit()

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

async_loop = asyncio.get_event_loop()
bot = commands.Bot(command_prefix=settings.CALL_CHARACTER)


@bot.command(hidden=True)
@commands.has_any_role("Mods", "Admin")
async def test(ctx):
    """Developer test function"""
    # await updatePollStatus(0)
    print(jsonpickle.encode(bot.get_cog("Polls").polls))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    bot.add_cog(PollCog(bot))
    bot.add_cog(TwitchCog(bot))


print("starting bot")
bot.run(settings.DISCORD_TOKEN)
