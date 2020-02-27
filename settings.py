# Config file parser
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

KEY_POLL_RATE = "TwitchPollRate"
KEY_TWITCH_INTEGRATION = "TwitchIntegrationEnabled"
KEY_TWITCH_CHANNEL = "TwitchChannel"
KEY_ANNOUNCEMENT_CHANNEL = "announcementchannel"


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
