import discord
from discord.ext import commands
from discord import app_commands
from discord import Embed
from shared_resources import names

class names_of_Allah(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='allnamesofallah', description='View a list of the 99 Names of Allah')
    async def allnamesofallah(self, interaction: discord.Interaction):
        message = ""
        name_num = 1
        for key, value in names.items():
            message += f"{name_num}: {key} - {value}\n"
            name_num += 1
        embed = Embed(title="Names of Allah", description=message, color=0xff8000)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='nameofallah', description='View a specific name of Allah')
    @app_commands.describe(name_number='Number of the name to get')
    async def nameofallah(self, interaction: discord.Interaction, name_number: int):
        try:
            if name_number < 1 or name_number> 99:
                await interaction.response.send_message("Number has to be between 1 and 99.")
                return
            i = 1
            for key, value in names.items():
                if i == name_number:
                    message = f"{i}: {key} - {value}"
                    break
                i += 1
            await interaction.response.send_message(message)
        except Exception as e:
            print(f"\n\nERROR IN nameofAllah COMMAND: {e}\n\n")

async def setup(client):
    await client.add_cog(names_of_Allah(client))
