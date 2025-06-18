# Import required dependencies
import discord
from discord import Interaction
import requests
import datetime
import datetime as dt_module
from datetime import datetime
import asyncio
import requests
import pytz
from urllib.parse import quote

# Make a list to keep track of users who are using a command to avoid spamming
users_list = []

async def get_prayer_timings(country, city, date, school, midnightMode, method, selected_prayers, forbiddenTimesReminder):
    prayer_timings = []
    url = f"http://api.aladhan.com/v1/timingsByCity/{date}?city={city}&country={country}&method={method}&school={school}&midnightMode={midnightMode}"
    data = requests.get(url)
    data = data.json()

    for prayer in selected_prayers:
        if prayer == None:
            prayer_timings.append(None)
        elif prayer == "HanafiAsr":
            if school == 1:
                prayer_timings.append(None)
            else:
                url = f"http://api.aladhan.com/v1/timingsByCity/{date}?city={city}&country={country}&method={method}&school=1&midnightMode={midnightMode}"
                hanafidata = requests.get(url)
                hanafidata = hanafidata.json()
                prayer_timings.append(hanafidata['data']['timings']['Asr'])
        else:
            prayer_timings.append(data['data']['timings'][prayer])
    
    #Making sure to always store beforeDhuhr and Sunrise times if the user chooses to be alerted about forbidden prayer times
    if forbiddenTimesReminder == 0:
        beforeDhuhr = None
    else:
        if prayer_timings[2] != None:
            Dhuhr = prayer_timings[2]
        else:
            Dhuhr = data['data']['timings']['Dhuhr']
        if prayer_timings[1] == None:
            prayer_timings[1] = data['data']['timings']['Sunrise']

        Dhuhr = datetime.strptime(Dhuhr, "%H:%M")
        beforeDhuhr = Dhuhr - dt_module.timedelta(minutes=25)
        beforeDhuhr = beforeDhuhr.strftime("%H:%M")

    return prayer_timings, beforeDhuhr

async def wait_for_interaction(self, message):
    # Longer timeout for timezone dropdown
    if message.content == "Please select your timezone (if you select 'More...' you cannot go back to the previous options, you have to wait for the interaction to time out):":
        timeout = 300
    else:
        timeout = 60
    try:
        # Wait for bot to react with checkmark
        await self.client.wait_for(
            'reaction_add',
            check=lambda r, u: r.message.id == message.id and u.id == self.client.user.id,
            timeout = timeout
        )
        timeout = False
    except asyncio.TimeoutError:
        timeout = True
    return timeout

class mode_selection_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Automatic'),
            discord.SelectOption(label='Manual')
        ]
        self.mode = None
        super().__init__(placeholder="Modes", min_values=1, max_values=1, options=options)
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.mode = self.values[0]
        return self.view.stop()

def geo_adhan_lookup(search_term: str, limit: int = 1, get_prayer_timings: bool = False):
    if not search_term:
        raise ValueError("Search term cannot be empty")

    if limit > 3:
        raise ValueError("Limit cannot be more than 3")

    if get_prayer_timings and limit > 1:
        raise Warning("Avoid using get_prayer_timings with limit > 1")

    # Escape the search term to ensure safe URL construction
    escaped_search_term = quote(search_term)

    url = f"https://geo.krauv.com/lookup/{escaped_search_term}?limit={limit}&get_prayer_timings={get_prayer_timings}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("Error fetching data")

    return response.json()

class location_confirmation_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Yes'),
            discord.SelectOption(label='No')
        ]
        super().__init__(placeholder="Location confirmation", min_values=1, max_values=1, options=options)
        self.choice = None
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.choice = self.values[0]
        return self.view.stop()

async def location_valid(country, city):
    try: 
        date = datetime.today().strftime("%d-%m-%Y")
        url = f"http://api.aladhan.com/v1/timingsByCity/{date}?city={city}&country={country}"
        response = requests.get(url)
        data = response.json()
        if data['data'] == "Unable to geocode address.":
            return False
        else:
            return True
    except:
        return False

async def get_location(self, interaction: discord.Interaction, message):
    await interaction.followup.send(message)
    try:
        location_message = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    except asyncio.TimeoutError:
        return None
    location = location_message.content
    return location

async def get_country(self, interaction: discord.Interaction):
    await interaction.followup.send("Please type the name of your country:")
    try:
        country_message = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    except asyncio.TimeoutError:
        return None
    country = country_message.content
    await country_message.add_reaction('\u2705')
    return country

async def get_city(self, interaction: discord.Interaction):
    await interaction.followup.send("Please type the name of your city:")
    try:
        city_message = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
    except asyncio.TimeoutError:
        return None
    city = city_message.content
    await city_message.add_reaction('\u2705')
    return city

async def get_info(self, interaction: discord.Interaction, message_str, view):
    message = await interaction.followup.send(message_str, view=view)
    timeout = await wait_for_interaction(self, message)
    if timeout:
        view.stop()
        return None
    else:
        await asyncio.sleep(1)
        return view
    
def sort_prayers(selected_prayers):
    prayers = []
    if "Fajr" in selected_prayers:
        prayers.append("Fajr")
        prayers.append("Sunrise")
    else:
        prayers.append(None)
        prayers.append(None)
    if "Dhuhr" in selected_prayers:
        prayers.append("Dhuhr")
    else:
        prayers.append(None)
    if "Asr" in selected_prayers:
        prayers.append("Asr")
        prayers.append("HanafiAsr")
    else:
        prayers.append(None)
        prayers.append(None)
    if "Maghrib" in selected_prayers:
        prayers.append("Maghrib")
    else:
        prayers.append(None)
    if "Isha" in selected_prayers:
        prayers.append("Isha")
        prayers.append("Midnight")
    else:
        prayers.append(None)
        prayers.append(None)
    return prayers
    
    
def get_time_string(least_difference):
    hours_till_prayer = least_difference.seconds // 3600
    minutes_till_prayer = (least_difference.seconds // 60) % 60
    if hours_till_prayer == 0:
        hour_str = ''
        hours_till_prayer = ''
    elif hours_till_prayer == 1:
        hour_str = ' hr '
    else:
        hour_str = ' hrs '
    if minutes_till_prayer == 0:
        minute_str = ''
        minutes_till_prayer = ''
    elif minutes_till_prayer == 1:
        minute_str = ' min'
    else:
        minute_str = ' mins'
    time_str = f'{hours_till_prayer}{hour_str}{minutes_till_prayer}{minute_str}'
    return time_str


def get_time_till_next_prayer(prayer_times, timezone):
    current_time = datetime.now(pytz.timezone(timezone))
    for i in range(0, len(prayer_times)):
        prayer_times[i] = pytz.timezone(timezone).localize(prayer_times[i])
    least_difference = prayer_times[0] - current_time
    for i in range(1, len(prayer_times)):
        difference = prayer_times[i] - current_time
        if difference.seconds < least_difference.seconds:
            least_difference = difference
    time_str = get_time_string(least_difference)
    return time_str
            
        
class dropdownView(discord.ui.View):
    def __init__(self, dropdown):
        super().__init__()
        self.add_item(dropdown)

class update_info_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Country/City/Timezone (Automatic Mode)"),
            discord.SelectOption(label="Country/City (Manual Mode)"),
            discord.SelectOption(label="Timezone"),
            discord.SelectOption(label="School"),
            discord.SelectOption(label="Midnight Mode", value="MidnightMode"),
            discord.SelectOption(label="Institute", value="Method"),
            discord.SelectOption(label="Selected Prayers"),
            discord.SelectOption(label="Alerts for Forbidden Prayer Times", value='forbiddenTimesReminder'),
            discord.SelectOption(label="Time Format", value="HourFormat"),
            discord.SelectOption(label="Reminder Time", value="RemindEarly")
        ]
        super().__init__(placeholder="Info", min_values=1, max_values=1, options=options)
        self.info_to_update = None
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.info_to_update = self.values[0]
        return self.view.stop()

class timezone_dropdown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=timezone) for timezone in pytz.all_timezones[:24]]
        options.append(discord.SelectOption(label="More..."))
        super().__init__(placeholder="Timezones", min_values=1, max_values=1, options=options)
        self.timezone = None
        self.options_selected = 24
    async def callback(self, interaction:Interaction):
        await interaction.response.defer()
        self.timezone = self.values[0]
        # A dropdown can have max 24 options so a 'More...' option is added to basically paginate the options
        if self.timezone == "More...":
            self.options = [discord.SelectOption(label=timezone) for timezone in pytz.all_timezones[self.options_selected:self.options_selected + 24]]
            if len(self.options) > 23:
                self.options.append(discord.SelectOption(label="More..."))
            self.options_selected += 24
            await interaction.message.edit(view=self.view)
        else:
            await interaction.message.add_reaction('\u2705')
            return self.view.stop()

class school_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Shafi/Hanbali/Maliki", description="Asr time is when shadow is equal to length of an object", value=0),
            discord.SelectOption(label="Hanafi", description="Asr time is when shadow is equal to double the length of an object", value=1)
        ]
        super().__init__(placeholder="School of thoughts:", min_values=1, max_values=1, options=options)
        self.school = None

    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.school = self.values[0]
        return self.view.stop()

class midnightMode_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Standard", description="Midnight is calculated from Mid Sunset to Sunrise", value="0"),
            discord.SelectOption(label="Jafari", description="Midnight is calculated from Mid Sunset to Fajr", value="1")
        ]
        super().__init__(placeholder="Midnight Modes:", min_values=1, max_values=1, options=options)
        self.midnightMode = None

    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.midnightMode = self.values[0]
        return self.view.stop()

class method_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Shia Ithna-Ansari", value="0"),
            discord.SelectOption(label="University of Islamic Sciences, Karachi", value="1"),
            discord.SelectOption(label="Islamic Society of North America", value="2"),
            discord.SelectOption(label="Muslim World League", value="3"),
            discord.SelectOption(label="Umm Al-Qura University, Makkah", value="4"),
            discord.SelectOption(label="Egyptian General Authority of Survey", value="5"),
            discord.SelectOption(label="Institute of Geophysics, University of Tehran", value="7"),
            discord.SelectOption(label="Gulf Region", value="8"),
            discord.SelectOption(label="Kuwait", value="9"),
            discord.SelectOption(label="Qatar", value="10"),
            discord.SelectOption(label="Majlis Ugama Islam Singapura, Singapore", value="11"),
            discord.SelectOption(label="Union Organization islamic de France", value="12"),
            discord.SelectOption(label="Diyanet İşleri Başkanliği, Turkey", value="13"),
            discord.SelectOption(label="Spiritual Administration of Muslims of Russia", value="14"),
            discord.SelectOption(label="Moonsighting Committee Worldwide", value="15"),
            discord.SelectOption(label="Dubai", value="16")
        ]
        # No I did not miscount, the API miscounted so I had to skip 6 as well when assigning ids
        super().__init__(placeholder="Methods: ", min_values=1, max_values=1, options=options)
        self.method = None

    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.method = self.values[0]
        return self.view.stop()

class prayerOptions_View(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.selected_prayers = set()

    async def handle_prayer_button(self, interaction:Interaction, button:discord.ui.Button):
        if button.custom_id in self.selected_prayers:
            self.selected_prayers.remove(button.custom_id)
            button.style = discord.ButtonStyle.secondary
        else:
            self.selected_prayers.add(button.custom_id)
            button.style = discord.ButtonStyle.primary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Fajr", style=discord.ButtonStyle.secondary, custom_id="Fajr")
    async def Fajr(self, interaction:Interaction, button:discord.ui.Button):
        await self.handle_prayer_button(interaction, button)

    @discord.ui.button(label="Dhuhr", style=discord.ButtonStyle.secondary, custom_id="Dhuhr")
    async def Dhuhr(self, interaction:Interaction, button:discord.ui.Button):
        await self.handle_prayer_button(interaction, button)

    @discord.ui.button(label="Asr", style=discord.ButtonStyle.secondary, custom_id="Asr")
    async def Asr(self, interaction:Interaction, button:discord.ui.Button):
        await self.handle_prayer_button(interaction, button)

    @discord.ui.button(label="Maghrib", style=discord.ButtonStyle.secondary, custom_id="Maghrib")
    async def Maghrib(self, interaction:Interaction, button:discord.ui.Button):
        await self.handle_prayer_button(interaction, button)

    @discord.ui.button(label="Isha", style=discord.ButtonStyle.secondary, custom_id="Isha")
    async def Isha(self, interaction:Interaction, button:discord.ui.Button):
        await self.handle_prayer_button(interaction, button)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def Confirm(self, interaction:Interaction, button:discord.ui.Button):
        if len(self.selected_prayers) >= 1:
            await interaction.message.add_reaction('\u2705')
            await interaction.response.defer()
            self.stop()
        else:
            await interaction.followup.send("Please select at least one prayer.")
                
class forbiddenTimes_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Yes', value='1'),
            discord.SelectOption(label='No', value='0')
        ]
        super().__init__(placeholder='Alert on forbidden times', min_values=1, max_values=1, options=options)
        self.forbiddenTimesReminder = None
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.forbiddenTimesReminder = self.values[0]
        return self.view.stop()
    
class hourFormat_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="12 hour", value="1"),
            discord.SelectOption(label="24 hour", value="0")
        ]
        super().__init__(placeholder="Time format", min_values=1, max_values=1, options=options)
        self.hourFormat = None
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.hourFormat = self.values[0]
        return self.view.stop()

class remindEarly_dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Remind on time', value=0),
            discord.SelectOption(label='Remind 5 minutes early', value=1)
        ]
        super().__init__(placeholder='Reminder Time', min_values=1, max_values=1, options=options)
        self.remindEarly = None
    async def callback(self, interaction:Interaction):
        await interaction.message.add_reaction('\u2705')
        await interaction.response.defer()
        self.remindEarly = self.values[0]
        return self.view.stop()
    