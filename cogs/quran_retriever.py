# Import required dependencies
import discord
from discord.ext import commands
from discord import Embed
from discord import app_commands
import requests
from shared_resources import surahs, num_verses_in_surah
import random


class quran_retriever(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name='quran', description='Retrieve a Quran verse')
    async def quran(self, interaction: discord.Interaction, chapter_number:int, verse_number:int):
        try:
            await interaction.response.defer()
            if int(chapter_number) > 114 or int(chapter_number) < 1:
                    await interaction.followup.send("Surah number must be between 1 and 114.")
                    return 
            data = requests.get('https://quranenc.com/api/v1/translation/aya/english_saheeh/' + str(chapter_number) + '/' + str(verse_number))
            data = data.json()
            if int(verse_number) > 286 or int(verse_number) < 1 or data == "":
                await interaction.followup.send("Invalid verse number.")
                return
            translation = data['result']['translation']

            embed = Embed(title="Quran English Translation", description=translation, color=0xff8000)
            embed.set_footer(text="Requested by " + interaction.user.name)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"\n\nERROR IN quran COMMAND: {e}\n\n")


    @app_commands.command(name='quranarabic', description='Retrieve a Quran verse in Arabic')
    async def quranarabic(self, interaction: discord.Interaction, chapter_number:int, verse_number:int):
        try:
            await interaction.response.defer()
            if int(chapter_number) > 114 or int(chapter_number) < 1:
                await interaction.followup.send("Surah number must be between 1 and 114.")
                return 
            data = requests.get('https://quranenc.com/api/v1/translation/aya/english_saheeh/' + str(chapter_number) + '/' + str(verse_number))
            data = data.json()
            if int(verse_number) > 286 or int(verse_number) < 1 or data == "":
                await interaction.followup.send("Invalid verse number.")
                return
            arabic_text = data['result']['arabic_text']
            embed = Embed(title="Quran Arabic", description=arabic_text, color=0xff8000)
            embed.set_footer(text="Requested by " + interaction.user.name)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"\n\nERROR IN quranarabic COMMAND: {e}\n\n")


    @app_commands.command(name='quranfootnotes', description='Retrieve a Quran verse with footnotes')
    async def quranfootnotes(self, interaction: discord.Interaction, chapter_number:int, verse_number:int):
        try:
            await interaction.response.defer()
            if int(chapter_number) > 114 or int(chapter_number) < 1:
                await interaction.followup.send("Surah number must be between 1 and 114.")
                return 
            data = requests.get('https://quranenc.com/api/v1/translation/aya/english_saheeh/' + str(chapter_number) + '/' + str(verse_number))
            data = data.json()
            if int(verse_number) > 286 or int(verse_number) < 1 or data == "":
                await interaction.response.send("Invalid verse number.")
                return
            translation = data['result']['translation']
            footnotes = data['result']['footnotes']
            if footnotes == "":
                footnotes = "None"

            if len(translation) > 1024 or len(footnotes) > 1024:
                await interaction.followup.send(f"**__Quran English Translation with Footnotes:__**\n\n**Translaion:**\n{translation}\n\n**Footnotes:**\n{footnotes}")
            else:
                embed = Embed(title="Quran Enlgish Translation with Footnotes", color=0xff8000)
                embed.add_field(name="Translation", value=translation, inline=False)
                embed.add_field(name="Footnotes", value=footnotes, inline=False)
                embed.set_footer(text="Requested by " + interaction.user.name)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"\n\nERROR IN quranfootnotes COMMAND: {e}\n\n")


    @app_commands.command(name='quranrandom', description='Retrieve a random Quran verse')
    @app_commands.describe(language='Language to get the verse in')
    @app_commands.choices(language=[
        discord.app_commands.Choice(name='English', value=1),
        discord.app_commands.Choice(name='Arabic', value=2)
        ])
    async def quranrandom(self, interaction: discord.Interaction, language:discord.app_commands.Choice[int]):
        try:
            await interaction.response.defer()
            if language.name == 'English':
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
            embed.set_footer(text="Requested by " + interaction.user.name)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"\n\nERROR IN quranrandom COMMAND: {e}\n\n")

    
    @app_commands.command(name='listsurahs', description='View a list of all Surahs in the Quran')
    async def listsurahs(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            surahs_str = ""
            for key, value in surahs.items():
                surahs_str += f"{key}: {value}\n"
            embed = Embed(title="List of Surahs", description=surahs_str, color=0xff8000)
            embed.set_footer(text="Requested by " + interaction.user.name)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"\n\nERROR IN listsurahs COMMAND: {e}\n\n")

async def setup(client):
   await client.add_cog(quran_retriever(client))