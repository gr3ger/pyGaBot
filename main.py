import asyncio
import configparser
import http.client
import json
import os
import pickle
import sys
import threading
import time
import urllib.request
from datetime import datetime
from os.path import exists

import discord
import jsonpickle
from discord.ext import commands
from flask import Flask, request, Response

from poll import Poll, Option

if sys.version_info < (3, 7):
    print("You are using Python version {major}.{minor}.{micro}, you need at least Python 3.7".format(
        major=sys.version_info.major, minor=sys.version_info.minor, micro=sys.version_info.micro))
    exit()

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

# Config file parser
config = configparser.ConfigParser()
config.read('config.ini')

async_loop = asyncio.get_event_loop()

connection = http.client.HTTPSConnection('api.twitch.tv')
DISCORD_TOKEN = config['DEFAULT']['DiscordToken']
CALL_CHARACTER = config['DEFAULT']['CallCharacter']
TWITCH_CLIENT_ID = config['DEFAULT']['TwitchClientID']
TWITCH_CLIENT_SECRET = config['DEFAULT']['TwitchClientSecret']
WEBHOOK_PORT = config['DEFAULT']['WebhookPort']
bot = commands.Bot(command_prefix=CALL_CHARACTER)
lease_seconds = 60 * 60 * 24 * 10
callback = 'http://' + urllib.request.urlopen('https://ident.me').read().decode('utf8') + ':' + WEBHOOK_PORT + '/'
poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

polls = []

if os.path.isfile('polls.bin'):
    polls = pickle.load(open("polls.bin", "rb"))


def get_external_ip():
    return urllib.request.urlopen('https://ident.me').read().decode('utf8')


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


# This will fetch the original message, and read all the reactions which in turn will update even if stuff
# happened while offline! Should probably only be used when closing the poll because of the HTTP calls.
async def updatePollStatus(id):
    message = await bot.get_channel(polls[id].channel_id).fetch_message(polls[id].message_id)
    print(message)
    for reaction in message.reactions:
        option_index = 0
        try:
            option_index = poll_emojis.index(str(reaction))
        except ValueError:
            continue

        final_string = "{}: ".format(reaction)
        polls[id].options[option_index].votes.clear()
        async for user in reaction.users():
            polls[id].options[option_index].votes.append(str(user))
            final_string += "{}, ".format(user)
        print(final_string)


@bot.command()
async def test(ctx):
    await updatePollStatus(0)
    print(jsonpickle.encode(polls))


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def disabletwitch(ctx):
    write_option("TwitchIntegrationEnabled", "False")
    await ctx.send("Twitch integration disabled")


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def enabletwitch(ctx, twitch_username):
    print(ctx.message.channel.id.__str__)
    if isinstance(ctx.message.channel, discord.TextChannel):
        user_json = get_twitch_user_by_name(twitch_username)
        print(user_json)
        try:
            write_option("AnnouncementChannel", ctx.message.channel.id.__str__())
            write_option("TwitchIntegrationEnabled", "True")
            write_option("TwitchChannelID", user_json["data"][0]["id"])
            await ctx.send(
                "Successfully set the announcement channel to: {}, I will post here when {} comes online.".format(
                    ctx.message.channel.name, twitch_username))
            subscribe_to_twitch()
        except IndexError:
            await ctx.send("Could not find user {}".format(twitch_username))
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
    endtime = time.time() + (int(args[0]) * 60 * 60)
    print(datetime.fromtimestamp(endtime).__str__())

    poll = Poll(name=args[1], endtime=endtime)
    poll.add_option(ctx.message.author.name, ctx.message.author.id,
                    " ".join(args[2:]))
    print(json.dumps(poll, default=json_converter))

    polls.append(poll)

    votes = ""
    embed = discord.Embed(title="*created by {creator_name}* - Poll is active, {hours_left} hours left.".format(
        creator_name=ctx.message.author.name, hours_left=args[0]), color=0xff3333)
    embed.set_author(
        name="{poll_name} - Poll number #{poll_number}".format(poll_name=args[1], poll_number=str(len(polls))),
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
    poll.channel_id = ctx.message.channel.id
    pickle.dump(polls, open("polls.bin", "wb"))


@makepoll.error
async def makepoll_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        poll = Poll()
        await ctx.send('Usage: `{call_character}makepoll <hours> <"Poll title"> <first movie option>`'
                       '\nExample: `{call_character}makepoll 48 "Gabber Movie Poll" Yeeting with Wolves`'
                       .format(call_character=CALL_CHARACTER))
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
    await ctx.send("removeoption: Not implemented yet")


def subscribe_to_twitch():
    print("callback to: " + callback)
    headers = {'Client-ID': TWITCH_CLIENT_ID,
               'Content-type': 'application/json'}

    topic = 'https://api.twitch.tv/helix/streams?user_id=' + read_option("twitchchannelid", 0)
    foo = {'hub.mode': 'subscribe',
           'hub.topic': topic,
           'hub.callback': callback,
           'hub.lease_seconds': lease_seconds,
           'hub.secret': TWITCH_CLIENT_SECRET
           }

    json_foo = json.dumps(foo)
    connection.request('POST', '/helix/webhooks/hub', body=json_foo, headers=headers)
    response = connection.getresponse()
    print(response.status, response.reason)
    print(response.read().decode())


async def send_message_to_channel(string, channel: int):
    print("Sending announcement to channel {}".format(channel))
    channel = bot.get_channel(channel)
    await channel.send(string)


# Start webhook
app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        print(request.args, file=sys.stderr)

        req_data = request.get_json()
        print(json.dumps(req_data), file=sys.stderr)

        if "hub.topic" in request.args:
            print("Responding to challenge", file=sys.stderr)
            response = Response(response="")
            response.status_code = 200
            response.content_type = 'text/plain'
            response.set_data(request.args['hub.challenge'])
            return response
        else:
            return "hello!"
    if request.method == 'POST':
        req_data = request.get_json()
        print("RESPONSE THROUGH WEBHOOK!", file=sys.stderr)
        print(json.dumps(req_data), file=sys.stderr)

        if len(req_data['data']) == 0:
            print("Empty data POST, ignoring", file=sys.stderr)
            return Response(status=200, response="")

        asyncio.run_coroutine_threadsafe(
            send_message_to_channel(
                "{name} is **{status}**\nGame id: **{game_id}**\nTitle: **{title}**".format(
                    name=req_data['data'][0]['user_name'],
                    status=req_data['data'][0]['type'],
                    game_id=req_data['data'][0]['game_id'],
                    title=req_data['data'][0]['title']), int(read_option("announcementchannel", 0))),
            async_loop).result()
        response = Response(response="")
        response.status_code = 200
        return response


def runStartupSubscription():
    time.sleep(5.0)
    if read_option("TwitchIntegrationEnabled", "False") == "True":
        print("Subscribing to channel status")
        subscribe_to_twitch()
    else:
        print("Didn't subscribe")


def runWebServer():
    print("Start webserver")
    app.run(host='0.0.0.0', port=int(WEBHOOK_PORT), debug=False)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    threading.Thread(target=runWebServer).start()
    threading.Thread(target=runStartupSubscription).start()


@bot.event
async def on_raw_reaction_add(payload):
    print(payload)


@bot.event
async def on_raw_reaction_remove(payload):
    print(payload)


print("starting bot")
bot.run(DISCORD_TOKEN)
