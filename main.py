import configparser
import http.client
import json
import urllib.request
from datetime import datetime, timedelta
from os.path import exists

import discord
from discord.ext import commands
from tinydb import TinyDB

from poll import Poll, Option

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

db = TinyDB('polls.json')

# Config file parser
config = configparser.ConfigParser()
config.read('config.ini')

connection = http.client.HTTPSConnection('api.twitch.tv')
TOKEN = config['DEFAULT']['Token']
CALL_CHARACTER = config['DEFAULT']['CallCharacter']
TWITCH_CLIENT_ID = config['DEFAULT']['TwitchClientID']
TWITCH_CLIENT_SECRET = config['DEFAULT']['TwitchClientSecret']
bot = commands.Bot(command_prefix=CALL_CHARACTER)
callback = 'http://' + urllib.request.urlopen('https://ident.me').read().decode('utf8') + ':8000/'
poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def json_converter(o):
    if isinstance(o, datetime):
        return o.__str__()
    elif isinstance(o, Poll):
        return o.__dict__
    elif isinstance(o, Option):
        return o.__dict__
    else:
        return json.JSONEncoder.default(o)


def write_option(key, value):
    config['OPTIONS'][key] = value
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def read_option(key, default):
    try:
        return config["OPTIONS"][key]
    except KeyError:
        print("Key [{}] not found, using value {} instead.".format(key, default))
        return default


def get_twitch_user_by_name(usernames):
    if isinstance(usernames, list):
        usernames = ['login={0}'.format(i) for i in usernames]
        req = '/helix/users?' + '&'.join(usernames)
    else:
        req = '/helix/users?login=' + usernames

    print(req)
    connection.request('GET', req, None, headers={'Client-ID': TWITCH_CLIENT_ID})
    response = connection.getresponse()
    print(response.status, response.reason)
    re = response.read().decode()
    j = json.loads(re)
    return j


@bot.command()
async def hello(ctx):
    await ctx.send("Hello {}!".format(ctx.message.author.name))


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def disabletwitch(ctx):
    write_option("TwitchIntegrationEnabled", "False")
    await ctx.send("Twitch integration disabled")


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def enabletwitch(ctx, arg):
    print(ctx.message.channel.__repr__)
    if isinstance(ctx.message.channel, discord.TextChannel):
        user_json = get_twitch_user_by_name(arg)
        print(user_json)
        try:
            write_option("AnnouncementChannel", ctx.message.channel.id.__str__())
            write_option("TwitchIntegrationEnabled", "True")
            write_option("TwitchChannelID", user_json["data"][0]["id"])
            await ctx.send(
                "Successfully set the announcement channel to: {}, I will post here when {} comes online.".format(
                    ctx.message.channel.name, arg))
        except IndexError:
            await ctx.send("Could not find user {}".format(arg))
    else:
        await ctx.send("Needs to be done in a regular channel")
        return


@enabletwitch.error
async def enabletwitch_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send('Usage: `{}enabletwitch <twitch_channel_name>` '
                       '\nIt must be used in a regular channel so it knows where to post announcements.'
                       .format(CALL_CHARACTER))


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def makepoll(ctx, *args):
    time = datetime.now() + timedelta(hours=int(args[0]))
    poll = Poll(name=args[1], endtime=time)
    poll.add_option(ctx.message.author.name, ctx.message.author.id, " ".join(args[2:]))
    print(json.dumps(poll, default=json_converter))

    votes = ""

    embed = discord.Embed(title="*created by {creator_name}* - Poll is active, {hours_left} hours left.".format(
        creator_name=ctx.message.author.name, hours_left=args[0]))
    embed.set_author(name="{poll_name} - Poll number #{poll_number}".format(poll_name=args[1], poll_number=""),
                     icon_url=ctx.message.author.avatar_url)
    embed.set_thumbnail(url=ctx.message.guild.icon_url)
    for x in range(0, 9):
        if poll.options[x].name == "":
            continue
        embed.add_field(name="{num_emoji} - `{movie_title}` - *[{user}]*".format(num_emoji=poll_emojis[x],
                                                                                 movie_title=poll.options[x].name,
                                                                                 user=poll.options[x].author),
                        value="Votes: **[{votes}]**".format(votes=votes), inline=False)
    response = await ctx.send(embed=embed)
    poll.message_id = response.id

@makepoll.error
async def makepoll_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        poll = Poll()
        await ctx.send('Usage: `{}makepoll <hours> <"Poll title"> <first movie option>`'
                       .format(CALL_CHARACTER))
    else:
        await ctx.send(str(error))


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


if read_option("TwitchIntegrationEnabled", "False") == "True":
    print("Subscribing to channel status")
else:
    print("Didn't subscribe")

print("starting bot")
bot.run(TOKEN)
