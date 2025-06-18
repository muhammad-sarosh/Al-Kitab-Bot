# Import required dependencies
import discord
from discord.ext import commands
from discord import app_commands
from discord import FFmpegPCMAudio
from shared_resources import surahs, surah_links
import asyncio

class quran_player(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = [] # Initialize an empty queue
        self.first_play = True

    # To make the bot leave the voice channel if all users leave
    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        bot_voice_channel = member.guild.voice_client # Voice client of the bot

        if bot_voice_channel: # If the bot is in a voice channel
            voice_channel = before.channel # Channel of the user before the state change
            
            if not member.id == self.client.user.id: # If the bot is not the user
                if voice_channel == bot_voice_channel.channel: # If the channel of the user is the same as the channel of the bot
                    if len(bot_voice_channel.channel.members) == 1: # If there is only 1 member in the channel (the bot)
                        await bot_voice_channel.disconnect() # Disconnect from the voice channel


    @app_commands.command(name='play', description='Play a Quran surah by number in the voice chat you are currently connected to')
    async def play(self, interaction: discord.Interaction, surah_number: int):
        try:
            if interaction.user.voice: # If user is in voice channel
                vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
                if vc is None: # If the bot is not in a voice channel
                    channel = interaction.user.voice.channel
                    vc = await channel.connect()
                elif interaction.user.voice.channel.id != vc.channel.id:
                    await interaction.response.send_message("You are not in the same voice channel as the bot.")
                    return

                if surah_number > 114 or surah_number < 1:
                    await interaction.response.send_message("Surah number must be between 1 and 114.")
                    return
                surah = surahs[surah_number]
                
                url = surah_links[surah]
                self.queue.append(url)
                if not self.first_play:
                    await interaction.response.send_message(f"{surah} has been added to the queue.")
                self.first_play = False
                if not vc.is_playing():
                    await interaction.response.send_message('**Processing...**')
                    self.play_next(interaction, vc)
            else:
                await interaction.response.send_message("You are not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN play COMMAND: {e}\n\n")


    def play_next(self, interaction: discord.Interaction, vc):
        try:
            if self.queue:
                next_url = self.queue.pop(0)
                surah_name = self.find_name(next_url)
                next_source = FFmpegPCMAudio(next_url)
                asyncio.create_task(interaction.channel.send(f"**Playing:** {surah_name}"))
                vc.play(next_source, after=lambda e:self.play_next)
            else:
                self.first_play = True
                vc.stop()
        except Exception as e:
            print(f"\n\nERROR IN play_next FUNCTION: {e}\n\n")

            
    @app_commands.command(name='viewqueue', description='View the current queue of surahs in the voice channel you are currently connected to')
    async def viewqueue(self, interaction: discord.Interaction):
        try:
            vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if vc:
                if interaction.user.voice:
                    if interaction.user.voice.channel.id == vc.channel.id:
                        if self.queue:
                            queue_str = "**Queue:** "
                            for surah_link in self.queue:
                                surah_name = self.find_name(surah_link)
                                queue_str += surah_name + ", "
                            queue_str = queue_str[:-2]
                            await interaction.response.send_message(queue_str)
                        else:
                            await interaction.response.send_message("The queue is empty.")
                    else:
                        await interaction.response.send_message("You are not in the same voice channel as the bot.")
                else:
                    await interaction.response.send_message("You are not in a voice channel.")
            else:
                await interaction.response.send_message("I am not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN viewqueue COMMAND: {e}\n\n")

    def find_name(self, surah_link):
        for surah_name, value in surah_links.items():
            if value == surah_link:
                return surah_name


    @app_commands.command(name='pause', description='Pause the currently playing surah in the voice channel you are currently connected to')
    async def pause(self, interaction: discord.Interaction):
        try:
            vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if vc: # If the bot is in a voice channel
                if interaction.user.voice:
                    if interaction.user.voice.channel.id == vc.channel.id:
                        if vc.is_playing():
                            await interaction.response.send_message("Surah has been paused.")
                            vc.pause()
                        else:
                            await interaction.response.send_message("No surah is currently playing.")
                    else:
                        await interaction.response.send_message("You are not in the same voice channel as the bot.")
                else:
                    await interaction.response.send_message("You are not in a voice channel.")
            else:
                await interaction.response.send_message("I am not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN pause COMMAND: {e}\n\n")


    @app_commands.command(name='resume', description='Resume the currently paused surah in the voice channel you are currently connected to')
    async def resume(self, interaction: discord.Interaction):
        try:
            vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if vc: # If bot is in a voice channel
                if interaction.user.voice:
                    if interaction.user.voice.channel.id == vc.channel.id:
                        if vc.is_paused():
                            await interaction.response.send_message("Surah has been resumed.")
                            vc.resume()
                        else:
                            await interaction.response.send_message("No surah is currently paused.")
                    else:
                        await interaction.response.send_message("You are not in the same voice channel as the bot.")
                else:
                    await interaction.response.send_message("You are not in a voice channel.")
            else:
                await interaction.response.send_message("I am not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN resume COMMAND: {e}\n\n")


    @app_commands.command(name='skip', description='Skip the currently playing surah in the voice channel you are currently connected to')
    async def skip(self, interaction: discord.Interaction):
        try:
            vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if vc:
                if interaction.user.voice:
                    if interaction.user.voice.channel.id == vc.channel.id:
                        if vc.is_playing():
                            await interaction.response.send_message("Surah has been skipped.")
                            vc.stop()
                            self.play_next(interaction, vc)
                        else:
                            await interaction.response.send_message("No surah is currently playing.")
                    else:
                        await interaction.response.send_message("You are not in the same voice channel as the bot.")
                else:
                    await interaction.response.send_message("You are not in a voice channel.")
            else:
                await interaction.response.send_message("I am not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN skip COMMAND: {e}\n\n")


    @app_commands.command(name='clearqueue', description='Clear the entire queue in the voice channel you are currently connected to')
    async def clearqueue(self, interaction: discord.Interaction):
        try: 
            vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if vc:
                if interaction.user.voice:
                    if interaction.user.voice.channel.id == vc.channel.id:
                        if self.queue != []:
                            self.queue = []
                            self.first_play = True
                            vc.stop()
                            await interaction.response.send_message("The queue has been cleared.")
                        else:
                            await interaction.response.send_message("The queue is already empty.")
                    else:
                        await interaction.response.send_message("You are not in the same voice channel as the bot.")
                else:
                    await interaction.response.send_message("You are not in a voice channel.")
            else:
                await interaction.response.send_message("I am not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN clearqueue COMMAND: {e}\n\n")


    @app_commands.command(name='leave', description='Disconnect the bot from the voice channel it is currently connected to')
    async def leave(self, interaction: discord.Interaction):
        try:
            vc = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if vc: # If the bot is in a voice channel
                if interaction.user.voice:
                    if interaction.user.voice.channel.id == vc.channel.id:
                        self.queue = []
                        self.first_play = True
                        await interaction.response.send_message("I have left the voice channel.")
                        await interaction.guild.voice_client.disconnect()
                    else:
                        await interaction.response.send_message("You are not in the same voice channel as the bot.")
                else:
                    await interaction.response.send_message("You are not in a voice channel.")
            else:
                await interaction.response.send_message("I am not in a voice channel.")
        except Exception as e:
            print(f"\n\nERROR IN leave COMMAND: {e}\n\n")
            
async def setup(client):
    await client.add_cog(quran_player(client))