''' 

Title: gizmo
Author: Kian Mortimer
Date: 03/12/22

Description:
A Discord bot for interacting with ballchasing.com
A reconstruction of two previous projects (HUNK / Thoth),
implemented with slash commands.

Version: 1.4.2
22/08/23

'''

# IMPORTS
import discord
import discord.ext.commands
import logging

import data
import commands
import events


# MAIN LOOP
if __name__ == '__main__':

    # Process Started
    print(' > Process Started')
    
    # Set up logger - https://realpython.com/python-logging/#the-logging-module
    logging.basicConfig(format='{asctime}: {levelname:<7} : {name}/{funcName} - {message}', datefmt='%y-%m-%d %H:%M:%S', style='{')
    
    # Define the bot status and create the client
    intents = discord.Intents.default()
    intents.members = True
    activity = discord.Activity(name = 'Omniscience', type = 5)
    bot = discord.ext.commands.Bot(
        activity=activity,
        status=discord.Status.online,
        intents=intents
    )
    
    # Initialise events & commands
    events.load(bot)
    commands.load(bot)
    
    # Run
    bot.run(data.TOKEN_DISCORD_GIZMO)

    # Process Terminated
    print(' > Process Terminated')
    
    
    
    
