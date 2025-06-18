# Import required dependencies
import pytz
import datetime
import datetime as dt_module
from datetime import datetime
from db_operations import get_reminder_info, get_reminder_user_ids, get_stored_prayer_timings, update_reminder_data, get_db_prayers, get_prayer_timings_data
from reminder_helper import get_prayer_timings
import asyncio
from discord.ext import commands
from db_operations import user_reminder_data_exists

prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

# Send the reminder to the user
async def send_reminder(client:commands.Bot, user_id, reminder_message):
    user = await client.fetch_user(user_id)
    await user.send(reminder_message)

# Get the name of the prayer the user will be reminded of
def get_prayer_name(prayer_timings, time):
    for element_num in range(5):
        if time == prayer_timings[element_num]:
            return prayers[element_num]

async def convert_time_format(end_time, start_time, user_id):
    hour_format = await get_reminder_info(user_id, "HourFormat")
    if hour_format == 0:
        return end_time, start_time
    else:
        end_time_obj = datetime.strptime(end_time, "%H:%M")
        end_time = end_time_obj.strftime("%I:%M %p")
        start_time_obj = datetime.strptime(start_time, "%H:%M")
        start_time = start_time_obj.strftime("%I:%M %p")
        return end_time, start_time

# Getting the ending time of the prayer and formatting both the start and end time according to the users time format preference
async def get_prayer_end_and_start_time(user_id, prayer_name, start_time):
    if prayer_name == "Fajr":
        end_time = await get_reminder_info(user_id, "Sunrise")
    elif prayer_name == "Dhuhr" or prayer_name == "Jummah":
        end_time = await get_reminder_info(user_id, "Asr")
    elif prayer_name == "Asr":
        if await get_reminder_info(user_id, "School") == 0:
            end_time = await get_reminder_info(user_id, "HanafiAsr")
        else:
            end_time = await get_reminder_info(user_id, "Maghrib")
    elif prayer_name == "Maghrib":
        end_time = await get_reminder_info(user_id, "Isha")
    elif prayer_name == "Isha":
        end_time = await get_reminder_info(user_id, "Midnight")
    
    end_time, start_time = await convert_time_format(end_time, start_time, user_id) 
    return end_time, start_time

# Formatting the reminder message
def get_reminder_message(prayer_name, prayer_start_time, prayer_end_time, remindEarly):
    if remindEarly == 1:
        remindEarly_str = " (Early)"
    else:   
        remindEarly_str = ""
    return (f"**__{prayer_name} Reminder{remindEarly_str}:__**\n**Start time:** {prayer_start_time}\n**End time:** {prayer_end_time}")

# Creating the process user task for all users in the database
async def reminder(client):
    user_ids = await get_reminder_user_ids()
    tasks = [process_user(client, user_id[0]) for user_id in user_ids]
    await asyncio.gather(*tasks)

# Checking asynchronously if the users prayer time has arrived and sending the reminder
async def process_user(client, user_id):
    while True:
        try:
            if await user_reminder_data_exists(user_id) == False:
                return
            timezone = await get_reminder_info(user_id, "Timezone")
            current_time = datetime.now(pytz.timezone(timezone)) # Getting the current time according to the users timezne
            prayer_timings = await get_stored_prayer_timings(user_id)
            for time in prayer_timings:
                if time != None: # If a time is None that means the user hasnt selected that prayer
                    stored_date = await get_reminder_info(user_id, "Date")
                    remindEarly = await get_reminder_info(user_id, "RemindEarly")
                    prayer_time_obj = datetime.strptime(f"{stored_date} {time}", "%d-%m-%Y %H:%M")
                    prayer_time = pytz.timezone(timezone).localize(prayer_time_obj) # Adding the timezone adjustment to the time to make it timezone aware
                    if remindEarly == 1: # Subtracting 5 mins from the prayer time if the user wants to be reminded early
                        prayer_time = prayer_time - dt_module.timedelta(minutes=5)
                    time_difference = prayer_time - current_time
                    wait = False
                    prayer_time_arrived = False
                    if time_difference < dt_module.timedelta(seconds=60) and time_difference.days >= 0: # Checking if the time left before the prayer is within a minute
                        wait = True
                        prayer_time_arrived = True
                    elif time_difference <= dt_module.timedelta(seconds=0) and time_difference >= dt_module.timedelta(days=-1, hours=23, minutes=59, seconds=0): # Checking if the prayer time has already passed by and if its been less than a minute since it has
                        prayer_time_arrived = True
                    cancelReminder = await get_reminder_info(user_id, "CancelReminder")
                    if prayer_time_arrived:
                        if cancelReminder: # Checking if the user had cancelled the upcoming reminder
                            await update_reminder_data(user_id, "CancelReminder", None)
                            break       
                        if wait:
                            await asyncio.sleep(time_difference.total_seconds()) # If the prayer time is withing a minute then wait for that time to pass and then send a reminder
                        # Get the prayer names and timings and send the reminder
                        prayer_name = get_prayer_name(prayer_timings, time)
                        dayOfTheWeek = current_time.strftime('%A')
                        if dayOfTheWeek == 'Friday' and prayer_name == 'Dhuhr':
                            prayer_name = 'Jummah'
                        prayer_end_time, prayer_start_time = await get_prayer_end_and_start_time(user_id, prayer_name, time)
                        message = get_reminder_message(prayer_name, prayer_start_time, prayer_end_time, remindEarly)
                        await send_reminder(client, user_id, message)
                        break # If a prayer time has arrived then dont check the other prayers
            beforeDhuhr = await get_reminder_info(user_id, "BeforeDhuhr")
            if beforeDhuhr != None:
                forbiddenTimesReminder = 1 #To use later in the code
                beforeDhuhr_obj = datetime.strptime(f"{stored_date} {beforeDhuhr}", "%d-%m-%Y %H:%M")
                beforeDhuhr_obj = pytz.timezone(timezone).localize(beforeDhuhr_obj) # Adding the timezone adjustment to the time to make it timezone aware
                time_difference = beforeDhuhr_obj - current_time
                wait = False
                forbidden_time_arrived = False
                if time_difference < dt_module.timedelta(seconds=60) and time_difference.days >= 0: # Checking if the time left before the forbidden is within a minute
                    wait = True
                    forbidden_time_arrived = True
                elif time_difference <= dt_module.timedelta(seconds=0) and time_difference >= dt_module.timedelta(days=-1, hours=23, minutes=59, seconds=0): # Checking if the forbidden time has already passed by and if its been less than a minute since it has
                    forbidden_time_arrived = True
                if forbidden_time_arrived:
                    if wait:
                        await asyncio.sleep(time_difference.total_seconds()) # If the forbidden time is withing a minute then wait for that time to pass and then send an alert
                    start_time = beforeDhuhr    
                    end_time = beforeDhuhr_obj + dt_module.timedelta(minutes=25)
                    end_time = end_time.strftime("%H:%M")
                    end_time, start_time = await convert_time_format(end_time, start_time, user_id)
                    message = f":warning: **__The Forbidden Time to Pray Voluntary Prayers has started:__ ** :warning:\n**Start time:** {start_time}\n**End time:** {end_time}"
                    await send_reminder(client, user_id, message)
                else:
                    sunrise = await get_reminder_info(user_id, "Sunrise")
                    sunrise_obj = datetime.strptime(f"{stored_date} {sunrise}", "%d-%m-%Y %H:%M")
                    sunrise_obj = pytz.timezone(timezone).localize(sunrise_obj) # Adding the timezone adjustment to the time to make it timezone aware
                    time_difference = sunrise_obj - current_time
                    wait = False
                    forbidden_time_arrived = False
                    if time_difference < dt_module.timedelta(seconds=60) and time_difference.days >= 0: # Checking if the time left before the forbidden is within a minute
                        wait = True
                        forbidden_time_arrived = True
                    elif time_difference <= dt_module.timedelta(seconds=0) and time_difference >= dt_module.timedelta(days=-1, hours=23, minutes=59, seconds=0): # Checking if the forbidden time has already passed by and if its been less than a minute since it has
                        forbidden_time_arrived = True
                    if forbidden_time_arrived:
                        if wait:
                            await asyncio.sleep(time_difference.total_seconds()) # If the forbidden time is withing a minute then wait for that time to pass and then send an alert
                        start_time = sunrise
                        end_time = sunrise_obj + dt_module.timedelta(minutes=15)
                        end_time = end_time.strftime("%H:%M")
                        end_time, start_time = await convert_time_format(end_time, start_time, user_id)
                        message = f":warning: **__The Forbidden Time to Pray Voluntary Prayers has started:__ ** :warning:\n**Start time:** {start_time}\n**End time:** {end_time}"
                        await send_reminder(client, user_id, message)
            else:
                forbiddenTimesReminder = 0
            stored_date = datetime.strptime(stored_date, "%d-%m-%Y").date()
            current_date = (datetime.now(pytz.timezone(timezone))).date() # Get current date according to the users timezone
            # Update the date and the prayer timings if the stored date comes before the current date
            if current_date > stored_date:
                current_date = current_date.strftime("%d-%m-%Y")
                await update_reminder_data(user_id, "Date", current_date)
                selected_prayers = await get_db_prayers(user_id)
                reminder_info = await get_prayer_timings_data(user_id)
                country, city, date, school, midnightMode, method = reminder_info[0], reminder_info[1], reminder_info[2], reminder_info[3], reminder_info[4], reminder_info[5]
                prayer_timings, beforeDhuhr = await get_prayer_timings(country, city, date, school, midnightMode, method, selected_prayers, forbiddenTimesReminder)
                await update_reminder_data(user_id, "Selected Prayers", prayer_timings)
                if forbiddenTimesReminder == 1:
                    await update_reminder_data(user_id, "BeforeDhuhr", beforeDhuhr)
            await asyncio.sleep(60) # Wait for a minute before checking again
        except Exception as e:
            print(f"\n\nERROR IN reminder PROCESS_USER FUNCTION: {e}\n\n")
            await asyncio.sleep(60)
