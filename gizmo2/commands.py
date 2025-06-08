''' 
Author: Kian Mortimer
Date: 18/05/25

Description:
Bot commands are loaded in this file
'''


# IMPORTS
import discord
import os

# MY IMPORTS
import config
import checks
import actions
import rocketleague


# LOAD THE BOT COMMANDS
def load(bot):
    '''
    This function should only be accessed from bot.py and only once.
    All commands are slash commands, meaning they are accessible through
    Discord's new slash system only and not direct messages.

    Guild commands are guild specific:
    Explicitly specified through the argument "guild_ids=[]".
    This type of command updates immediately but cannot be used
    outside of the specified guilds. Guild commands should be used
    for testing as a result of updating immediately.

    Global commands are accessible in all guilds and direct messages:
    Implicitly specified through omitting the "guild_ids=[]" argument.
    This type of command can take up to an hour to update and therefore
    should not be used for testing purposes.    
    '''

    # BLANK COMMAND
    # Use as a platform for building other commands
    
    '''
    @bot.tree.command(
        name="ph", 
        description="placeholder",
        guild=discord.Object(config.GUILDS[0])
    )
    @utility.developer()
    async def placeholder(interaction: discord.Interaction):
        await interaction.response.send_message("[placeholder] was run")
    '''

    ## DEVELOPER ##

    @bot.command()
    @checks.developer()
    async def sync(ctx) -> None:
        synced = await bot.tree.sync()
        print(f" > Synced [{len(synced)}] commands globally")
        await ctx.send(f" > `Synced [{len(synced)}] commands globally`")

    ## EVERYONE ##

    @bot.tree.command(
        name="balls", 
        description="Invoke the power of Balls II"
    )
    @checks.everyone()
    async def balls(interaction: discord.Interaction, target: str = None) -> None:
        print(f" + Command: /balls {str(target)}")
        print(f"   + User : {interaction.user.name}")
        print(f"   + Guild: {interaction.guild.name}")
        await actions.update_presence(bot, config.ACTIVITY["Thinking"])
        await interaction.response.defer()

        await rocketleague.run_shallow_search(interaction, target)

        await actions.reset_presence(bot)

    @bot.tree.command(
        name="deep", 
        description="Go balls deep into the archives"
    )
    @checks.everyone()
    async def deep(interaction: discord.Interaction, target: str = None) -> None:
        print(f" + Command: /deep {str(target)}")
        print(f"   + User : {interaction.user.name}")
        print(f"   + Guild: {interaction.guild.name}")
        await actions.update_presence(bot, config.ACTIVITY["Thinking"])
        await interaction.response.defer()

        player = await rocketleague.run_shallow_search(interaction, target)
        if player is not None:
            more_coming = await interaction.followup.send(" > More coming **↓** (This might take a minute)")
            await rocketleague.run_deep_search(interaction, player)
            await more_coming.delete()

        await actions.reset_presence(bot)


