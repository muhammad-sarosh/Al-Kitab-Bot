# Import required dependencies
import discord
from discord.ext import commands
from discord import app_commands
from discord import Embed
from db_operations import user_reminder_data_exists, insert_reminder_data, update_reminder_data, get_prayer_timings_data, get_db_prayers, delete_reminder_data, get_reminder_info
from datetime import datetime
import requests
import pytz
from reminder_helper import *
from reminder_background_tasks import process_user

class reminder_commands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='setupreminder', description='Set up your prayer reminder')
    async def setupreminder(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if interaction.guild != None:
                await interaction.followup.send("For privacy reasons, this command can only be used in DMs.")
                return

            user_id = interaction.user.id

            if user_id in users_list:
                await interaction.followup.send("You are already using a command. Wait for for the current command to timeout if you would like to use this command.")
                return
            users_list.append(user_id)

            if await user_reminder_data_exists(user_id):
                await interaction.followup.send("You already have a reminder set up. If you would like to update any info use the `/updatereminder` command, or if you would like to set up the whole reminder again use the `/disablereminder` command and *then* the `/setupreminder` commannd.")
                return
            
            instance = mode_selection_dropdown()
            view = dropdownView(instance)
            message = "Would you like to select your Country, City and Timezone manually, or enter an address and have the bot determine these things automatically?"
            view = await get_info(self, interaction, message, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            mode = view.children[0].mode
            
            if mode == 'Automatic':
                while True:
                    message = "Please type your location, make sure the location is accurate for the most accurate prayer timings. E.g '16-2 Rosslyn Rd, Watford, UK'. Type 'cancel' to cancel:"
                    location = await get_location(self, interaction, message)
                    if location is None:
                        await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                        return
                    elif location == 'cancel':
                        await interaction.followup.send("Cancelled setup.")
                        return
                    
                    data = geo_adhan_lookup(location, 1, False)
                    if data['err'] == 'Error: Location not found':
                        await interaction.followup.send("Invalid location. (Try making your location more accurate or less accurate)")
                        continue
                    elif data['success'] is False:
                        await interaction.followup.send('Automatic mode is not working right now. Please use the command again and try manual mode')
                        return
                    
                    instance = location_confirmation_dropdown()
                    view = dropdownView(instance)
                    confirmation_message = f"**__Location Data:__**\n"
                    for key, value in data['data']['address']['data'].items():
                        confirmation_message += f"{key}: {value}\n"
                    confirmation_message += "\nIs this location data correct?"
                    view = await get_info(self, interaction, confirmation_message, view)
                    if view is None:
                        await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                        return
                    choice = view.children[0].choice
                    if choice == 'Yes':
                        break
                    else:
                        continue

                country = data['data']['address']['data']['country']
                timezone = data['data']['timezone']

                try:
                    city = data['data']['address']['data']['city']
                except KeyError:
                    try:
                        city = data['data']['address']['data']['town']
                    except KeyError:
                        try:
                            city = data['data']['address']['data']['state']
                        except KeyError:
                            await interaction.followup.send("Error caused as your city could not be fetched properly. Please call the command again with to retry. If the error persists please use manual mode, or contact the developer.")
                            return
            else:
                await interaction.followup.send("(Please note that the bot cannot always determine whether the country and city you gave are valid. Please make sure that the country and city you gave are correct.)")
                country = await get_country(self, interaction)
                if country is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                
                city = await get_city(self, interaction)
                if city is None:    
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                
                if await location_valid(country, city) == False:
                    await interaction.followup.send("Invalid location. Please call the command again if you want to retry.")
                    return
                
                instance = timezone_dropdown()
                view = dropdownView(instance)
                message_str = "Please select your timezone (if you select 'More...' you cannot go back to the previous options, you have to wait for the interaction to time out):"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                timezone = view.children[0].timezone
    
            instance = school_dropdown()
            view = dropdownView(instance)
            message_str = "Please select your school of thought, this will be used for calculating the asr time:"
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            school = int(view.children[0].school)

            instance = midnightMode_dropdown()
            view = dropdownView(instance)
            message_str = "Please select your midnight mode:"
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            midnightMode = int(view.children[0].midnightMode)

            instance = method_dropdown()
            view = dropdownView(instance)
            message_str = "Please select the institute that will be used for calculating prayer times: "
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            method = int(view.children[0].method)

            view = prayerOptions_View()
            message_str = "Please select the prayers you want to be reminded of:"
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            selected_prayers = list(view.selected_prayers)
            
            instance = forbiddenTimes_dropdown()
            view = dropdownView(instance)
            message_str = "Would you like to be alerted about the forbidden times to pray voluntary prayers? (details for the forbidden times can be viewed using the command `/forbiddentimes` after you are done setting up your reminder)"
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            forbiddenTimesReminder = int(view.children[0].forbiddenTimesReminder)

            instance = hourFormat_dropdown()
            view = dropdownView(instance)
            message_str = "Please select the format you want the prayers starting and ending time to be displayed in:"
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            hourFormat = int(view.children[0].hourFormat)

            instance = remindEarly_dropdown()
            view = dropdownView(instance)
            message_str = "Please select whether you want your prayer reminder on time or 5 minutes early:"
            view = await get_info(self, interaction, message_str, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            remindEarly = int(view.children[0].remindEarly)
            
            timezone_object = pytz.timezone(timezone)
            date = datetime.now(timezone_object).strftime("%d-%m-%Y")
            selected_prayers = sort_prayers(selected_prayers)
            reminder_data = [user_id]
            prayer_timings, beforeDhuhr = await get_prayer_timings(country, city, date, school, midnightMode, method, selected_prayers, forbiddenTimesReminder)
            reminder_data += prayer_timings
            reminder_data += [country, city, timezone, date, school, midnightMode, method, hourFormat, remindEarly, beforeDhuhr]
            
            await insert_reminder_data(reminder_data)
            await interaction.followup.send("All done :ballot_box_with_check:")
            asyncio.create_task(process_user(self.client, user_id))
        except Exception as e:
            print(f"ERROR in setupreminder command: {e}")
        finally:
            if interaction.guild is None:
                users_list.remove(user_id)


    @app_commands.command(name='updatereminder', description="Update your prayer reminder information")
    @app_commands.choices(info_to_update=[
            discord.app_commands.Choice(name="Country/City/Timezone (Automatic Mode)", value='Country/City/Timezone (Automatic Mode)'),
            discord.app_commands.Choice(name="Country/City (Manual Mode)", value='Country/City (Manual Mode)'),
            discord.app_commands.Choice(name="Timezone", value='Timezone'),
            discord.app_commands.Choice(name="School Of Thought", value='School'),
            discord.app_commands.Choice(name="Midnight Mode", value="MidnightMode"),
            discord.app_commands.Choice(name="Institute", value="Method"),
            discord.app_commands.Choice(name="Selected Prayers", value='Selected Prayers'),
            discord.app_commands.Choice(name="Alerts for Forbidden Prayer Times", value='forbiddenTimesReminder'),
            discord.app_commands.Choice(name="Time Format", value="HourFormat"),
            discord.app_commands.Choice(name="Reminder Time", value="RemindEarly")
    ])
    async def updatereminder(self, interaction: discord.Interaction, info_to_update: discord.app_commands.Choice[str]):
        try:
            await interaction.response.defer()

            if interaction.guild != None:
                await interaction.followup.send("For privacy reasons, this command can only be used in DMs.")
                return
        
            user_id = interaction.user.id
            if user_id in users_list:
                await interaction.followup.send("You are already using a command. Wait for for the current command to timeout if you would like to this command.")
                return
            users_list.append(user_id)

            if await user_reminder_data_exists(user_id) == False:
                await interaction.followup.send("You do not have a reminder set up due to which you cannot use this command. To set up a reminder, use the `/setupreminder` command.")
                return

            info_to_update = info_to_update.value
            
            if info_to_update == "Country/City/Timezone (Automatic Mode)":
                while True:
                    message = "Please type your location, make sure the location is accurate for the most accurate prayer timings. E.g '16-2 Rosslyn Rd, Watford, UK'. Type 'cancel' to cancel:"
                    location = await get_location(self, interaction, message)
                    if location is None:
                        await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                        return
                    elif location == 'cancel':
                        await interaction.followup.send("Cancelled setup.")
                        return
                    
                    data = geo_adhan_lookup(location, 1, False)
                    if data['err'] == 'Error: Location not found':
                        await interaction.followup.send("Invalid location. (Try making your location more accurate or less accurate)")
                        continue
                    elif data['success'] is False:
                        await interaction.followup.send('Automatic mode is not working right now. Please use the command again and try manual mode')
                        return
                    
                    instance = location_confirmation_dropdown()
                    view = dropdownView(instance)
                    confirmation_message = f"**__Location Data:__**\n"
                    for key, value in data['data']['address']['data'].items():
                        confirmation_message += f"{key}: {value}\n"
                    confirmation_message += "\nIs this location data correct?"
                    view = await get_info(self, interaction, confirmation_message, view)
                    if view is None:
                        await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                        return
                    choice = view.children[0].choice
                    if choice == 'Yes':
                        break
                    else:
                        continue
                
                country = data['data']['address']['data']['country']
                timezone = data['data']['timezone']

                try:
                    city = data['data']['address']['data']['city']
                except KeyError:
                    try:
                        city = data['data']['address']['data']['town']
                    except KeyError:
                        try:
                            city = data['data']['address']['data']['state']
                        except KeyError:
                            await interaction.followup.send("Error caused as your city could not be fetched properly. Please call the command again with to retry. If the error persists please use manual mode, or contact the developer.")
                            return
                await update_reminder_data(user_id, "Country", country)
                await update_reminder_data(user_id, "City", city)
                await update_reminder_data(user_id, "Timezone", timezone)
            elif info_to_update == "Country/City (Manual Mode)":
                await interaction.followup.send("You will have to enter both your country *and* city again")
                await interaction.followup.send("(Please note that the bot cannot always determine whether the country and city you gave is valid. Please make sure that the country and city you gave are correct.)")
                country = await get_country(self, interaction)
                if country is None: 
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                
                city = await get_city(self, interaction)
                if city is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                
                if await location_valid(country, city) == False:
                    await interaction.followup.send("Invalid location. Please call the command again if you want to retry.")
                    return
                
                info_to_update = "Country"
                await update_reminder_data(user_id, info_to_update, country)
                info_to_update = "City"
                await update_reminder_data(user_id, info_to_update, city)
            elif info_to_update == "Timezone":
                instance = timezone_dropdown()
                view = dropdownView(instance)
                message_str = "Please select your timezone (if you select 'More...' you cannot go back to the previous options, you have to wait for the interaction to time out):"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                timezone = view.children[0].timezone
                await update_reminder_data(user_id, info_to_update, timezone)
            elif info_to_update == "School":
                instance = school_dropdown()
                view = dropdownView(instance)
                message_str = "Please select your school of thought, this will be used for calculating the asr time:"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                school = int(view.children[0].school)
                await update_reminder_data(user_id, info_to_update, school)
            elif info_to_update == "MidnightMode":
                instance = midnightMode_dropdown()
                view = dropdownView(instance)
                message_str = "Please select your midnight mode:"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                midnightMode = int(view.children[0].midnightMode)
                await update_reminder_data(user_id, info_to_update, midnightMode)
            elif info_to_update == "Method":
                instance = method_dropdown()
                view = dropdownView(instance)
                message_str = "Please select the institute that will be used for calculating prayer times: "
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                method = int(view.children[0].method)
                await update_reminder_data(user_id, info_to_update, method)
            elif info_to_update == "Selected Prayers":
                view = prayerOptions_View()
                message_str = "Please select the prayers you want to be reminded of:"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                selected_prayers = list(view.selected_prayers)
                selected_prayers = sort_prayers(selected_prayers)
                info = await get_prayer_timings_data(user_id)
                Country, City, Date, School, MidnightMode, Method = info[0], info[1], info[2], info[3], info[4], info[5]
                #In the below line, 'beforeDhuhr' is being received purely so the function doesnt raise an error. There is no involvement of the variable in this case otherwise
                prayer_timings, beforeDhuhr = await get_prayer_timings(Country, City, Date, School, MidnightMode, Method, selected_prayers, 0)
                await update_reminder_data(user_id, info_to_update, prayer_timings)
            elif info_to_update == "forbiddenTimesReminder":
                instance = forbiddenTimes_dropdown()
                view = dropdownView(instance)
                message_str = "Would you like to be alerted about the forbidden times to pray voluntary prayers? (details for the forbidden times can be viewed using the command `/forbiddentimes` after you are done updating your reminder settings)"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                forbiddenTimesReminder = int(view.children[0].forbiddenTimesReminder)
                if forbiddenTimesReminder == 0:
                    await update_reminder_data(user_id, 'BeforeDhuhr', None)
                    fajr = await get_reminder_info(user_id, 'Fajr')
                    if fajr is None:
                        await update_reminder_data(user_id, 'Sunrise', None)
                else:
                    info = await get_prayer_timings_data(user_id)
                    country, city, date, school, midnightMode, method = info[0], info[1], info[2], info[3], info[4], info[5]
                    url = f"http://api.aladhan.com/v1/timingsByCity/{date}?city={city}&country={country}&method={method}&school={school}&midnightMode={midnightMode}"
                    data = requests.get(url)
                    data = data.json()
                    Dhuhr = data['data']['timings']['Dhuhr']
                    Dhuhr = datetime.strptime(Dhuhr, "%H:%M")
                    beforeDhuhr = Dhuhr - dt_module.timedelta(minutes=25)
                    beforeDhuhr = beforeDhuhr.strftime("%H:%M")
                    await update_reminder_data(user_id, 'BeforeDhuhr', beforeDhuhr)
                    fajr = await get_reminder_info(user_id, 'Fajr')
                    if fajr is None:
                        sunrise = data['data']['timings']['Sunrise']
                        await update_reminder_data(user_id, 'Sunrise', sunrise)     
            elif info_to_update == "HourFormat":
                instance = hourFormat_dropdown()
                view = dropdownView(instance)
                message_str = "Please select the format you want the prayers starting and ending time to be displayed in:"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                hourFormat = int(view.children[0].hourFormat)
                await update_reminder_data(user_id, info_to_update, hourFormat)
            elif info_to_update == "RemindEarly":
                instance = remindEarly_dropdown()
                view = dropdownView(instance)
                message_str = "Please select whether you want your prayer reminder on time or 5 minutes early:"
                view = await get_info(self, interaction, message_str, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                remindEarly = int(view.children[0].remindEarly)
                await update_reminder_data(user_id, info_to_update, remindEarly)

            if info_to_update != "HourFormat" and info_to_update != "Selected Prayers" and info_to_update != "RemindEarly" and info_to_update != "forbiddenTimesReminder":
                selected_prayers = await get_db_prayers(user_id)
                info = await get_prayer_timings_data(user_id)
                Country, City, Date, School, MidnightMode, Method = info[0], info[1], info[2], info[3], info[4], info[5]
                beforeDhuhr = await get_reminder_info(user_id, "BeforeDhuhr")
                if beforeDhuhr != None:
                    forbiddenTimesReminder = 1
                else:
                    forbiddenTimesReminder = 0
                prayer_timings, beforeDhuhr = await get_prayer_timings(Country, City, Date, School, MidnightMode, Method, selected_prayers, forbiddenTimesReminder)
                await update_reminder_data(user_id, "Selected Prayers", prayer_timings)
                if beforeDhuhr != None:
                    await update_reminder_data(user_id, "BeforeDhuhr", beforeDhuhr)
            await interaction.followup.send("Information updated :ballot_box_with_check:")
        except Exception as e:
            print(f"\n\nERROR IN updatereminder COMMAND: {e}\n\n")
        finally:
            if interaction.guild is None:
                users_list.remove(user_id)


    @app_commands.command(name='disablereminder', description="Disable your prayer reminder if you have it set up")
    async def disablereminder(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user_id = interaction.user.id
            if await user_reminder_data_exists(user_id) == False:
                await interaction.followup.send("You do not have a reminder set up. To set up a reminder, use the `/setupreminder` command.")
                return
            await delete_reminder_data(user_id)
            await interaction.followup.send("Prayer Reminder has been disabled and your data has been deleted :wastebasket:")
        except Exception as e:
            print(f"\n\nERROR IN disablereminder COMMAND: {e}\n\n")


    @app_commands.command(name='prayertimings', description='Get the prayer timings for today (only works if you have a prayer reminder set up)')
    async def prayertimings(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user_id = interaction.user.id
            if not await user_reminder_data_exists(user_id):
                await interaction.followup.send("You do not have a reminder set up due to which you cannot use this command. To set up a reminder, use the `/setupreminder` command.")
                return
            info = await get_prayer_timings_data(user_id)
            country, city, date, school, midnightMode, method = info[0], info[1], info[2], info[3], info[4], info[5]
            hourFormat = await get_reminder_info(user_id, 'HourFormat')
            data = requests.get(f"http://api.aladhan.com/v1/timingsByCity/{date}?city={city}&country={country}&method={method}&school={school}&midnightMode={midnightMode}")
            data = data.json()

            if hourFormat == 1:
                format_arg = '%I:%M %p'
            else:
                format_arg = '%H:%M'

            timezone = await get_reminder_info(user_id, 'Timezone')
            stored_date = await get_reminder_info(user_id, "Date")

            Fajr_start = datetime.strptime(f"{stored_date} {data['data']['timings']['Fajr']}", '%d-%m-%Y %H:%M')
            Dhuhr_start = datetime.strptime(f"{stored_date} {data['data']['timings']['Dhuhr']}", '%d-%m-%Y %H:%M')
            Asr_start = datetime.strptime(f"{stored_date} {data['data']['timings']['Asr']}", '%d-%m-%Y %H:%M')
            Maghrib_start = datetime.strptime(f"{stored_date} {data['data']['timings']['Maghrib']}", '%d-%m-%Y %H:%M')
            Isha_start = datetime.strptime(f"{stored_date} {data['data']['timings']['Isha']}", '%d-%m-%Y %H:%M')

            prayer_times = [Fajr_start, Dhuhr_start, Asr_start, Maghrib_start, Isha_start]
            time_till_next_prayer = get_time_till_next_prayer(prayer_times, timezone)

            Fajr_start = Fajr_start.strftime(format_arg)
            Dhuhr_start = Dhuhr_start.strftime(format_arg)
            Asr_start = Asr_start.strftime(format_arg)
            Maghrib_start = Maghrib_start.strftime(format_arg)
            Isha_start = Isha_start.strftime(format_arg)

            Fajr_end = datetime.strptime(data['data']['timings']['Sunrise'], "%H:%M").strftime(format_arg)
            Dhuhr_end = Asr_start
            Maghrib_end = Isha_start
            Isha_end = datetime.strptime(data['data']['timings']['Midnight'], "%H:%M").strftime(format_arg)

            if school == 1:
                Asr_end = Maghrib_start
            else:
                data = requests.get(f"http://api.aladhan.com/v1/timingsByCity/{date}?city={city}&country={country}&method={method}&school=1&midnightMode={midnightMode}")
                data = data.json()
                Asr_end = datetime.strptime(data['data']['timings']['Asr'], "%H:%M").strftime(format_arg)
            
            dayOfTheWeek = datetime.now(pytz.timezone(timezone)).strftime("%A")
            dhuhrOrJummah = ""
            if dayOfTheWeek != 'Friday':
                dhuhrOrJummah = 'Dhuhr'
            else:
                dhuhrOrJummah = 'Jummah'

            embed = Embed(title='Prayer Timings', color=0xff8000)
            embed.add_field(name='Fajr', value=Fajr_start + ' - ' + Fajr_end, inline=False)
            embed.add_field(name=dhuhrOrJummah, value=Dhuhr_start + ' - ' + Dhuhr_end, inline=False)
            embed.add_field(name='Asr', value=Asr_start + ' - ' + Asr_end, inline=False)
            embed.add_field(name='Maghrib', value=Maghrib_start + ' - ' + Maghrib_end, inline=False)
            embed.add_field(name='Isha', value=Isha_start + ' - ' + Isha_end, inline=False)
            embed.set_footer(text=f'Time till next prayer: {time_till_next_prayer}\nRequested by: {interaction.user.name}')
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"\n\nERROR IN prayertimings COMMAND: {e}\n\n")


    @app_commands.command(name='cancelnextreminder', description="Cancel the next prayer reminder if you have it set up")
    async def cancelnextreminder(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user_id = interaction.user.id
            if not await user_reminder_data_exists(user_id):
                await interaction.followup.send("You do not have a reminder set up due to which you cannot use this command. To set up a reminder, use the `/setupreminder` command.")
                return
            cancelReminder = await get_reminder_info(user_id, 'CancelReminder')
            if not cancelReminder:
                await update_reminder_data(user_id, 'CancelReminder', 1)
                await interaction.followup.send("Next reminder cancelled :wastebasket:")
            else:
                await interaction.followup.send("Next reminder is already cancelled.")
        except Exception as e:
            print(f"\n\nERROR IN cancelnextreminder COMMAND: {e}\n\n")
            

    @app_commands.command(name='restorenextreminder', description="Enable the next prayer reminder if you cancelled it")
    async def restorenextreminder(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user_id = interaction.user.id
            if not await user_reminder_data_exists(user_id):
                await interaction.followup.send("You do not have a reminder set up due to which you cannot use this command. To set up a reminder, use the `/setupreminder` command.")
                return
            cancelReminder = await get_reminder_info(user_id, 'CancelReminder')
            if cancelReminder is not None:
                await update_reminder_data(user_id, 'CancelReminder', None)
                await interaction.followup.send("Next reminder enabled :ballot_box_with_check:")
            else:
                await interaction.followup.send("Next reminder is already enabled.")
        except Exception as e:
            print(f"\n\nERROR IN restorenextreminder COMMAND: {e}\n\n")

async def setup(client):
    await client.add_cog(reminder_commands(client))