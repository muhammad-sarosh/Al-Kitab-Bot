# Import required dependencies
import discord
from discord.ext import commands
from discord import app_commands
from discord import Interaction
from reminder_helper import get_info, timezone_dropdown, dropdownView, geo_adhan_lookup, get_location, location_confirmation_dropdown
from db_operations import insert_daily_data, get_daily_data, update_daily_data, delete_daily_data
from datetime import datetime
import pytz
from daily_hadith_background_tasks import process_user
import asyncio

users_list = []

class time_to_send_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='0:00'),
            discord.SelectOption(label='1:00'),
            discord.SelectOption(label='2:00'),
            discord.SelectOption(label='3:00'),
            discord.SelectOption(label='4:00'),
            discord.SelectOption(label='5:00'),
            discord.SelectOption(label='6:00'),
            discord.SelectOption(label='7:00'),
            discord.SelectOption(label='8:00'),
            discord.SelectOption(label='9:00'),
            discord.SelectOption(label='10:00'),
            discord.SelectOption(label='11:00'),
            discord.SelectOption(label='12:00'),
            discord.SelectOption(label='13:00'),
            discord.SelectOption(label='14:00'),
            discord.SelectOption(label='15:00'),
            discord.SelectOption(label='16:00'),
            discord.SelectOption(label='17:00'),
            discord.SelectOption(label='18:00'),
            discord.SelectOption(label='19:00'),
            discord.SelectOption(label='20:00'),
            discord.SelectOption(label='21:00'),
            discord.SelectOption(label='22:00'),
            discord.SelectOption(label='23:00')
        ]
        self.time_to_send = None
        super().__init__(placeholder='Time', min_values=1, max_values=1, options=options)
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.time_to_send = self.values[0]
        return self.view.stop()
    
class hadith_language_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='English', value='english'),
            discord.SelectOption(label='Arabic', value='arabic'),
            discord.SelectOption(label='Urdu', value='urdu')
        ]
        self.language = None
        super().__init__(placeholder='Languages', min_values=1, max_values=1, options=options)
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.language = self.values[0]
        return self.view.stop()
    
class timezone_mode_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Automatic'),
            discord.SelectOption(label='Manual')
        ]
        self.mode = None
        super().__init__(placeholder='Modes', min_values=1, max_values=1, options=options)
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.mode = self.values[0]
        return self.view.stop()

class daily_hadith_commmands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='setupdailyhadith', description='Have the bot send you a random hadith in your DMs everyday')
    async def setupdailyhadith(self, interaction: discord.Interaction):
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

            if await get_daily_data('DailyHadithData', user_id, 'HadithUserID') is not None:
                await interaction.followup.send("You already have the daily hadith set up. If you would like to update any info use the `/updatedailyhadith` command, or if you would like to set up the whole thing again use the `/disabledailyhadith` command and *then* the `/setupdailyhadith` commannd.")
                return
            
            instance = time_to_send_dropdown()
            view = dropdownView(instance)
            time_message = "Please select the time at which you want me to send the hadith to you (Note that you might not get the hadith at this *exact* time, just *around* this time):"
            view = await get_info(self, interaction, time_message, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            time_to_send = view.children[0].time_to_send

            instance = timezone_mode_dropdown()
            view = dropdownView(instance)
            mode_message = "Would you like to enter your timezone manually, or enter your rough location and have me determine your timezone automatically?"
            view = await get_info(self, interaction, mode_message, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            mode = view.children[0].mode
            
            if mode == 'Automatic':
                while True:
                    message = "Please enter your rough location. Type 'cancel' to cancel the setup:"
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
                    
                    timezone = data['data']['timezone']

                    instance = location_confirmation_dropdown()
                    view = dropdownView(instance)
                    confirmation_message = f"Is this your timezone:\n**{timezone}**"
                    view = await get_info(self, interaction, confirmation_message, view)
                    if view is None:
                        await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                        return
                    choice = view.children[0].choice
                    if choice == 'Yes':
                        break
                    else:
                        continue
            else:
                instance = timezone_dropdown()
                view = dropdownView(instance)
                timezone_message = "Please select your timezone (if you select 'More...' you cannot go back to the previous options, you have to wait for the interaction to time out):"
                view = await get_info(self, interaction, timezone_message, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                timezone = view.children[0].timezone

            instance = hadith_language_dropdown()
            view = dropdownView(instance)
            language_message = "Please select the language you want to recieve the hadith in:"
            view = await get_info(self, interaction, language_message, view)
            if view is None:
                await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                return
            language = view.children[0].language

            date = datetime.now(pytz.timezone(timezone)).date()

            await insert_daily_data('DailyHadithData', user_id, timezone, time_to_send, date, language)
            
            await interaction.followup.send('All done :ballot_box_with_check:')

            asyncio.create_task(process_user(self.client, user_id))
        except Exception as e:
            print(f"\n\nERROR IN setupdailyhadith COMMAND: {e}\n\n")
        finally:
            if interaction.guild is None:
                users_list.remove(user_id)


    @app_commands.command(name='updatedailyhadith', description='Update your daily hadith information')
    @app_commands.choices(info_to_update = [
            discord.app_commands.Choice(name='Timezone (Automatic Mode)', value='timezone_automatic'),
            discord.app_commands.Choice(name='Timezone (Manual Mode)', value='timezone_manual'),
            discord.app_commands.Choice(name='Time at which you recieve the hadith', value='time_to_send'),
            discord.app_commands.Choice(name='Hadith Language', value='language')
        ])
    async def updatedailyhadith(self, interaction: discord.Interaction, info_to_update:discord.app_commands.Choice[str]):
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
            if await get_daily_data('DailyHadithData', user_id, 'HadithUserID') is None:
                await interaction.followup.send("You do not have daily hadith set up. To set up daily hadith, use the `/setupdailyhadith` command.")
                return

            choice = info_to_update.value
            
            if choice == 'timezone_automatic':
                while True:
                    message = "Please enter your rough location. Type 'cancel' to cancel the setup:"
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
                    
                    timezone = data['data']['timezone']
                    
                    instance = location_confirmation_dropdown()
                    view = dropdownView(instance)
                    confirmation_message = f"Is this your timezone:\n**{timezone}**"
                    view = await get_info(self, interaction, confirmation_message, view)
                    
                    if view is None:
                        await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                        return
                    choice = view.children[0].choice
                    if choice == 'Yes':
                        break
                    else:
                        continue
                await update_daily_data('DailyHadithData', user_id, 'Timezone', timezone)
            elif choice == 'timezone_manual':
                instance = timezone_dropdown()
                view = dropdownView(instance)
                timezone_message = "Please select your timezone (if you select 'More...' you cannot go back to the previous options, you have to wait for the interaction to time out):"
                view = await get_info(self, interaction, timezone_message, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                timezone = view.children[0].timezone
                await update_daily_data('DailyHadithData', user_id, 'Timezone', timezone)
            elif choice == 'time_to_send':
                instance = time_to_send_dropdown()
                view = dropdownView(instance)
                time_message = "Please select the time at which you want me to send the hadith to you (Note that you might not get the hadith at this *exact* time, just *around* this time):"
                view = await get_info(self, interaction, time_message, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                time_to_send = view.children[0].time_to_send
                await update_daily_data('DailyHadithData', user_id, 'TimeToSend', time_to_send)
            else:
                instance = hadith_language_dropdown()
                view = dropdownView(instance)
                language_message = "Please select the language you want to recieve the hadith in:"
                view = await get_info(self, interaction, language_message, view)
                if view is None:
                    await interaction.followup.send("The user took too long to respond. Please call the command again if you want to retry.")
                    return
                language = view.children[0].language

                await update_daily_data('DailyHadithData', user_id, 'Language', language)
            await interaction.followup.send('All done :ballot_box_with_check:')
        except Exception as e:
            print(f'\n\nERROR IN updatedailyhadith COMMAND: {e}\n\n')
        finally:
            users_list.remove(user_id)

    @app_commands.command(name='disabledailyhadith', description='Disables the daily hadith if you have it set up')
    async def disabledailyhadith(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user_id = interaction.user.id
            if await get_daily_data('DailyHadithData', user_id, 'HadithUserID') is None:
                await interaction.followup.send("You do not have daily hadith set up. To set up daily hadith, use the `/setupdailyhadith` command.")
                return
            await delete_daily_data('DailyHadithData', user_id)
            await interaction.followup.send("Daily Hadith has been disabled and your data has been deleted :wastebasket:")
        except Exception as e:
            print(f'\n\nERROR IN disabledailyhadith_slash COMMAND: {e}\n\n')

async def setup(client):
    await client.add_cog(daily_hadith_commmands(client))