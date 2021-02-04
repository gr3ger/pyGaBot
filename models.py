import datetime

from peewee import Model, SqliteDatabase, TextField, IntegerField, DateTimeField

db = SqliteDatabase('gabot.db')


class BaseModel(Model):
    class Meta:
        database = db


class TwitchSettings(BaseModel):
    guild_id = IntegerField(primary_key=True)
    hook_uuid = TextField(default="")
    twitch_channel = TextField(default="")
    announcement_channel = TextField(default="")
    announcement_template = TextField(default="@here {streamer} is live: {stream_description} <{stream_link}>")
    cooldown_minutes = IntegerField(default=300)


class YoutubeSettings(BaseModel):
    guild_id = IntegerField(primary_key=True)
    youtube_channel = TextField(default="")
    announcement_channel = TextField(default="")
    announcement_template = TextField(default="{title} - {url}")
    last_update = DateTimeField(default=(datetime.datetime.now() + datetime.timedelta(minutes=5)))


class QueueItem(BaseModel):
    type = TextField(default="")
    user = IntegerField(default=0)
    channel = IntegerField(default=0)
    related_message = IntegerField(default=0)
    data = TextField(default="")
    expires = DateTimeField(default=datetime.datetime.now)


def initialize():
    db.connect()
    db.create_tables([TwitchSettings, YoutubeSettings])
