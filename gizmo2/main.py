''' 
Title: gizmo2
Author: Kian Mortimer
Date: 18/05/25

Description:
A Discord bot for interacting with ballchasing.com
A rewrite of the infamous Balls (gizmo1)

gizmo2 uses the Interactions discord.py features
A key function of gizmo1 was the web scraping of ballchasing.com which
has since been blocked by forcing users to sign in to Steam before displaying
the information that would previously have been scraped.

The goal of gizmo2 is to be a compact framework for adding on
extra features.

Version: 2
18/05/25
'''

# IMPORTS
import discord
import discord.ext.commands as slash_commands
from dotenv import load_dotenv
import os
import logging

# MY IMPORTS
import events
import commands
import config
import actions

# MAIN LOOP
if __name__ == '__main__':

    # Process Started
    print(' > Process Started')

    # Define the bot status and create the client
    intents = discord.Intents.default()
    intents.message_content = True
    state = config.DEFAULT_ACTIVITY['State']
    if (config.DEFAULT_ACTIVITY['Name'] == "Rocket League"):
        state = actions.random_presence_rl()
    bot = slash_commands.Bot(
        command_prefix=config.PREFIX,
        activity=discord.Activity(
            name = config.DEFAULT_ACTIVITY['Name'], 
            type = config.DEFAULT_ACTIVITY['Type'],
            state = state
        ),
        status=config.DEFAULT_ACTIVITY['Status'],
        intents=intents
    )

    # Initialise logging handler
    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
    
    # Initialise events & commands
    load_dotenv()
    events.load(bot)
    commands.load(bot)
    
    # Run
    bot.run(os.getenv('TOKEN_DISCORD'), log_handler=handler, log_level=logging.DEBUG)

    # Process Terminated
    print(' > Process Terminated')