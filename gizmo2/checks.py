''' 
Author: Kian Mortimer
Date: 18/05/25

Description:
Privilege checks are written here.
'''


# IMPORTS
import discord.ext.commands as slash_commands

# MY IMPORTS
import config


## PRIVILEGES ##

# Grant access only to developers of the bot
def developer():
    def predicate(ctx):
        return (str(ctx.author.id) in config.DEVELOPERS)
    return slash_commands.check(predicate)

# Grant access to everyone
def everyone():
    def predicate(ctx):
        return (str(ctx.author.id) not in config.BLACKLIST)
    return slash_commands.check(predicate)