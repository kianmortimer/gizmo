''' 

Author: Kian Mortimer
Date: 04/12/22

Description:
File governing the web scraping

'''


# IMPORTS
import discord
import requests
import ballchasing
import re
import bs4

import data
import database


# API call
api = ballchasing.Api(data.TOKEN_BALLCHASING)


# INFO COMMAND FUNCTION
async def command_info(ctx, target):
    '''
    @param
     - ctx    : Discord context
     - target : User input

    @return
     - boolean (success or not)

    Controls the execution of the info command.
    '''

    if target is None:
        msg = await failed_embed(ctx, "Help")
        return None, msg

    # Find the target and get replay information
    platform_player_id = determine_account(target)
    player_object, date = get_player_object(platform_player_id)

    # Error on parsing replay
    if player_object is None:
        msg = await failed_embed(ctx, f"\"{target}\" not found.")
        return False, msg

    # Target found
    # Web scrape the target's ballchasing.com profile
    player_information = scrape_ballchasing(platform_player_id)

    # Error on parsing ballchasing.com profile
    if player_information is None:
        msg = await failed_embed(ctx, f"\"{target}\" not found.")
        return False, msg

    # Identify player through database
    identify_results = [None, None, None, None, None, None]
    db = database.Database()
    if db.connect():
        identify_results = db.identify(player_object)
        db.close()

    # Format results from database query
    player_verification = ""
    if identify_results[0] is not None:
        main = data.PLAYER_STATUS_MAIN if identify_results[1] else data.PLAYER_STATUS_ALT
        player_verification = f"**{identify_results[0]}**  {main}"
    player_original = f"\n`AKA: {identify_results[5]}`" if identify_results[5] is not None else ''
    camera_similarity_full = ""
    if identify_results[3] is not None:
        if platform_player_id in data.ANONYMISE:
            identify_results[3].remove("joryx")
        for i in range(1,5):
            pcnt_padded = f"{identify_results[2][identify_results[3][-i]]:.0f}% ".ljust(7, ' ')
            name_padded = f" {identify_results[3][-i]}".ljust(10, ' ')
            camera_similarity_full = f"{camera_similarity_full}\n`{pcnt_padded}{name_padded}`"

    # Simplify some player data
    car_text = ""
    for car in player_information['Cars'].keys():
        car_text = car_text + f"{car}: `{player_information['Cars'][car]:.2%}`    "
    camera = player_object['camera']

    ''' Discord Embed '''
    
    # Create the Discord embed using the gathered information
    embed = discord.Embed(
        title=f"{player_object['name']}",
        description=f"{player_verification} {data.PLAYER_STATUS_PRO if player_information['Pro'] else ''}{player_original}\
        ```{player_object['id']['platform']}:{player_object['id']['id']}```",
        url=player_information['Ballchasing'],
        color=data.GREEN
    )
    embed.set_thumbnail(
        url=player_information['Avatar'] # Dynamic image only if Steam
    )
    embed.add_field(
        name="**Aliases**",
        value=f"```{player_information['Aliases']}```",
        inline=False
    )
    embed.add_field(
        name="**Friends**",
        value=f"```{player_information['Friends']}```",
        inline=False
    )
    embed.add_field(
        name="**Statistics**",
        value=f"Uploader: `{str(player_information['Uploader'])}`    {player_information['Appearances']}\n{car_text}\nLast Used Car: `{player_object['car_name'] if 'car_name' in player_object.keys() else 'Not Applicable'}`    Date: `{date}`",
        inline=False
    )
    embed.add_field(
        name="**Settings**",
        value=f"```📸 {camera['fov']} {camera['distance']} {camera['height']} {camera['pitch']} {camera['stiffness']} {camera['swivel_speed']} {camera['transition_speed']}   ⚙️ {player_object['steering_sensitivity']}```",
        inline=False
    )
    if identify_results[3] is not None:
        embed.add_field(
            name="**Camera Similarity**",
            value=f"{camera_similarity_full}",
            inline=True
        )
    embed.add_field(
        name="**Links**",
        value=f"- {player_information['Steam']}\n- {player_information['Ballchasing']}\n- {player_information['Tracker']}\n- {player_information['Liquipedia']}",
        inline=False
    )
    embed.set_footer(
        text=data.BOT_FOOTER_TEXT
    )
    await ctx.followup.send(embed=embed)

    # Flags
    if identify_results[4] is not None:
        # (id, player,special,game,rlcs,6mans,odl,boosting,service,hacking)
        flags = identify_results[4][0][2:]
        colour = data.ORANGE
        flag_text = ""
        for i in range(len(flags)):
            if flags[i]:
                flag_text = flag_text + data.FLAGS_TEXT[i] + "\n"
                if i == 0:
                    colour = data.BLUE
                    break
                elif (0 < i < 5) and colour is not data.BLUE: colour = data.RED
        if flag_text == "": 
            flag_text = "Flags not updated"
            colour = data.YELLOW
        embed_flags = discord.Embed(
            description=flag_text.strip(),
            color=colour
        )
        await ctx.send(embed=embed_flags)

    return True, embed

# Response if the target is invalid
async def failed_embed(ctx, title):
    '''
    @param
     - ctx    : Discord context
     - title  : String title of embed

    @return
     - None
    '''
    
    embed = discord.Embed(
        title=f"{title}", 
        description=f"*↓ Help for the `info` command*",
        color=data.ORANGE if title == "Help" else data.RED
    )
    embed.add_field(
        name="Example Inputs",
        value=f"`https://steamcommunity.com/id/SquishyMuffinz/`\n`https://ballchasing.com/player/steam/76561198286759507`\n`steam:76561198286759507`\n`Squishy`",
        inline=False
    )
    embed.add_field(
        name="Platforms",
        value="`steam` `epic` `xbox` `ps4`",
        inline=True
    )
    embed.add_field(
        name="Tips",
        value=" > This tool is **case-sensitive**\n > If searching by name, the name must be an **exact** match",
        inline=False
    )
    embed.set_footer(
        text=data.BOT_FOOTER_TEXT
    )
    await ctx.followup.send(embed=embed)

# Parse the argument(s) into a player id
def determine_account(target):
    '''
    @param
     - target : User input

    @return
     - String : Target's "platform:id" pair
    
    The purpose is to confirm a platform and id of the target.
    This can be achieved by first defining the search term for
    ballchasing.com using regex, and then running through a
    sequence of replay searches where the more specific search terms
    get applied first.
    '''

    if target is None: return None
    target.strip()

    ''' Input Parsing (Regex)

    Using regular expressions, the user input can be filtered
    into a tuple in the format (<platform>, <id>)

    The more specific search terms are more efficient and therefore
    we apply them before the more arbitrary terms.
    e.g. steam:76561198438198955 will have a lower complexity than
         any:joryx

    We search replays with the "deep=False" parameter in the
    ballchasing API because at this stage we don't care about receiving
    all the stats and instead are just scouting to find the replays.

    1.2.1:
    Swapped check for steam url and platform?id as an id/joryx 
    would have previously been picked up as a platform?id pair
    '''
    
    # Set up account id tuple
    account_id = ("", "")
    # Check for steam url
    if re.match("^.*((id)|(profiles))/[a-zA-Z0-9_-]{1,50}/*$", target) is not None:
        link = target.replace("/", " ").strip()
        split_link = link.split(" ")
        account_id = ("steam", split_link[-1])
    # Check for "platform?id" where ? is [: /]
    elif re.match("^[a-zA-Z4]{3,5}[: /][a-zA-Z0-9_-]{1,50}$", target) is not None:
        account_id = tuple(re.split("[: /]", target, 1))
    # Check for ballchasing url
    elif re.match("^.*/[a-z4]{3,5}/[a-zA-Z0-9_-]{1,50}/*$", target) is not None:
        link = target.replace("/", " ").strip()
        split_link = link.split(" ")
        account_id = (split_link[-2], split_link[-1])
    # Check for steam id
    elif re.match("^7656[0-9]{13}$", target) is not None:
        account_id = ("steam", target)
    # Check for "platform?name" where ? is [: /]
    elif re.match("^[a-zA-Z4]{3,5}[: /].{1,50}$", target) is not None:
        account_id = tuple(re.split("[: /]", target, 1))
    # Check for other
    elif re.match("^.{1,50}$", target) is not None:
        account_id = ("any", target)
    # Does not match expected
    else:
        return None

    # Account for user stupidity
    account_id = (account_id[0].strip().lower(), account_id[1].strip())
    
    ''' Replay Searches

    Algorithm:
     - Check perfect scenario of platform and id
       ("platform", "id")
     - Search by name (pro players from RLCS only)
       Only if platform matches or platform wasn't specified
     - Check Steam URL ID (Steam is specified)
       Could be SteamID(64) or custom URL ID
     - Check for ID without platform
       User may have entered appropriate ID but missed platform
     - Search by name (pro replays only)
       Only if platform matches or platform wasn't specified
     - Search by name (any replays)
       Only if platform was specified, and only accept matching platform
     - Check Steam URL ID (platform is unspecified)
       Only custom URL ID as SteamID(64) would have been found already
     - Complete wildcard search
       Search by name, without any limitations
       This should pick up all the stragglers.
    '''
    
    # Search by player_id (platform:id)
    platform_player_id = account_id[0] + ":" + account_id[1]
    replays = list(api.get_replays(player_id=platform_player_id, sort_by="replay-date", deep=False, count=1))
    if len(replays) == 1:
        return platform_player_id
    
    # Search by name (PRO) FROM RLCS REFEREE
    replays = list(api.get_replays(player_name=f'"{account_id[1]}"', uploader="76561199225615730", sort_by="replay-date", deep=False, count=1, pro="true"))
    if len(replays) == 1:
        replay = replays[0]
        for player in replay['blue']['players']: # blue
            if player is None: continue
            if (player['name'] == account_id[1] and
            (player['id']['platform'] == account_id[0] or
            "any" == account_id[0]) and
            "player_number" not in player['id']): # Make sure to ignore splitscreen
                platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                return platform_player_id
        for player in replay['orange']['players']: # orange
            if player is None: continue
            if (player['name'] == account_id[1] and
            (player['id']['platform'] == account_id[0] or
            "any" == account_id[0]) and
            "player_number" not in player['id']): # Make sure to ignore splitscreen
                platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                return platform_player_id
    
    # If steam url
    if account_id[0] == "steam":
        # Search by Steam (we know it's a Steam account)
        platform_player_id = search_by_steam(account_id[1])
        if platform_player_id is not None: return platform_player_id
        
    # Search by id (w/o platform)
    if account_id[0] == "any":
        for platform in data.PLATFORMS:
            platform_player_id = platform + ":" + account_id[1]
            replays = list(api.get_replays(player_id=platform_player_id, sort_by="replay-date", deep=False, count=1))
            if len(replays) == 1 and platform != "ps4":
                return platform_player_id

    # Search by name (PRO)
    replays = list(api.get_replays(player_name=f'"{account_id[1]}"', sort_by="replay-date", deep=False, count=1, pro="true"))
    if len(replays) == 1:
        replay = replays[0]
        for player in replay['blue']['players']: # blue
            if player is None: continue
            if (player['name'] == account_id[1] and
            (player['id']['platform'] == account_id[0] or
            "any" == account_id[0]) and
            "player_number" not in player['id']): # Make sure to ignore splitscreen
                platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                return platform_player_id
        for player in replay['orange']['players']: # orange
            if player is None: continue
            if (player['name'] == account_id[1] and
            (player['id']['platform'] == account_id[0] or
            "any" == account_id[0]) and
            "player_number" not in player['id']): # Make sure to ignore splitscreen
                platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                return platform_player_id

    # Search by name (non PRO) (specific platform)
    if account_id[0] != "any":
        replays = list(api.get_replays(player_name=f'"{account_id[1]}"', sort_by="replay-date", deep=False, count=1))
        if len(replays) == 1:
            replay = replays[0]
            for player in replay['blue']['players']: # blue
                if player is None: continue
                if (player['name'] == account_id[1] and
                player['id']['platform'] == account_id[0] and
                "player_number" not in player['id']): # Make sure to ignore splitscreen
                    platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                    return platform_player_id
            for player in replay['orange']['players']: # orange
                if player is None: continue
                if (player['name'] == account_id[1] and
                player['id']['platform'] == account_id[0] and
                "player_number" not in player['id']): # Make sure to ignore splitscreen
                    platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                    return platform_player_id
    
    # Search by Steam (we don't know if it's a Steam account)
    platform_player_id = search_by_steam(account_id[1])
    if platform_player_id is not None: return platform_player_id
    
    # Search by name (non PRO) ("any" platform)
    replays = list(api.get_replays(player_name=f'"{account_id[1]}"', sort_by="replay-date", deep=False, count=1))
    if len(replays) == 1:
        replay = replays[0]
        for player in replay['blue']['players']: # blue
            if player is None: continue
            if (player['name'] == account_id[1] and
            "player_number" not in player['id']): # Make sure to ignore splitscreen
                platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                return platform_player_id
        for player in replay['orange']['players']: # orange
            if player is None: continue
            if (player['name'] == account_id[1] and
            "player_number" not in player['id']): # Make sure to ignore splitscreen
                platform_player_id = player['id']['platform'] + ":" + player['id']['id']
                return platform_player_id

    # No player found
    return None

# Steam search
def search_by_steam(steam_id):
    '''
    @param
     - steam_id : Target's Steam name or id

    @return
     - String : Target's "platform:id" pair
    '''
    
    #steam_api_request = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={data.TOKEN_STEAM}&steamids={steam_id}"
    steam_api_request = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={data.TOKEN_STEAM}&vanityurl={steam_id}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    page = requests.get(steam_api_request, headers=headers)
    
    # Page found
    if page.status_code == 200:
        # Parse the json response
        _json = page.json()
        
        try:
            steam_id = _json['response']['steamid']
            
            # Generate "platform:id" pair
            platform_player_id = "steam:" + steam_id
            return platform_player_id
        except KeyError:
            return None
    return None

# Get a player object by id (steam:76561198438198955)
def get_player_object(platform_player_id):
    '''
    @param
     - platform_player_id : Target's "platform:id" pair

    @return
     - Dictionary : Target's replay information

    Now that we know the platform:id pair, we can guarantee
    finding the player on ballchasing.com

    We need the player object because it contains the relevant
    information about the player:
     - player name
     - camera settings
     - steering sensitivity
     - last used car

    This time when we search replays, we are going to grab all
    the information about the replay by using the "deep=True"
    parameter in the ballchasing API. This is less efficient
    but some of the information we require is only available
    like this.

    Note: This function is used independently in the database file.
    '''

    # Make sure we have player id
    if platform_player_id is None: return None, None
    player_object = None
    replay = None
    
    # Get the player's latest replay (using deep=True to get all stats)
    replays = list(api.get_replays(player_id=platform_player_id, playlist=data.REPLAY_PLAYLIST, sort_by="replay-date", deep=True, count=1))
    if replays == None or replays == [] or len(replays) == 0:
        return None, None
    replay = replays[0]
    
    # Find player in the replay
    for player in replay['blue']['players']: # blue
        if player is None: continue
        if str(player['id']['platform'] + ":" + player['id']['id']) == platform_player_id \
        and "player_number" not in player['id']: # Make sure to ignore splitscreen
            player_object = player
            break
    if player_object is None:
        for player in replay['orange']['players']: # orange
            if player is None: continue
            if str(player['id']['platform'] + ":" + player['id']['id']) == platform_player_id \
            and "player_number" not in player['id']: # Make sure to ignore splitscreen
                player_object = player
                break
    
    # Return player object
    return player_object, replay["date"].split("T")[0]
    

# Scrape data from ballchasing.com
def scrape_ballchasing(platform_player_id):
    '''
    @param
     - platform_player_id : Target's "platform:id" pair

    @return
     - Dictionary : Target's ballchasing profile information
    
    Web scraping the designated profile in order to get
    relevant stats about them:
     - Aliases
     - Friends
     - Car Preferences
     - Liquipedia Presence
     - etc.
    '''
    
    if platform_player_id == None: return None

    # Request the ballchasing profile
    platform, player_id = platform_player_id.split(":")
    ballchasing_url = "https://ballchasing.com/player/{}/{}".format(platform, player_id)
    page = requests.get(ballchasing_url)
    if page.status_code != 200: return None

    # Set up parser
    soup = bs4.BeautifulSoup(page.content[:200000], 'html.parser')
    nameclass = soup.find('h2', class_="title")
    aliasclass = soup.find('p', class_="is-4")
    replaystatsclass = soup.find_all('p', class_="subtitle is-4")

    # Get player name
    name = nameclass.get_text().strip()
    name = name.splitlines()[0]

    # Set up friends / car parser
    dualclass = soup.find_all('ul', class_="mates")
    carclass = None
    matesclass = None
    if len(dualclass) > 0:
        carclass = dualclass[0]
    if len(dualclass) > 1:
        matesclass = dualclass[1]

    # Get aliases
    init_aliases = aliasclass.find_all('strong')
    aliases = []
    aliasclass = str(aliasclass)
    if aliasclass.find("Also played as:") != -1:
        for i in range(0, len(init_aliases)):
            aname = init_aliases[i].get_text()
            aliases.append(aname)
    else:
        aliases.append("Not Applicable")

    # Format the aliases text
    aliastext = ""
    if aliases == None or aliases == [] or len(aliases) == 0:
        aliases = []
        aliases.append("Not Applicable")
    else:
        for i in range(0, len(aliases) - 1):
            if aliases[i] not in data.BOT_NAMES: aliastext = aliastext + aliases[i] + ", "
    if aliases[-1] not in data.BOT_NAMES: aliastext = aliastext + aliases[-1]
    if aliastext == "": aliastext = "Not Applicable"

    # Get friends
    mates = []
    if matesclass != None:
        init_mates = matesclass.find_all('li', class_='mate')
        mates = []
        for i in range(0, len(init_mates)):
            text = init_mates[i].get_text().strip()
            n = text.splitlines()[0]
            if text.find("PRO") != -1:
                n = n + ":PRO"
            else:
                n = n + ":NOT"
            mates.append(n)
    else:
        mates.append("Not Applicable")

    # Format the friends text
    matestext = ""
    mname = "null"
    mpro = ""
    if len(mates) > 1:
        for i in range(0, len(mates) - 1):
            mpro = ""
            mname = mates[i].rsplit(":", 1)
            if mname[-1] == "PRO":
                mpro = " ⭐"
            matestext = matestext + mname[0] + mpro + ", "
        mpro = ""
    if mates[0] != "Not Applicable":
        mname = mates[-1].rsplit(":", 1)
        if mname[-1] == "PRO":
            mpro = " ⭐"
        matestext = matestext + mname[0] + mpro
    else:
        matestext = matestext + mates[0] + mpro

    # Create a dictionary to store the replay related stats
    replaystats = {}
    
    # Is the target an uploader?
    replays = api.get_replays(uploader=player_id, sort_by="replay-date", deep=False, count=1)
    replaystats["uploader"] = False
    for replay in replays:
        replaystats["uploader"] = True
    
    # Appearances
    for x in replaystatsclass:
        appears = x.get_text().strip().splitlines()
        if appears[0].find("Appears") != -1:
            appears_initial = appears[0] + " " + appears[-1]
            appears_initial = appears_initial.split(" ")
            appears_initial[2] = "**{}**".format(appears_initial[2])
            replaystats["appears"] = " ".join(appears_initial)
    
    # Cars
    cars = {}
    if carclass != None:
        init_cars = carclass.find_all('strong')
        init_pcnts = carclass.find_all('span')
        for i in range(0, len(init_cars)):
            cars[init_cars[i].get_text()] = round((float(init_pcnts[i].get_text().strip().removesuffix("%")) / 100.0), 4)
    replaystats["cars"] = cars

    # Get Liquipedia if applicable
    liquipedia_url = "~~Liquipedia~~"
    isPro = False
    for link in soup.find_all('a'):
        link_href = link.get('href')
        if link_href is not None and link_href.find("liquipedia") != -1:
            liquipedia_url = link_href.removesuffix("/")
            isPro = True

    # Get the target's tracker link
    tracker_url = "Not Applicable"
    if platform == "epic":
        tracker_url = "https://rocketleague.tracker.network/rocket-league/profile/{}/{}".format(platform, name.replace(" ", "%20"))
    elif platform == "xbox":
        tracker_url = "https://rocketleague.tracker.network/rocket-league/profile/xbl/{}".format(name.replace(" ", "%20"))
    elif platform == "ps4":
        tracker_url = "https://rocketleague.tracker.network/rocket-league/profile/psn/{}".format(player_id)
    else:
        tracker_url = "https://rocketleague.tracker.network/rocket-league/profile/{}/{}".format(platform, player_id)

    # Get the target's Steam link if applicable
    steam_url = "~~Steam~~"
    avatar_url = ""
    if platform == "steam":

        steam_api_request = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={data.TOKEN_STEAM}&steamids={player_id}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        page = requests.get(steam_api_request, headers=headers)
        
        # Page found
        if page.status_code == 200:
            # Parse the json response
            _json = page.json()
            try:
                steam_url = _json['response']['players'][0]['profileurl'].removesuffix("/")
                avatar_url = _json['response']['players'][0]['avatarfull']
                
            except KeyError:
                pass
    
    # Put all the scraped data into a dictionary
    player_information = {}
    player_information['AccountID'] = player_id
    player_information['Platform'] = platform
    player_information['Pro'] = isPro
    player_information['Ballchasing'] = ballchasing_url
    player_information['Tracker'] = tracker_url
    player_information['Steam'] = steam_url
    player_information['Liquipedia'] = liquipedia_url
    player_information['Avatar'] = avatar_url
    
    player_information['Aliases'] = aliastext[:1000]
    player_information['Friends'] = matestext[:1000]
    
    player_information['Uploader'] = replaystats['uploader']
    player_information['Appearances'] = replaystats['appears']
    player_information['Cars'] = replaystats['cars']
    
    return player_information

