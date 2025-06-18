# Import required dependencies
import discord
from discord.ext import commands
from discord import app_commands
from db_operations import get_tracker_info, get_tracker_prayer_markers, reset_tracker_markers, update_tracker_data, insert_tracker_user_id

prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

class prayer_tracker(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='prayed', description="Marks a prayer as 'prayed'")
    @app_commands.describe(prayer_to_mark='Name of the prayer to mark')
    @app_commands.choices(prayer_to_mark=[
        discord.app_commands.Choice(name='Fajr', value=1),
        discord.app_commands.Choice(name='Dhuhr', value=2),
        discord.app_commands.Choice(name='Asr', value=3),
        discord.app_commands.Choice(name='Maghrib', value=4),
        discord.app_commands.Choice(name='Isha', value=5)
    ])
    async def prayed(self, interaction: discord.Interaction, prayer_to_mark: discord.app_commands.Choice[int]):
        try:
            user_id = interaction.user.id
            prayer_to_mark = prayer_to_mark.name[0].upper() + prayer_to_mark.name[1:].lower()
            
            user_id_exists = await get_tracker_info(user_id, 'TrackerUserID')
            if not user_id_exists:
                await insert_tracker_user_id(user_id)
            
            prayer_status = await get_tracker_info(user_id, prayer_to_mark)
            prayer_status = prayer_status[0]
            if prayer_status == 1:
                await interaction.response.send_message("Prayer is already marked.")
                return

            await update_tracker_data(user_id, prayer_to_mark, 1)
            await interaction.response.send_message("Prayer marked successfully!")

            prayer_markers = await get_tracker_prayer_markers(user_id)
            marked_prayers = 0
            for prayer in prayer_markers:
                if prayer == 1:
                    marked_prayers += 1
            if marked_prayers == 5:
                await reset_tracker_markers(user_id)
                await interaction.response.send_message("You have marked all 5 prayers. Your tracker has been reset.")
                return
        except Exception as e:
            print(f"\n\nERROR IN prayed COMMAND: {e}\n\n")


    @app_commands.command(name='unprayed', description="Removes the 'prayed' marker from a prayer")
    @app_commands.describe(prayer_to_unmark='Name of the prayer to unmark')
    @app_commands.choices(prayer_to_unmark=[
        discord.app_commands.Choice(name='Fajr', value=1),
        discord.app_commands.Choice(name='Dhuhr', value=2),
        discord.app_commands.Choice(name='Asr', value=3),
        discord.app_commands.Choice(name='Maghrib', value=4),
        discord.app_commands.Choice(name='Isha', value=5)
    ])
    async def unprayed(self, interaction: discord.Interaction, prayer_to_unmark: discord.app_commands.Choice[int]):
        try:
            user_id = interaction.user.id
            prayer_to_unmark = prayer_to_unmark.name[0].upper() + prayer_to_unmark.name[1:].lower()
            
            user_id_exists = await get_tracker_info(user_id, 'TrackerUserID')
            if not user_id_exists:
                await insert_tracker_user_id(user_id)

            prayer_status = await get_tracker_info(user_id, prayer_to_unmark)
            prayer_status = prayer_status[0]
            if prayer_status is None:
                await interaction.response.send_message("Prayer is already unmarked.")
                return
            else:
                await update_tracker_data(user_id, prayer_to_unmark, None)
                await interaction.response.send_message("Prayer unmarked successfully!")
        except Exception as e:
            print(f"\n\nERROR IN unprayed COMMAND: {e}\n\n")


    @app_commands.command(name='viewtracker', description="View your prayer tracker")
    async def viewtracker(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            
            user_id_exists = await get_tracker_info(user_id, 'TrackerUserID')
            if not user_id_exists:
                await insert_tracker_user_id(user_id)

            prayer_markers = await get_tracker_prayer_markers(user_id)
            tracker_message = "**__Prayer Tracker:__**\n"
            for prayer_num in range(5):
                if prayer_markers[prayer_num] == 1:
                    tracker_message += f"**{prayers[prayer_num]}:** :white_check_mark:\n"
                else:
                    tracker_message += f"**{prayers[prayer_num]}:** :x:\n"
            await interaction.response.send_message(tracker_message)
        except Exception as e:
            print(f"\n\nERROR IN viewtracker COMMAND: {e}\n\n")


    @app_commands.command(name='bookmark', description="Save your Quran bookmark")
    async def bookmark(self, interaction: discord.Interaction, chapter_number:int, verse_number:int):
        try:
            user_id = interaction.user.id

            user_id_exists = await get_tracker_info(user_id, 'TrackerUserID')
            if not user_id_exists:
                await insert_tracker_user_id(user_id)
            
            bookmark = f"{chapter_number}:{verse_number}"

            await update_tracker_data(user_id, 'Bookmark', bookmark)
            await interaction.response.send_message("Bookmark saved :ballot_box_with_check:")
        except Exception as e:
            print(f"\n\nERROR IN bookmark COMMAND: {e}\n\n")


    @app_commands.command(name='viewbookmark', description="View your last bookmark")
    async def viewbookmark(self, interaction: discord.Interaction):
        try:
            user_id =interaction.user.id 
            stored_user_id = await get_tracker_info(user_id, 'TrackerUserID')
            if stored_user_id:
                bookmark = await get_tracker_info(user_id, 'Bookmark')
                if bookmark:
                    bookmark = bookmark[0]
                    await interaction.response.send_message(f"**Your Last Bookmark:** {bookmark}")
                else:
                    await interaction.response.send_message("No bookmarks have been saved. Use `/bookmark` command to save a bookmark.")
            else:
                await interaction.response.send_message("No bookmarks have been saved. Use `/bookmark` command to save a bookmark.")
        except Exception as e:
            print(f"\n\nERROR IN viewbookmark COMMAND: {e}\n\n")

async def setup(client):
    await client.add_cog(prayer_tracker(client))
