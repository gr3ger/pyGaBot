# Config file parser
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

KEY_POLL_RATE = "TwitchPollRate"
KEY_TWITCH_INTEGRATION = "TwitchIntegrationEnabled"
KEY_TWITCH_CHANNEL = "TwitchChannel"
KEY_ANNOUNCEMENT_CHANNEL = "announcementchannel"
KEY_TWITCH_ACCESS_TOKEN = "twitchaccesstoken"

DISCORD_TOKEN = config['DEFAULT']['DiscordToken']
CALL_CHARACTER = config['DEFAULT']['CallCharacter']
TWITCH_CLIENT_ID = config['DEFAULT']['TwitchClientID']
TWITCH_CLIENT_SECRET = config['DEFAULT']['TwitchClientSecret']
TWITCH_ANNOUNCEMENT_MESSAGE = config['DEFAULT']['TwitchAnnouncementMessage']


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
