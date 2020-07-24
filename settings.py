# Config file parser
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def write_option(key, value, category="BOT_VARS"):
    config[category][key] = value
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def read_option(key, default="NULL", category="BOT_VARS"):
    try:
        return config[category][key]
    except KeyError:
        print("Key [{}] not found, using value {} instead.".format(key, default))
        return default


KEY_TWITCH_INTEGRATION = "TwitchIntegrationEnabled"
KEY_TWITCH_CHANNEL = "TwitchChannel"
KEY_ANNOUNCEMENT_CHANNEL_TWITCH = "announcementchannel_twitch"
KEY_TWITCH_ACCESS_TOKEN = "twitchaccesstoken"

KEY_YOUTUBE_CHANNEL_ID = "YoutubeChannelId"
KEY_YOUTUBE_LAST_UPDATE = "YT_LAST_UPDATE"
KEY_ANNOUNCEMENT_CHANNEL_YOUTUBE = "announcementchannel_youtube"
KEY_YOUTUBE_INTEGRATION = "YoutubeIntegrationEnabled"

KEY_CATEGORY_TWITCH = "TWITCH"
KEY_CATEGORY_YOUTUBE = "YOUTUBE"
KEY_CATEGORY_DISCORD = "DISCORD"

DISCORD_TOKEN = config['DISCORD']['DiscordToken']
CALL_CHARACTER = config['DISCORD']['CallCharacter']
TWITCH_CLIENT_ID = config['TWITCH']['TwitchClientID']
TWITCH_CLIENT_SECRET = config['TWITCH']['TwitchClientSecret']
TWITCH_ANNOUNCEMENT_MESSAGE = config['TWITCH']['AnnouncementMessage']
YOUTUBE_ANNOUNCEMENT_MESSAGE = config['YOUTUBE']['AnnouncementMessage']
TWITCH_POLL_RATE = int(read_option("TwitchPollRate", "60", category=KEY_CATEGORY_TWITCH))
YOUTUBE_POLL_RATE = int(read_option("YoutubePollRate", "600", category=KEY_CATEGORY_YOUTUBE))
GOOGLE_API_KEY = config['YOUTUBE']['GoogleApiKey']
