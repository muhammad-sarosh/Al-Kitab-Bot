# Import required dependencies
import asyncio
import pytz
import datetime as dt_module
from datetime import datetime
from db_operations import get_daily_user_ids, get_daily_data, update_daily_data
import random
from shared_resources import num_verses_in_surah
import requests
from discord import Embed

async def get_random_verse(language):
        if language == 'english':
            key = 'translation'
            title = 'Quran English Translation'
        else:
            key = 'arabic_text'
            title = 'Quran Arabic'
        chapter = random.randint(1, 114)
        verse = random.randint(1, num_verses_in_surah[chapter])
        data = requests.get('https://quranenc.com/api/v1/translation/aya/english_saheeh/' + str(chapter) + '/' + str(verse))
        data = data.json()
        text = data['result'][key]
        text = text + f" -{chapter}:{verse}"
        embed = Embed(title=title, description=text, color=0xff8000)
        embed.set_footer(text="Requested by Al Kitab Bot")
        return embed

# Creating the process user task for all users in the database
async def daily_verse_sender(client):
    user_ids = await get_daily_user_ids('DailyVerseData')
    tasks = [process_user(client, user_id[0]) for user_id in user_ids]
    await asyncio.gather(*tasks)

async def process_user(client, user_id):
    while True:
        try:
            if await get_daily_data('DailyVerseData', user_id, 'VerseUserID') is None:
                return
            timezone = await get_daily_data('DailyVerseData', user_id, 'Timezone')
            timezone = timezone[0]
            current_time = datetime.now(pytz.timezone(timezone)) # Getting the current time according to the users timezone
            sent = await get_daily_data('DailyVerseData', user_id, 'MessageSent')
            sent = sent[0]
            if not sent: # If sent = 0 then the the daily verse hasnt been sent today
                time_to_send = await get_daily_data('DailyVerseData', user_id, 'TimeToSend')
                time_to_send = time_to_send[0]
                time_to_send_obj = datetime.strptime(f"{current_time.date()} {time_to_send}", "%Y-%m-%d %H:%M") # Making a datetime object
                time_to_send = pytz.timezone(timezone).localize(time_to_send_obj) # Making the time_to_send object timezone aware
                language = await get_daily_data('DailyVerseData', user_id, 'Language')
                language = language[0]
                time_arrived = False
                wait = False

                time_difference = time_to_send - current_time

                if time_difference < dt_module.timedelta(minutes=30) and time_difference.days >= 0: # Checking if the time to send the verse is withing 30 minutes
                    time_arrived = True
                    wait = True
                elif time_difference <= dt_module.timedelta(seconds=0) and time_difference >= dt_module.timedelta(days=-1, hours=23, minutes=30, seconds=0): # Checking if the time to send the verse has past by and if its been less than 30 minutes since it did 
                    time_arrived = True
                
                if time_arrived:
                    if wait:
                        await asyncio.sleep(time_difference.total_seconds()) # Waiting till the time to send the verse has arrived if the time was withing 30 minutes
                    embed = await get_random_verse(language)
                    user = await client.fetch_user(user_id)
                    await user.send("**__Daily Verse:__**", embed=embed)
                    await update_daily_data('DailyVerseData', user_id, 'MessageSent', 1)
            current_date = current_time.date()
            stored_date = await get_daily_data('DailyVerseData', user_id, 'Date')
            stored_date = stored_date[0]
            stored_date = datetime.strptime(stored_date, "%Y-%m-%d").date() # Making the stored date a datetime object
            # Updating the stored date if the current date is ahead of it
            if current_date > stored_date:
                await update_daily_data('DailyVerseData', user_id, 'Date', current_date)
                await update_daily_data('DailyVerseData', user_id, 'MessageSent', 0)
            await asyncio.sleep(1800) # Wait for 30 minutes before checking again
        except Exception as e:
            print(f'\n\n\nERROR IN verse PROCESS_USER FUNCTION: {e}\n\n\n')
            await asyncio.sleep(1800)