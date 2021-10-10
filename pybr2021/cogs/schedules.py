import asyncio
import datetime
import json
from datetime import datetime
from pprint import pprint

import discord
import httpx
from decouple import config
from discord.ext import commands, tasks
from loguru import logger
from pytz import timezone

CALENDAR_URL='https://www.googleapis.com/calendar/v3/calendars/7siodq5un9gqbqd4mmgf2poiqs@group.calendar.google.com/events?key=AIzaSyAIn8DyZFtthupLozgwIX3NUURFMWEIPb4&timeMin=2021-10-11T00:00:00.000Z&timeMax=2021-10-18T00:00:00.000Z&singleEvents=true&maxResults=9999&timeZone=UTC'
CALENDER_TIMEZONE='America/Sao_Paulo'

DISCORD_MSG_CHANNEL_ID='896438209020579951'

class Schedules(): # commands.Cog):
    
    # def __init__(self, bot: commands.Bot):
    #     self.bot = bot
        # self.weekly_meeting_points.start()
    
    def  __init__(self,bot):
        self.loop = asyncio.get_event_loop()
        self._events = None
        self._bot = bot
        self.load_events.start()

    @tasks.loop(minutes=1)
    async def load_events(self):
        url = CALENDAR_URL
        semaphore = asyncio.BoundedSemaphore(10)
        async with httpx.AsyncClient() as client:
            response = await self.http_get_json(semaphore, client, url)
        
        self._events = await self.parse_events(response)

   
    async def parse_events(self,response):
        events=[]
        for item in response.get("items"):
            events.append(
                {
                    'start':item.get('start').get('dateTime'),
                    'timezone':item.get('start').get('timeZone'),
                    'title':item.get('extendedProperties').get('private').get('title'),
                    'author':item.get('extendedProperties').get('private').get('author'),
                    'discord_channel':item.get('extendedProperties').get('private').get('discord_channel'),
                    'type':item.get('extendedProperties').get('private').get('type'),
                    'youtube_channel':item.get('extendedProperties').get('private').get('youtube_channel'),  
                }
            )
        return events

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

    async def next_events(self):
        now_calendar = datetime.utcnow().replace(tzinfo=timezone(CALENDER_TIMEZONE))
        event_show=[]
        for event in self._events:
            if event.get('start') >= now_calendar:
                event_show.append(await self.format_message(event))
                
    async def format_message(self,event):
        return f'{event.get("type")} - {event.get("start").strftime("%d-%m-%Y %H:%M")} - {event.get("title")} - {event.get("author")} - <{event.get("youtube_channel")}> - <{event.get("discord_channel")}>'

    async def send_event(self, message):
        channel = await self._bot.fetch_channel(DISCORD_MSG_CHANNEL_ID)
        await channel.send(message)







