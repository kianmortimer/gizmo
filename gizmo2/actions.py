''' 
Author: Kian Mortimer
Date: 18/05/25

Description:
Bot commands are loaded in this file
'''

# IMPORTS
import discord
import random

import config

# Change presence during command execution
async def update_presence(bot, presence):
    await bot.change_presence(
        status = presence['Status'],
        activity = discord.Activity(
            name = presence['Name'], 
            type = presence['Type'],
            state = presence['State']
        )
    )

# Reset presence to the default
async def reset_presence(bot):
    state = config.DEFAULT_ACTIVITY['State']
    if (config.DEFAULT_ACTIVITY['Name'] == "Rocket League"):
        state = random_presence_rl()
    
    await bot.change_presence(
        status = config.DEFAULT_ACTIVITY['Status'],
        activity = discord.Activity(
            name = config.DEFAULT_ACTIVITY['Name'], 
            type = config.DEFAULT_ACTIVITY['Type'],
            state = state
        )
    )

# Randomise Rocket League InGame stats
def random_presence_rl() -> str:
    rnd = [random.randint(0,6),
           random.randint(0,5),
           random.randint(0,6),
           random.randint(0,6),
           random.randint(0,6),
           random.randint(0,10)
    ]
    time = random.choice([f"Overtime {rnd[0]}:{rnd[4]}{rnd[5]}",
                          f"{rnd[1]}:{rnd[4]}{rnd[5]} remaining",
                          f"{rnd[1]}:{rnd[4]}{rnd[5]} remaining"])
    state = random.choice([f"InGame {rnd[2]}:{rnd[3]} [{time}]", 
                              f"Private {rnd[2]}:{rnd[3]} [{time}]",
                              "In Training",
                              "Main Menu"])
    return state
    