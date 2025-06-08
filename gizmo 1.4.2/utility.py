''' 

Author: Kian Mortimer
Date: 04/12/22

Description:
Utilities such as privilege checks are written here.

'''


# IMPORTS
import discord.ext.commands

import data


## PRIVILEGES ##

# Grant access to developers of the bot
def developer():
    def predicate(ctx):
        return (ctx.author.id == data.USER_JORYX_ID) or (ctx.author.id == data.USER_KIAN_ID)
    return discord.ext.commands.check(predicate)


## APP LOGGING ##

# Create logging function
def log(ctx, target, response, msg):
    with open('app.log', 'a') as file:
        description = "None"
        if msg is not None:
            description = msg.description.split(' ')[0].strip('**')
            if '```' in description or '<' in description:
                description = description.split('```')[-2]
        file.write(f'{"INFO" if response else "WARNING" if response is None else "ERROR":<7} : \
{ctx.author.name}>{ctx.guild}>{ctx.channel if ctx.guild is not None else "DM"} - \'{target if target is not None else "None"}\'>\'\
{description}\'\n')