''' 

Author: Kian Mortimer
Date: 03/12/22

Description:
Bot events such as on_ready() are loaded in this file.
These events are independent of commands but may be triggered
by them if the commands fail or other.

'''


# IMPORTS
import discord.ext.commands

# LOAD THE BOT EVENTS
def load(bot):
    ''' This function should only be accessed from bot.py and only once. '''
    
    @bot.event
    async def on_ready():
        print(" > Logged in as {0.user}".format(bot))

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, discord.ext.commands.errors.CheckFailure):
            await ctx.send("**Something went wrong; you may not have \
                           permission to access that command.**")
