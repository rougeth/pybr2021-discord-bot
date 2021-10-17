import asyncio
import datetime
from collections import defaultdict
from datetime import date, datetime, timedelta
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
DISCORD_MSG_CHANNEL_ID = config("DISCORD_MSG_CHANNEL_ID","859819206584959007") # Python Brasil 2021 > Geral

START_TIME={"hour":8,"minute":00}
END_TIME={"hour":22,"minute":00}

DATE_FMT = "%d/%m/%Y %H:%M:%S"
HOUR_FMT = "%H:%M"
class Schedules(commands.Cog):

    def  __init__(self,bot):
        self.loop = asyncio.get_event_loop()
        self._events = None
        self.index = {}
        self._bot = bot
        self.alerts_type=["talk","closing","keynote","panel","light"]
        self._first_loop=True
        self.parse_start_end() #todo async
       #self.load_events.start()
        #self.next_events.start()
        #self.boteco_loop.start()
        #self.hello_loop.start()
        #self.first_loop.start()
     

    @tasks.loop(minutes=30)
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
        if await self.run_loop():
            logger.info("Send mext events")
            await self.send_next_events()
            
    async def send_next_events(self):
        logger.info("Sending Schedules to channel")
        now_calendar = datetime.now().replace(tzinfo=timezone(CALENDER_TIMEZONE))
        logger.info(f"Check events on {now_calendar}")
        today_events = self.index.get(now_calendar.date(),[])
        logger.info(f"Today events {len(today_events)}")
        today_events = sorted(today_events, key=lambda itens: itens['start'])
        event_show=[]
        if today_events:
            for event in today_events:
                if (now_calendar + timedelta(minutes=15)) >= event.get("start") >= now_calendar:
                    logger.info(f"Add evento do show {event.get('title')}") 
                    event_show.append(await self.format_message(event))
        logger.info(f"Events to show {len(event_show)}")
        if event_show:
            await self.sender(bot_msg.schedule_message_header + ''.join(event_show) + bot_msg.schedule_message_footer)
            logger.info("Next events sent to channel")

    async def format_message(self,event):
        paramns = {
            "hour":event.get("start").astimezone(timezone(event.get("timezone"))).strftime(HOUR_FMT),
            "type":event.get("type").capitalize(),
            "title":f"**{event.get('title').strip()}**",
            "author":f"*{event.get('author').strip()}*" if event.get("author") != "" else "",
            "youtube":f"<{event.get('youtube_channel')}>" if event.get("youtube_channel") != "" else "",
            "discord":f"<#{event.get('discord_channel')}>" if event.get("discord_channel") != "" else ""
        }
        return bot_msg.schedule_message.format(**paramns)
    
    @commands.command(name="boteco",brief="Send a remember to use buteco")
    async def boteco(self,ctx):
        await self.sender(bot_msg.buteco)

    @tasks.loop(minutes=9999)
    async def first_loop(self):
        self._first_loop = False

    @tasks.loop(hours=2)
    async def boteco_loop(self):
        if await self.run_loop():
            logger.info("Send Boteco Message")
            await self.sender(bot_msg.buteco)

    @commands.command(name="hello",brief="Send a hello message")
    async def hello(self,ctx):
        await self.sender(bot_msg.hello)

    @tasks.loop(minutes=60)
    async def hello_loop(self):
        if await self.run_loop():
            logger.info("Send hello message")
            await self.sender(bot_msg.hello)

    async def sender(self,message):
        channel = await self._bot.fetch_channel(DISCORD_MSG_CHANNEL_ID)
        await channel.send(message)

    def get_txt_channel(self):
        return DISCORD_MSG_CHANNEL_ID

    async def run_loop(self):
        run_loop = self.end_date_utc >= datetime.now().astimezone(tz=timezone('UTC')) >= self.start_date_utc and not self._first_loop
        logger.info(f"Loop will be run ? {run_loop}")
        return run_loop

    def parse_start_end(self):
        logger.info("Parsing Start an End Date")
        now = datetime.now()
        start_date={ 
            "year":now.year,
            "month":now.month,
            "day":now.day,
            **START_TIME,
        }
        end_date={ 
            "year":now.year,
            "month":now.month,
            "day":now.day,
            **END_TIME,
        }
        self.start_date = datetime(**start_date).replace(tzinfo=timezone(SHOW_TIMEZONE))
        self.end_date = datetime(**end_date).replace(tzinfo=timezone(SHOW_TIMEZONE))
        self.start_date_utc = datetime(**start_date).astimezone(tz=timezone('UTC'))
        self.end_date_utc = datetime(**end_date).astimezone(tz=timezone('UTC'))
        logger.info(f"Start Date: UTC:{self.start_date_utc.strftime(DATE_FMT)} -- Local:{self.start_date}")
        logger.info(f"End Date: UTC:{self.end_date_utc.strftime(DATE_FMT)} -- Local:{self.end_date}")

        


