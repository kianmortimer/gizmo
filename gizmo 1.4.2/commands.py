''' 

Author: Kian Mortimer
Date: 03/12/22

Description:
Bot commands are loaded in this file

'''


# IMPORTS
import discord.ext.commands

import data
import utility
import scraping
import database


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
    @bot.slash_command(
        name="test",
        description="Test Command",
        guild_ids=[data.SERVER_TEST_ID] # Omit to make global
    )
    @discord.option(
        name="target", 
        description="Enter the target's name or ID",
        required=False,
        default='None'
    )
    async def test(ctx, target): 
        await ctx.respond(f"Target: {target}")
    '''


    ## PUBLIC COMMANDS ##
    
    # INFO
    @bot.slash_command(
        name="info",
        description="Get various information about an account"
    )
    @discord.option(
        name="target", 
        description="Specify the target account for the search",
        required=False,
        default=None
    )
    async def info(ctx, target):
        await ctx.defer()
        response, msg = await scraping.command_info(ctx, target)
        utility.log(ctx, target, response, msg)


    ## PRIVATE COMMANDS ##
        
    # SERVERS
    @bot.slash_command(
        name="servers",
        description="List active guilds"
    )
    @utility.developer()
    async def servers(ctx):
        activeservers = bot.guilds
        servers = ""
        for guild in activeservers:
            servers = servers + " > **" + guild.name + "**    `" \
                      + guild.owner.name + "#" + guild.owner.discriminator \
                      + "`    `" + str(guild.member_count) + "`\n"
        await ctx.respond(servers)

    # RECONDITION DATABASE
    @bot.slash_command(
        name="recondition",
        description="Update all the records in the database"
    )
    @utility.developer()
    async def recondition(ctx):
        await ctx.respond(' > Updating all database records')
        db = database.Database()
        if db.connect():
            response = db.recondition()
            db.close()

    # GET DATABASE RECORD
    @bot.slash_command(
        name="get",
        description="Get a player and their accounts from the database"
    )
    @discord.option(
        name="player", 
        description="The player's name",
        required=True,
        default=None
    )
    @utility.developer()
    async def get(ctx, player):
        embed = None
        db = database.Database()
        if db.connect():
            response = db.get(player)
            if response is None:
                # Create the failed Discord embed
                embed = discord.Embed(
                    title=f"\"{player}\" not found.",
                    description="The player is not in the database",
                    color=data.RED
                )
            else:
                name = response[0][0]
                region = response[0][1]
                original = response[0][2]
                accounts = ""
                for result in response:
                    if result[0] != name: break
                    account = result[3] + ":" + result[4]
                    main = data.PLAYER_STATUS_MAIN if result[5] == 1 else data.PLAYER_STATUS_ALT
                    accounts = f"{accounts}{main}  ```{account}```\n"
                if original is not None:
                    original = f"`AKA:{original}`"
                else:
                    original = ""
                
                # Create the Discord embed using the gathered information
                embed = discord.Embed(
                    title=name,
                    description=f"`{region}`   {original}",
                    color=data.GREEN
                )
                embed.add_field(
                    name="**Accounts**",
                    value=accounts,
                    inline=False
                )
            db.close()
        else:
            # Database Offline
            embed = discord.Embed(
                title=f"Database Offline",
                description="Restart the database before continuing",
                color=data.ORANGE
            )
        
        embed.set_footer(
            text=data.BOT_FOOTER_TEXT
        )
        await ctx.respond(embed=embed)

    # SET NEW DATABASE RECORD
    @bot.slash_command(
        name="set",
        description="Set a new player or account in the database"
    )
    @discord.option(
        name="account", 
        description="The account to be added",
        required=True,
        default=None
    )
    @discord.option(
        name="player", 
        description="The player's name",
        required=True,
        default=None
    )
    @utility.developer()
    async def set(ctx, account, player):
        embed = None
        db = database.Database()
        if db.connect():
            response = db.set(account, player)
            if not response:
                # Create the failed Discord embed
                embed = discord.Embed(
                    title=f"\"{account}\" not set.",
                    description="The account has not been entered into the database",
                    color=data.RED
                )
            else:
                # Create the success Discord embed
                embed = discord.Embed(
                    title="Successfully updated!",
                    description=f"```{account}``` → {player}",
                    color=data.GREEN
                )
                db.close()
        else:
            # Database Offline
            embed = discord.Embed(
                title=f"Database Offline",
                description="Restart the database before continuing",
                color=data.ORANGE
            )
        embed.set_footer(
                text=data.BOT_FOOTER_TEXT
            )
        await ctx.respond(embed=embed)

    # ADD FLAG TO PLAYER
    @bot.slash_command(
        name="flag",
        description="Add a flag to a player"
    )
    @discord.option(
        name="player", 
        description="The player",
        required=True,
        default=None
    )
    @utility.developer()
    async def flag(ctx, player):
        embed = None
        db = database.Database()
        if db.connect():
            response, player_id = db.flag(player)
            if player_id is None:
                # "Failed" Discord embed: Unknown error
                    embed = discord.Embed(
                        title=f"Unknown error on \"{player}\"",
                        description="[Edit Table](http://localhost/phpmyadmin/sql.php?db=rocket_league&table=flags&pos=0)",
                        color=data.RED
                    ) 
            elif not response:
                if player_id == 0:
                    # Failed Discord embed: Player doesnt exist
                    embed = discord.Embed(
                        title=f"\"{player}\" doesn't exist",
                        description="Name must be an **exact** match",
                        color=data.RED
                    )
                elif player_id > 0:
                    # "Failed" Discord embed: Player already in flags table
                    embed = discord.Embed(
                        title=f"\"{player}\" already has flags",
                        description=f"**{player_id}**: [Edit Record](http://localhost/phpmyadmin/tbl_select.php?db=rocket_league&table=flags)",
                        color=data.YELLOW
                    ) 
            else:
                # Create the success Discord embed
                embed = discord.Embed(
                    title=f"{player}",
                    description=f"**{player_id}**: [Edit Record](http://localhost/phpmyadmin/tbl_select.php?db=rocket_league&table=flags)",
                    color=data.GREEN
                )
            
            db.close()
        else:
            # Database Offline
            embed = discord.Embed(
                title=f"Database Offline",
                description="Restart the database before continuing",
                color=data.ORANGE
            )
        embed.set_footer(
                text=data.BOT_FOOTER_TEXT
            )
        await ctx.respond(embed=embed)

    # SET DOMAIN
    @bot.slash_command(
        name="domain",
        description="Set the domain for Balls messaging",
        guild_ids=[data.SERVER_TEST_ID]
    )
    @discord.option(
        name="Channel ID", 
        description="The channel to send messages to",
        required=True,
        default=None
    )
    @utility.developer()
    async def domain(ctx, channel_id):
        data.DOMAIN = data.DOMAIN_DEFAULT
        channel = None

        try:
            channel_id = int(channel_id)
        except:
            channel_id = int(data.DOMAIN_DEFAULT)
        if channel is None:
            channel = bot.get_channel(channel_id)
        if channel is None:
            channel = bot.get_user(channel_id)
        if channel is None:
            channel = bot.get_channel(int(data.DOMAIN_DEFAULT))
        data.DOMAIN = int(channel.id)
        
        await ctx.respond(f"> **Domain** → `#{channel.name}`")
            
        
        

    # SEND MESSAGE
    @bot.slash_command(
        name="send",
        description="Send a message as Balls to the specified domain",
        guild_ids=[data.SERVER_TEST_ID]
    )
    @discord.option(
        name="Content", 
        description="Content to send",
        required=True,
        default=None
    )
    @utility.developer()
    async def send(ctx, content):
        channel = bot.get_channel(int(data.DOMAIN))
        if channel is None:
            channel = bot.get_user(int(data.DOMAIN))
            if channel.dm_channel is None:
                channel = await channel.create_dm()

        await channel.send(content)

        name = "None"
        try:
            name = channel.name
        except:
            name = channel.recipient.name

        await ctx.respond(f"> `#{name}` → `{content}`")