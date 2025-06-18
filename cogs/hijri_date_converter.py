# Import required dependencies
import discord
from discord.ext import commands
from discord import app_commands
import requests

class hijri_date_converter(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @app_commands.command(name='hijriconverter', description='Converts Gregorian date to Hijri date')
    async def hijriconverter(self, interaction: discord.Interaction, day:int, month:int, year:int):
        try:
            if day < 1 or day > 31:
                await interaction.response.send_message('Invalid day. Please enter a day between 1 and 31.')
                return
            if month < 1 or month > 12:
                await interaction.response.send_message('Invalid month. Please enter a month between 1 and 12.')
                return
            if year < 622 or year > 9999:
                await interaction.response.send_message('Invalid year. Please enter a year between 622 and 9999.')
                return
            date = f'{day}-{month}-{year}'
            data = requests.get(f'http://api.aladhan.com/v1/gToH/{date}')
            data = data.json()
            hijri_date = data['data']['hijri']['date']
            hijri_month = data['data']['hijri']['month']['en']

            await interaction.response.send_message(f"**Hijri Date:** {hijri_date}\n**Hijri Month:** {hijri_month}")
        except Exception as e:
            print(f"\n\nERROR IN hijri COMMAND: {e}\n\n")
            
async def setup(client):
    await client.add_cog(hijri_date_converter(client))