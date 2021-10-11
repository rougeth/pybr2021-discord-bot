import asyncio
import datetime
from collections import defaultdict
from datetime import datetime, timedelta
from pprint import pprint

import bot_msg
import httpx
from decouple import config
from discord.ext import commands, tasks
from loguru import logger
from pytz import timezone

CALENDAR_URL='https://www.googleapis.com/calendar/v3/calendars/7siodq5un9gqbqd4mmgf2poiqs@group.calendar.google.com/events?key=AIzaSyAIn8DyZFtthupLozgwIX3NUURFMWEIPb4&timeMin=2021-10-11T00:00:00.000Z&timeMax=2021-10-18T00:00:00.000Z&singleEvents=true&maxResults=9999&timeZone=UTC'
CALENDER_TIMEZONE= 'UTC'
SHOW_TIMEZONE='America/Sao_Paulo'
#DISCORD_MSG_CHANNEL_ID='859819206584959007'  # Python Brasil 2021 > Geral
DISCORD_MSG_CHANNEL_ID = '862433669322899457'

DATE_FMT = "%d/%m/%Y %H:%M:%S"
HOUR_FMT = "%H:%M"
class Schedules(commands.Cog):

    def  __init__(self,bot):
        self.loop = asyncio.get_event_loop()
        self._events = None
        self.index = {}
        self._bot = bot
        self.alerts_type=["talk","closing","keynote","panel"]
        self.load_events.start()

    @tasks.loop(minutes=60)
    async def load_events(self):
        logger.info("Loading calendar events.")
        url = CALENDAR_URL
        semaphore = asyncio.BoundedSemaphore(10)
        async with httpx.AsyncClient() as client:
            response = await self.http_get_json(semaphore, client, url)

        logger.info("Parsing events")
        self._events = await self.parse_events(response)
        self.index = self.create_index(self._events)
        logger.info("Calendar finished load")

    async def parse_events(self,response):
        events=[]
        for item in response.get("items"):
            if item.get('extendedProperties').get('private').get('type') in self.alerts_type:
                events.append(
                    {
                        'start': datetime.strptime(item.get('start').get('dateTime'),'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone(CALENDER_TIMEZONE)),
                        'timezone':item.get('start').get('timeZone'),
                        'location':item.get('location'),
                        'title':item.get('extendedProperties').get('private').get('title'),
                        'author':item.get('extendedProperties').get('private').get('author'),
                        'discord_channel':item.get('extendedProperties').get('private').get('discord_channel'),
                        'type':item.get('extendedProperties').get('private').get('type'),
                        'youtube_channel':item.get('extendedProperties').get('private').get('youtube_channel'),
                    }
            )
        return events

    def create_index(self,events):
        index = defaultdict(list)
        for event in events:
            index[event["start"].date()].append(event)

        return index

    async def http_get_json(self,semaphore, client, url, retry=3):
        async with semaphore:
            try:
                response = await client.get(url)
                return response.json()
            except httpx.ReadTimeout:
                if retry > 0:
                    await asyncio.sleep(5)
                    return await self.http_get_json(semaphore, client, url, retry - 1)
                logger.exception("Erro")

    @commands.command(name="next-talks",brief="Send a remember of next calls")
    async def next_events_manual(self,ctx):
        await self.send_next_events()

    @tasks.loop(minutes=15)
    async def next_events(self):
        await self.send_next_events()

    async def send_next_events(self):
        logger.info("Sending Schedules to channel")
        now_calendar = datetime.now().replace(tzinfo=timezone(CALENDER_TIMEZONE))
        today_events = self.index.get(now_calendar.date(),[])
        today_events = sorted(today_events, key=lambda itens: itens['start'])
        event_show=[]
        if today_events:
            for event in today_events:
                print(now_calendar + timedelta(minutes=15))
                if (now_calendar + timedelta(minutes=15)) >= event.get("start") >= now_calendar:
                    print(event.get("start"))
                    event_show.append(await self.format_message(event))
        if event_show:
            await self.send_event(bot_msg.schedule_message_header + ''.join(event_show))
            logger.info("Next events sent to channel")

    async def format_message(self,event):
        paramns = {
            "hour":event.get("start").astimezone(timezone(event.get("timezone"))).strftime(HOUR_FMT),
            "type":event.get("type").capitalize(),
            "title":f"**{event.get('title').strip()}**",
            "author":f"*{event.get('author').strip()}*" if event.get("author") != "" else "",
            "youtube":f"<{event.get('youtube_channel')}>",
            "discord":f"<#{event.get('discord_channel')}>" if event.get("discord_channel") != "" else ""
        }
        return bot_msg.schedule_message.format(**paramns)

    async def send_event(self, message):
        channel = await self._bot.fetch_channel(DISCORD_MSG_CHANNEL_ID)
        await channel.send(message)
