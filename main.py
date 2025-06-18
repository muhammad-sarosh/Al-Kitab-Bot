# Import required dependencies
import discord
from discord.ext import commands
import os
from reminder_background_tasks import reminder
from daily_hadith_background_tasks import daily_hadith_sender
from daily_verse_background_tasks import daily_verse_sender
from database_backup import database_backup
import asyncio
import aiosqlite

# Import the bot token
from sensitive_info import botToken

# Set intents and make instance of bot
intents = discord.Intents.all()
client = commands.Bot(command_prefix='-', intents=intents)
client.remove_command('help')

# For the function that is used to send a message to all registered users
db_name = 'UserData.db'
sticky_sushi_id = 546962882047508481
dry_vegetable_id = 788285654395519007

# Defining on ready function
@client.event
async def on_ready():
    await load_cogs()
    await client.change_presence(status=discord.Status.online, activity=discord.Game("/help"))
    print("The bot is now ready for use!\n------------------------------")
    asyncio.create_task(reminder(client)) # start the reminder task to keep checking for prayer times
    asyncio.create_task(daily_hadith_sender(client)) # start the daily_hadith_sender task to keep checking for the time to send daily hadith
    asyncio.create_task(daily_verse_sender(client)) # start the daily_verse_sender task to keep checking for the time to send daily verse
    asyncio.create_task(database_backup(client)) # start the database_backup task to keep a backup of the database
    
    # Sending a message to all users
    #message = "Assalamulaikum Warahmatullahi Wabarakatuh!\n\nThere were some issues with the server where Al Kitab Bot was being hosted which led to it being down for a few days. The Bot will work as usual now In shaa Allah\n\nIf you find experience any issues please contact the creator of the bot `sticky_sushi`. Jazaak Allah Khair for your patience"
    #await send_message(message)

@client.command(pass_context=True)
async def sync(ctx):
    if ctx.author.id == sticky_sushi_id:
        synced = await client.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands")

@client.command(pass_context=True)
async def clear(ctx):
    if ctx.author.id == sticky_sushi_id:
        client.tree.clear_commands(guild=None)
        await ctx.send("Cleared all commands")

@client.command(pass_context=True)
async def backup(ctx):
    if ctx.author.id == sticky_sushi_id or ctx.author.id == dry_vegetable_id:
        await ctx.send(file=discord.File(db_name))

# Get all the files that ends with .py in t he cogs folder   
initial_extensions = []
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        initial_extensions.append("cogs." + filename[:-3])

# Load all the cogs
async def load_cogs():
        for cog in initial_extensions:
            await client.load_extension(cog)

@client.tree.command(name='help', description='View a list of all commands')
async def help(interaction: discord.Interaction):
    reminder_commands = """`setupreminder:` Set up the prayer reminder which will DM you when your prayer time has arrived. This command can only be used in DMs.
    `updatereminder:` Update your prayer reminder information.
    `disablereminder:` Disable your prayer reminder and delete your data.
    `cancelnextreminder:` Cancel the next prayer reminder.
    `restorenextreminder:` Enable the next prayer reminder if you cancelled it.
    `prayertimings:` Get the current prayer timings according to your reminder settings.\n"""

    tracker_commands = """`bookmark:` Save your quran bookmark.
    `viewbookmark:` View your saved bookmark.
    `prayed:` Mark a prayer as prayed.
    `unprayed:` Unmark a prayer you've marked.
    `viewtracker:` See which prayers you've prayed and which prayers you haven't prayed.\n"""

    quran_commands = """`quran:` Retrieve a quran verse in English.
    `quranarabic:` Retrieve a quran verse in Arabic.
    `quranfootnotes:` Retrieve a quran verse in english with footnotes.
    `quranrandom:` Retrieve a random quran verse in your chosen language.
    `listsurahs:` View a list of all the surahs in the quran.\n"""

    daily_verse_commands = """`setupdailyverse:` Set up daily verse which will DM you a random verse from the Quran daily.
    `updatedailyverse:` Update your daily verse information.
    `disabledailyverse:` Disable the daily verse feature and delete your data.\n"""

    quran_player_commands = """`play:` Play a surah from the quran by number in voice chat. If this command is used when a surah is already playing, the next surah will be queued.
    `pause:` Pause the currently playing surah.
    `resume:` Resume the currently paused surah.
    `skip:` Skip the currently playing surah.
    `viewqueue:` View the current queue of surahs
    `clearqueue:` Clear the current queue of surahs
    `leave:` Disconnect the bot from the voice channel. If all users leave the voice channel, the bot will automatically disconnect.\n"""

    hadith_commands = """`hadith:` Retrieve a hadith from your chosen book in English . 
    `haditharabic:` Retrieve a hadith in from your chosen book Arabic .
    `hadithurdu:` Retrieve a hadith from your chosen book in Urdu.
    `hadithrandom:` Retrieve a random hadith from a random book in your chosen language.\n"""

    daily_hadith_commands = """`setupdailyhadith:` Set up daily hadith which will DM you a random hadith daily.
    `updatedailyhadith:` Update your daily hadith information.
    `disabledailyhadith:` Disable the daily hadith feature and delete your data.\n"""

    hijri_commands = """`hijriconverter:` View the hijri date at the specified Gregorian date."""

    names_of_Allah_commands = """`allnamesofllah`: View a list of the 99 names of Allah.
    `nameofallah`: View a specific name of Allah by number.\n"""

    forbiddentimes_commands = """`forbiddentimes:` There are times in the day when you are not allowed
    to pray voluntary prayers. This command can be used to view details regarding this matter.\n"""    

    embed = discord.Embed(title="List of commands", color=0xff8000)
    embed.add_field(name='Reminder Commands', value=reminder_commands, inline=False)
    embed.add_field(name='Prayer Tracker and Bookmark Commands', value=tracker_commands, inline=False)
    embed.add_field(name='Quran Commands', value=quran_commands, inline=False)
    embed.add_field(name='Quran Player Commands', value=quran_player_commands, inline=False)
    embed.add_field(name='Daily Verse Commands', value=daily_verse_commands, inline=False)
    embed.add_field(name='Hadith Commands', value=hadith_commands, inline=False)
    embed.add_field(name='Daily Hadith Commands', value=daily_hadith_commands, inline=False)
    embed.add_field(name='Date Converter Commands', value=hijri_commands, inline=False)
    embed.add_field(name="Names of Allah Commands", value=names_of_Allah_commands, inline=False)
    embed.add_field(name="Forbidden Times Commands", value=forbiddentimes_commands, inline=False)
    embed.set_footer(text="Requested by " + interaction.user.name)
    await interaction.response.send_message(embed=embed)

@client.tree.command(name='forbiddentimes', description='View details regarding forbidden times to pray voluntary prayers.')
async def forbiddentimes(interaction: discord.Interaction):
    await interaction.response.defer()
    first_message = """**__Detail Regarding Forbidden Times to Pray:__**
Allah has given us set times during which we must perform prayers. However there are certain times in the day during which performing voluntary prayers isnt allowed.

The majority of scholars say that you must pray the qadha of the prayers you missed, even during the forbidden times. 

Other than that there are the Sunan Ar Rawatib, voluntary parts of a prayer that the prophet pbuh would almost never miss. A lot of scholars are of the view that if you miss these due to a valid excuse, then you can make them up i.e pray qadha. In the case that you follow this opinion, the scholars differed regarding whether it is allowed to make them up at the forbidden times. Famously Imam Shafi' and Imam Ibn Taymiyah (may Allah have mercy on them) were of the view that these prayers should be made up even in the forbidden times.

Any prayer other than these that is not fardh and neither is it part of the sunan ar rawatib, it cannot be prayed in the forbidden times to pray.

There are 3 forbidden times to pray during the day. Lets first look at a brief description then go into a little more detail for each one:
1: When the time for fajr begins till approximately 15 mins after fajr
2: From approximately 20 mins before dhuhr till when dhuhr starts
3: From when you have prayed the fardh of Asr till the start of maghrib

Now lets go into detail:
1: There are 2 opinions regarding the forbidden time of fajr. 
- The hanbalis say that one should not offer voluntary prayers from the adhan of fajr until 15 mins after fajr, except the sunnah of fajr. 

- The Shafis say that one should not offer voluntary prayers from when they've prayed the fardh of fajr till 15 mins after fajr. 

If you want to play it safe you should follow the first opinion. Regardless, both opinions are valid"""
    
    second_message = """2: From approximately 20 to 25 minutes before Dhuhr till the start of Dhuhr. So you must not pray any voluntary prayer from 25 mins before Dhuhr until Dhuhr starts. Some scholars said that this time is shorter. Ibn Qasim (may Allah have mercy on him) said that it is a brief time period, only enough to say the takbeer to start the prayer. 
Again, if you wanna go the safe route you should go with the '25 minutes before Dhuhr' opinion. 

3: From when you've prayed Asr till the start of maghrib, meaning that once you've prayed the fardh of Asr, you must not pray any voluntary prayer after that until maghrib arrives. 

If you choose to use the prayer reminder feature for Al Kitab bot and have the option for alerts for the forbiden times enabled, you should know that for every forbidden time the bot follows the safest opinion regarding that time. 

Another thing to note is that for the case of the fajr and asr forbidden times, they are based off when you've actually prayed the fardh of that prayer. But the bot does not have a way of knowing whether you have prayed said prayer. So for the case of Fajr the bot will tell you at the time of sunrise that the forbidden time has begun, and it will show you the end time for the forbidden time which is 15 minutes after sunrise. As for Asr you should just remember to not pray any voluntary prayer after praying the fardh of Asr

If you feel any information given here is incorrect/inaccurate, or something should be added, feel free to DM the creator of the bot.

If you want to read into further detail and read the evidence for the views provided, refer to these links:
https://islamqa.info/en/answers/48998/forbidden-prayer-times
https://islamqa.info/en/answers/112114/naafil-prayers-that-it-is-permissible-to-do-at-times-when-prayer-is-otherwise-forbidden
https://islamqa.info/en/answers/34668/naafil-prayers-at-times-when-prayer-is-not-allowed
https://islamqa.info/en/answers/20013/making-up-prayers-at-times-when-prayer-is-disallowed"""
    await interaction.followup.send(first_message)
    await interaction.followup.send(second_message)

# Function to send a message to all registered users
async def send_message(message):
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT UserID FROM ReminderData")
        user_ids = await cursor.fetchall()
        user_ids = [user_id[0] for user_id in user_ids]
        for user_id in user_ids:
            user = await client.fetch_user(user_id)
            await user.send(message)

# running the bot
client.run(botToken)