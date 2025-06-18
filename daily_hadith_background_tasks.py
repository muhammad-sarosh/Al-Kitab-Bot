# Import required dependencies
import asyncio
import pytz
import datetime as dt_module
from datetime import datetime
from db_operations import get_daily_user_ids, get_daily_data, update_daily_data
import random
from shared_resources import books
import requests
import discord

# Discord word limit is 2000 so a message has to be split into multiple messages if its too long
async def divide_message(message):
    messages_list = []
    for i in range(0, len(message), 2000):
        messages_list.append(message[i:i+2000])
    return messages_list

async def get_random_hadith(language):
    bookSlugs = ['sahih-bukhari', 'sahih-muslim', 'al-tirmidhi', 'abu-dawood', 'ibn-e-majah', 'sunan-nasai']
    selected_book = random.choice(bookSlugs)
    hadith_num = random.randint(1, books[selected_book])

    params = {
        'book': selected_book,
        'hadithNumber':hadith_num,
    }

    data = requests.get('https://www.hadithapi.com/api/hadiths/?apiKey=$2y$10$xxSmbj6QTXNoYCVeEN8MyShWyIx2suugbtgOQaATomCeHEmNxKiK', params=params)
    data = data.json()

    if language != 'arabic':
        narrator = data['hadiths']['data'][0][language + 'Narrator']
    else:
        narrator = ""

    language = language[0].upper() + language[1:]
    book_name = data['hadiths']['data'][0]['book']['bookName']
    chapter = data['hadiths']['data'][0]['chapter']['chapter' + language]
    heading = data['hadiths']['data'][0]['heading' + language]
    hadith = data['hadiths']['data'][0]['hadith' + language]
    status = data['hadiths']['data'][0]['status']
    status = data['hadiths']['data'][0]['status']
    status = status[0].upper() + status[1:]
    hadith = hadith.replace("`", "")

    # Maximum length for a field in an embed is 1024 characters so if the hadith is longer than that then we send it as a normal message else send it as an embed
    if len(hadith) <= 1024:
        if narrator is not None and narrator != "" :
            hadith = f"{narrator} {hadith}"
        if chapter == "":
            chapter = "Unavailible"
        if status == "":
            status = "Unavailible"
        embed = discord.Embed(title=f'Hadith in {language}', color=0xff8000)
        embed.add_field(name='Book', value=book_name, inline=False)
        embed.add_field(name='Chapter', value=chapter, inline=False)
        if heading is not None and not heading == "":
            embed.add_field(name='Heading', value=heading, inline=False)
        embed.add_field(name='Hadith', value=hadith, inline=False)
        embed.add_field(name='Grade', value=status, inline=False)
        embed.add_field(name='Hadith Number', value=hadith_num, inline=False)
        embed.set_footer(text="Requested by Al Kitab Bot")
        return embed
    else:
        if chapter:
            chapter_str = f"**Chapter:** {chapter}\n\n"
        else:
            chapter_str = ""

        if narrator != "":
            narrator_str = f"{narrator} "
        else:
            narrator_str = ""

        if heading:
            heading_str = f"**__{heading}:__**\n\n"
        else:
            heading_str = ""

        reference_str = f"**Hadith Number:** {hadith_num}"
        hadith_str = f"**Book: **{book_name}\n\n{chapter_str}{heading_str}{narrator_str}{hadith}\n\n**Grade:** {status}\n\n{reference_str}"
        return hadith_str

# Creating the process user task for all users in the database
async def daily_hadith_sender(client):
    user_ids = await get_daily_user_ids('DailyHadithData')
    tasks = [process_user(client, user_id[0]) for user_id in user_ids]
    await asyncio.gather(*tasks)

# Checking asynchronously if the time to send the user their daily hadith has arrived
async def process_user(client, user_id):
    while True:
        try:
            if await get_daily_data('DailyHadithData', user_id, 'HadithUserID') is None:
                return
            timezone = await get_daily_data('DailyHadithData', user_id, 'Timezone')
            timezone = timezone[0]
            current_time = datetime.now(pytz.timezone(timezone)) # Getting the current time according to the users timezone
            sent = await get_daily_data('DailyHadithData', user_id, 'MessageSent')
            sent = sent[0]
            if not sent: # If sent = 0 then the the daily hadith hasnt been sent today
                time_to_send = await get_daily_data('DailyHadithData', user_id, 'TimeToSend')
                time_to_send = time_to_send[0]
                time_to_send_obj = datetime.strptime(f"{current_time.date()} {time_to_send}", "%Y-%m-%d %H:%M") # Making a datetime object
                time_to_send = pytz.timezone(timezone).localize(time_to_send_obj) # Making the time_to_send object timezone aware
                language = await get_daily_data('DailyHadithData', user_id, 'Language')
                language = language[0]
                time_arrived = False
                wait = False

                time_difference = time_to_send - current_time

                if time_difference < dt_module.timedelta(minutes=30) and time_difference.days >= 0: # Checking if the time to send the hadith is withing 30 minutes
                    time_arrived = True
                    wait = True
                elif time_difference <= dt_module.timedelta(seconds=0) and time_difference >= dt_module.timedelta(days=-1, hours=23, minutes=30, seconds=0): # Checking if the time to send the hadith has past by and if its been less than 30 minutes since it did
                    time_arrived = True
                
                if time_arrived:
                    if wait:
                        await asyncio.sleep(time_difference.total_seconds()) # Wait till the time to send the hadith has arrived if it was withing 30 minutes
                    user = await client.fetch_user(user_id)
                    data = await get_random_hadith(language)
                    if type(data) != str: # If the return object is not a string then send it as an embed
                        await user.send("**__Daily Hadith:__**", embed=data)
                    else: # If it is a string then check if the string is less than 2000 characters and send it as a single message otherwise split it into multiple messages and then send it
                        data = '**__Daily Hadith:__**\n\n' + data
                        if len(data) <= 2000:
                            await user.send(data)
                        else:
                            messages_list = await divide_message(data)
                            for chunk in messages_list:
                                await user.send(chunk)
                    await update_daily_data('DailyHadithData', user_id, 'MessageSent', 1) # Change the value of MessageSent to 1 to indicate that the hadith for today has been sent
            current_date = current_time.date()
            stored_date = await get_daily_data('DailyHadithData', user_id, 'Date')
            stored_date = stored_date[0]
            stored_date = datetime.strptime(stored_date, "%Y-%m-%d").date() # Making the stored date a datetime object
            # If the current date is ahead of the stored date then update the stored date
            if current_date > stored_date:
                await update_daily_data('DailyHadithData', user_id, 'Date', current_date)
                await update_daily_data('DailyHadithData', user_id, 'MessageSent', 0)
            await asyncio.sleep(1800) # Wait for 30 minutes before checking again
        except Exception as e:
            print(f'\n\n\nERROR IN hadith PROCESS_USER FUNCTION: {e}\n\n\n')
            await asyncio.sleep(1800)