# Import required dependencies
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from shared_resources import books
import requests
import random
        
book_message = "Please select a book:"

# This command is needed as discord has a word limit of 2000 characters
async def divide_message(message):
    messages_list = []
    for i in range(0, len(message), 2000):
        messages_list.append(message[i:i+2000])
    return messages_list

async def get_hadith_num(self, ctx):
    await ctx.send("Please type the hadith number you want to get:")
    try:
        hadith_num_message = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
    except asyncio.TimeoutError:
        return None
    hadith_num = hadith_num_message.content
    return hadith_num

class book_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Sahih Bukhari', value='sahih-bukhari'),
            discord.SelectOption(label='Sahih Muslim', value='sahih-muslim'),
            discord.SelectOption(label="Jami' Al-Tirmidhi", value="al-tirmidhi"),
            discord.SelectOption(label="Sunan Abu Dawood", value="abu-dawood"),
            discord.SelectOption(label="Sunan Ibn-e-Majah", value="ibn-e-majah"),
            discord.SelectOption(label="Sunan An-Nasa`i", value="sunan-nasai"),
        ]
        super().__init__(placeholder='Hadith Books', min_values=1, max_values=1, options=options)
        self.selected_book = None
    async def callback(self, interaction:discord.Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.selected_book = self.values[0]
        return self.view.stop()
        
class hadith_retriever(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @app_commands.command(name='hadith', description='View a specific Hadith in English')
    @app_commands.choices(book=[
        discord.app_commands.Choice(name='Sahih Bukhari', value='sahih-bukhari'),
        discord.app_commands.Choice(name='Sahih Muslim', value='sahih-muslim'),
        discord.app_commands.Choice(name="Jami' Al-Tirmidhi", value="al-tirmidhi"),
        discord.app_commands.Choice(name="Sunan Abu Dawood", value="abu-dawood"),
        discord.app_commands.Choice(name="Sunan Ibn-e-Majah", value="ibn-e-majah"),
        discord.app_commands.Choice(name="Sunan An-Nasa'i", value="sunan-nasai"),
    ])
    async def hadith(self, interaction: discord.Interaction, book:discord.app_commands.Choice[str], hadith_number:int):
        try:
            max_hadith_num = books[book.value]
            if hadith_number < 1 or hadith_number > max_hadith_num:
                await interaction.response.send_message(f"The hadith number for this book must be between 1 and {max_hadith_num}. Please call the command again if you want to retry")
                return
            
            params = {
                'book': book.value,
                'hadithNumber':hadith_number,
            }

            data = requests.get('https://www.hadithapi.com/api/hadiths/?apiKey=$2y$10$xxSmbj6QTXNoYCVeEN8MyShWyIx2suugbtgOQaATomCeHEmNxKiK', params=params)
            data = data.json()
        
            chapter = data['hadiths']['data'][0]['chapter']['chapterEnglish']
            narrator = data['hadiths']['data'][0]['englishNarrator']
            heading = data['hadiths']['data'][0]['headingEnglish']
            hadith = data['hadiths']['data'][0]['hadithEnglish']
            if hadith == '':
                await interaction.response.send_message('Hadith Unavailible.')
                return
            status = data['hadiths']['data'][0]['status']
            status = status[0].upper() + status[1:]
            hadith = hadith.replace("`", "")

            if len(hadith) <= 1024:
                if narrator is not None and narrator != "":
                    hadith = f"{narrator} {hadith}"
                if chapter == "":
                    chapter = "Unavailible"
                if status == "":
                    status = "Unavailible"
                embed = discord.Embed(title='Hadith in English', color=0xff8000)
                embed.add_field(name='Chapter', value=chapter, inline=False)
                if heading is not None and not heading == "":
                    embed.add_field(name='Heading', value=heading, inline=False)
                embed.add_field(name='Hadith', value=hadith, inline=False)
                embed.add_field(name='Grade', value=status, inline=False)
                embed.set_footer(text="Requested by " + interaction.user.name)
                await interaction.response.send_message(embed=embed)
            else:
                if chapter:
                    chapter_str = f"**Chapter:** {chapter}\n\n"
                else:
                    chapter_str = ""

                if narrator:
                    narrtor_str = f"{narrator} "
                else:
                    narrtor_str = ""

                if heading:
                    heading_str = f"**__{heading}:__**\n\n"
                else:   
                    heading_str = ""
                hadith_str = f"{chapter_str}{heading_str}{narrtor_str}{hadith}\n\n**Grade:** {status}"
                if len(hadith_str) > 2000:
                    messages_list = await divide_message(hadith_str)
                    for chunk in messages_list:
                        await interaction.response.send_message(chunk)
                else:
                    await interaction.response.send_message(hadith_str)
        except Exception as e:
            print(f'\n\nERROR IN hadith COMMAND: {e}\n\n')

    @app_commands.command(name='haditharabic', description='View a specific Hadith in Arabic')
    @app_commands.choices(book=[
        discord.app_commands.Choice(name='Sahih Bukhari', value='sahih-bukhari'),
        discord.app_commands.Choice(name='Sahih Muslim', value='sahih-muslim'),
        discord.app_commands.Choice(name="Jami' Al-Tirmidhi", value="al-tirmidhi"),
        discord.app_commands.Choice(name="Sunan Abu Dawood", value="abu-dawood"),
        discord.app_commands.Choice(name="Sunan Ibn-e-Majah", value="ibn-e-majah"),
        discord.app_commands.Choice(name="Sunan An-Nasa'i", value="sunan-nasai"),
    ])
    async def haditharabic(self, interaction: discord.Interaction, book:discord.app_commands.Choice[str], hadith_number:int):
        try:
            max_hadith_num = books[book.value]
            if hadith_number < 1 or hadith_number > max_hadith_num:
                await interaction.response.send_message(f"The hadith number for this book must be between 1 and {max_hadith_num}. Please call the command again if you want to retry")
                return
            
            params = {
                'book': book.value,
                'hadithNumber':hadith_number,
            }

            data = requests.get('https://www.hadithapi.com/api/hadiths/?apiKey=$2y$10$xxSmbj6QTXNoYCVeEN8MyShWyIx2suugbtgOQaATomCeHEmNxKiK', params=params)
            data = data.json()

            chapter = data['hadiths']['data'][0]['chapter']['chapterArabic']
            heading = data['hadiths']['data'][0]['headingArabic']
            hadith = data['hadiths']['data'][0]['hadithArabic']
            if hadith == '':
                await interaction.response.send_message('Hadith Unavailible.')
                return
            status = data['hadiths']['data'][0]['status']
            status = status[0].upper() + status[1:]
            hadith = hadith.replace("`", "")
            
            if len(hadith) <= 1024:
                if chapter == "":
                    chapter = "Unavailible"
                if status == "":
                    status = "Unavailible"
                embed = discord.Embed(title='Hadith in Arabic', color=0xff8000)
                embed.add_field(name='Chapter', value=chapter, inline=False)
                if heading is not None and not heading == "":
                    embed.add_field(name='Heading', value=heading, inline=False)
                embed.add_field(name='Hadith', value=hadith, inline=False)
                embed.add_field(name='Grade', value=status, inline=False)
                embed.set_footer(text="Requested by " + interaction.user.name)
                await interaction.response.send_message(embed=embed)
            else:
                if chapter:
                    chapter_str = f"**Chapter:** {chapter}\n\n"
                else:
                    chapter_str = ""

                if heading:
                    heading_str = f"**__{heading}:__**\n\n"
                else:
                    heading_str = ""
                hadith_str = f"{chapter_str}{heading_str}{hadith}\n\n**Grade:** {status}"
                if len(hadith_str) > 2000:
                    messages_list = await divide_message(hadith_str)
                    for chunk in messages_list:
                        await interaction.response.send_message(chunk)
                else:
                    await interaction.response.send_message(hadith_str)
        except Exception as e:
            print(f'\n\nERROR IN haditharabic COMMAND: {e}\n\n')


    @app_commands.command(name='hadithurdu', description='View a specific Hadith in Urdu')
    @app_commands.choices(book=[
        discord.app_commands.Choice(name='Sahih Bukhari', value='sahih-bukhari'),
        discord.app_commands.Choice(name='Sahih Muslim', value='sahih-muslim'),
        discord.app_commands.Choice(name="Jami' Al-Tirmidhi", value="al-tirmidhi"),
        discord.app_commands.Choice(name="Sunan Abu Dawood", value="abu-dawood"),
        discord.app_commands.Choice(name="Sunan Ibn-e-Majah", value="ibn-e-majah"),
        discord.app_commands.Choice(name="Sunan An-Nasa'i", value="sunan-nasai"),
    ])
    async def hadithurdu(self, interaction: discord.Interaction, book:discord.app_commands.Choice[str], hadith_number:int):
        try:
            max_hadith_num = books[book.value]
            if hadith_number < 1 or hadith_number > max_hadith_num:
                await interaction.response.send_message(f"The hadith number for this book must be between 1 and {max_hadith_num}. Please call the command again if you want to retry")
                return
            
            params = {
                'book': book.value,
                'hadithNumber':hadith_number,
            }

            data = requests.get('https://www.hadithapi.com/api/hadiths/?apiKey=$2y$10$xxSmbj6QTXNoYCVeEN8MyShWyIx2suugbtgOQaATomCeHEmNxKiK', params=params)
            data = data.json()

            chapter = data['hadiths']['data'][0]['chapter']['chapterUrdu']
            narrator = data['hadiths']['data'][0]['urduNarrator']
            heading = data['hadiths']['data'][0]['headingUrdu']
            hadith = data['hadiths']['data'][0]['hadithUrdu']
            if hadith == '':
                await interaction.response.send_message('Hadith Unavailible.')
                return
            status = data['hadiths']['data'][0]['status']
            status = status[0].upper() + status[1:]
            hadith = hadith.replace("`", "")

            if len(hadith) <= 1024:
                if narrator is not None and narrator != "":
                    hadith = f"{narrator} {hadith}"
                if chapter == "":
                    chapter = "Unavailible"
                if status == "":
                    status = "Unavailible"
                embed = discord.Embed(title='Hadith in Urdu', color=0xff8000)
                embed.add_field(name='Chapter', value=chapter, inline=False)
                if heading is not None and not heading == "":
                    embed.add_field(name='Heading', value=heading, inline=False)
                embed.add_field(name='Hadith', value=hadith, inline=False)
                embed.add_field(name='Grade', value=status, inline=False)
                embed.set_footer(text="Requested by " + interaction.user.name)
                await interaction.response.send_message(embed=embed)
            else:
                if chapter:
                    chapter_str = f"**Chapter:** {chapter}\n\n"
                else:
                    chapter_str = ""

                if narrator:
                    narrtor_str = f"{narrator} "
                else:
                    narrtor_str = ""

                if heading:
                    heading_str = f"**__{heading}:__**\n\n"
                else:
                    heading_str = ""
                hadith_str = f"{chapter_str}{heading_str}{narrtor_str}{hadith}\n\n**Grade:** {status}"
                if len(hadith_str) > 2000:
                    messages_list = await divide_message(hadith_str)
                    for chunk in messages_list:
                        await interaction.response.send_message(chunk)
                else:
                    await interaction.response.send_message(hadith_str)
        except Exception as e:
            print(f'\n\nERROR IN hadithurdu COMMAND: {e}\n\n')
    
    @app_commands.command(name='hadithrandom', description='View a random Hadith in your chosen language')
    @app_commands.choices(language=[
        discord.app_commands.Choice(name='English', value='english'),
        discord.app_commands.Choice(name='Arabic', value='arabic'),
        discord.app_commands.Choice(name='Urdu', value='urdu'),
    ])
    async def hadithrandom(self, interaction: discord.Interaction, language: discord.app_commands.Choice[str]):
        try:
            bookSlugs = ['sahih-bukhari', 'sahih-muslim', 'al-tirmidhi', 'abu-dawood', 'ibn-e-majah', 'sunan-nasai']
            while True:
                selected_book = random.choice(bookSlugs)
                hadith_number = random.randint(1, books[selected_book])

                params = {
                    'book': selected_book,
                    'hadithNumber':hadith_number,
                }

                data = requests.get('https://www.hadithapi.com/api/hadiths/?apiKey=$2y$10$xxSmbj6QTXNoYCVeEN8MyShWyIx2suugbtgOQaATomCeHEmNxKiK', params=params)
                data = data.json()

                if language.value != 'arabic':
                    narrator = data['hadiths']['data'][0][language.value + 'Narrator']
                else:
                    narrator = ""

                language = language.value[0].upper() + language.value[1:]
                book_name = data['hadiths']['data'][0]['book']['bookName']
                chapter = data['hadiths']['data'][0]['chapter']['chapter' + language]
                heading = data['hadiths']['data'][0]['heading' + language]
                hadith = data['hadiths']['data'][0]['hadith' + language]
                if hadith == '':
                    continue
                status = data['hadiths']['data'][0]['status']
                status = data['hadiths']['data'][0]['status']
                status = status[0].upper() + status[1:]
                hadith = hadith.replace("`", "")

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
                    embed.add_field(name='Hadith Number', value=hadith_number, inline=False)
                    embed.set_footer(text="Requested by " + interaction.user.name)
                    await interaction.response.send_message(embed=embed)
                    return
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

                    reference_str = f"**Hadith Number:** {hadith_number}"
                    hadith_str = f"**Book: **{book_name}\n\n{chapter_str}{heading_str}{narrator_str}{hadith}\n\n**Grade:** {status}\n\n{reference_str}"
                    if len(hadith_str) > 2000:
                        messages_list = await divide_message(hadith_str)
                        for chunk in messages_list:
                            await interaction.response.send_message(chunk)
                            return
                    else:
                        await interaction.response.send_message(hadith_str)
                        return
        except Exception as e:
            print(f'\n\nERROR IN hadithrandom COMMAND: {e}\n\n')

async def setup(client):
    await client.add_cog(hadith_retriever(client))