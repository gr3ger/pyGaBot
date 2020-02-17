import urllib.request
import http.client
import json
from flask import Flask, url_for
from flask_websub.subscriber import Subscriber, SQLite3TempSubscriberStorage, SQLite3SubscriberStorage, discover
from os.path import exists
import discord
from discord.ext import commands
import configparser

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

# PubSub stuff
app = Flask(__name__)
app.config['SERVER_NAME'] = 'https://api.twitch.tv/helix/webhooks/hub'
subscriber = Subscriber(SQLite3SubscriberStorage('client_data.sqlite3'),
                        SQLite3TempSubscriberStorage('client_data.sqlite3'))
app.register_blueprint(subscriber.build_blueprint(url_prefix='/callbacks'))

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


@subscriber.add_success_handler
def on_success(topic_url, callback_id, mode):
    print("SUCCESS!", topic_url, callback_id, mode)


@subscriber.add_error_handler
def on_error(topic_url, callback_id, msg):
    print("ERROR!", topic_url, callback_id, msg)


@subscriber.add_listener
def on_topic_change(topic_url, callback_id, body):
    print('TOPIC CHANGED!', topic_url, callback_id, body)


@app.route('/subscribe')
def subscribe_route():
    id = subscriber.subscribe(**discover(callback))
    return 'Subscribed. ' + url_for('renew_route', id=id, _external=True)


@app.route('/renew/<id>')
def renew_route(id):
    new_id = subscriber.renew(id)
    return 'Renewed: ' + url_for('unsubscribe_route', id=new_id, _external=True)


@app.route('/unsubscribe/<id>')
def unsubscribe_route(id):
    subscriber.unsubscribe(id)
    return 'Unsubscribed: ' + url_for('cleanup_and_renew_all', _external=True)


@app.route('/cleanup_and_renew_all')
def cleanup_and_renew_all():
    subscriber.cleanup()
    # 9 days, to make sure every single subscription is renewed
    subscriber.renew_close_to_expiration(24 * 60 * 60 * 9)
    return 'Done!'


def write_option(key, value):
    config['OPTIONS'][key] = value
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def read_option(key, default):
    try:
        return config["OPTIONS"][key]
    except KeyError:
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
                "Successfully set the announcement channel to: {}, I will post here when user {} comes online."
                    .format(ctx.message.channel.name, arg))
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


print("starting bot")
bot.run(TOKEN)
print("starting pubsub")
app.run(host='0.0.0.0', port=8081)
if read_option("TwitchIntegrationEnabled", "False") == "True":
    print("Subscribing to channel status")
    subscriber.subscribe(**discover('https://api.twitch.tv/helix/streams?user_id=' + read_option("twitchchannelid", 0)))
else:
    print("Didn't subscribe")
