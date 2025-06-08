'''
Author: Kian Mortimer
Date: 18/05/25

Description:
Contains all the functionality associated with Rocket League
'''

# IMPORTS
import ballchasing
import re
import os
import requests
import discord
from datetime import datetime
import pytz

# MY IMPORTS
import config
import actions

class Player():
    '''
    Represents the target player of the search
    Contains statistics pertaining to their identification and replay history
    '''
    def __init__(self, target: str) -> None:
        # Populated from construction
        self.target: str = target.strip()
        self.ballchasing_api = ballchasing.Api(os.getenv('TOKEN_BALLCHASING'))

        # Player information
        self.player_platform_id: str = None # The key player identifier (platform:id)
        self.platform: str = None           # The platform of the player -> Retrieved from platform_player_id
        self.player_id: str = None          # The id of the player -> Retrieved from platform_player_id
        self.replay_object: dict = {}       # Deep replay for camera settings and other
        self.links: dict = {}               # Relevant links (Steam, Ballchasing...)
        self.is_uploader: bool = False      # Does the account upload replays?

        # Player stats
        self.replay_count: int = 0          # Number of replays excluding duplicates
        self.names_time: dict = {}          # dict: {asc(timestamp): playername}
        self.names_count: dict = {}         # dict: {playername: desc(count)}
        self.is_pro: bool = False           # Is the player listed as a pro?
        # Team stats
        self.team_names_raw: dict = {}      # dict: {teamid: [names]}
        self.team_names: dict = {}          # dict: {teamid: name}
        self.team_count: dict = {}          # dict: {teamid: desc(count)}
        self.team_pro: dict = {}            # dict: {teamid: isPro}
        # Opponent stats
        self.opp_names_raw: dict = {}       # dict: {oppid: [names]}
        self.opp_names: dict = {}           # dict: {oppid: name}
        self.opp_count: dict = {}           # dict: {oppid: desc(count)}
        self.opp_pro: dict = {}             # dict: {oppid: isPro}
        
    ''' Identify player from the target string '''
    def locate_target(self) -> bool:
        '''
        The purpose is to confirm a platform and id of the target.
        This can be achieved by first defining the search term for
        ballchasing.com using regex, and then running through a
        sequence of replay searches where the more specific search terms
        get applied first.
        '''

        # Helper function for this method
        def steam_get_id_from_vanity(vanity: str) -> str | None:
    
            steam_api_request = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={os.getenv('TOKEN_STEAM')}&vanityurl={vanity}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
            page = requests.get(steam_api_request, headers=headers)
            
            # Page found
            if page.status_code == 200:
                # Parse the json response
                _json = page.json()
                
                try:
                    return _json['response']['steamid']
                except KeyError:
                    return None
            return None
        
        # Helper function for this method
        def replay_check_teams_for_player(mode: int, replay: dict, account_id: tuple) -> str:
            def condition(mode: int, actual_platform: str, test_platform: str):
                match mode:
                    case 0:
                        return True
                    case 1:
                        return (actual_platform == test_platform or 
                                "any" == test_platform)
                    case 2:
                        return (actual_platform == test_platform)
            
            def check_team(colour: str) -> str:
                for player in replay[colour]['players']: # blue
                    if player is None: continue
                    if (player['name'] == account_id[1] and
                    (condition(mode, player['id']['platform'], account_id[0])) and
                    "player_number" not in player['id']): # Make sure to ignore splitscreen
                        return player['id']['platform'] + ":" + player['id']['id']
                return None
            
            platform_player_id = check_team("blue")
            if platform_player_id is None:
                platform_player_id = check_team("orange")
            return platform_player_id

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

        '''

        # Set up account id tuple
        account_id = ("", "")
        # Check for steam url
        if re.match("^.*((id)|(profiles))/[a-zA-Z0-9_-]{1,50}/*$", self.target) is not None:
            link = self.target.replace("/", " ").strip()
            split_link = link.split(" ")
            account_id = ("steam", split_link[-1])
        # Check for "platform?id" where ? is [: /]
        elif re.match("^[a-zA-Z4]{3,5}[: /][a-zA-Z0-9_-]{1,50}$", self.target) is not None:
            account_id = tuple(re.split("[: /]", self.target, 1))
        # Check for ballchasing url
        elif re.match("^.*/[a-z4]{3,5}/[a-zA-Z0-9_-]{1,50}/*$", self.target) is not None:
            link = self.target.replace("/", " ").strip()
            split_link = link.split(" ")
            account_id = (split_link[-2], split_link[-1])
        # Check for steam id
        elif re.match("^7656[0-9]{13}$", self.target) is not None:
            account_id = ("steam", self.target)
        # Check for "platform?name" where ? is [: /]
        elif re.match("^[a-zA-Z4]{3,5}[: /].{1,50}$", self.target) is not None:
            account_id = tuple(re.split("[: /]", self.target, 1))
        # Check for other
        elif re.match("^.{1,50}$", self.target) is not None:
            account_id = ("any", self.target)
        # Does not match expected
        else:
            return False

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
        self.platform_player_id = account_id[0] + ":" + account_id[1]
        print("   - 1: " + self.platform_player_id)
        try:
            next(self.ballchasing_api.get_replays(player_id=self.platform_player_id, sort_by="replay-date", deep=False, count=1))
            self.platform, self.player_id = self.platform_player_id.split(":")
            return True
        except StopIteration: # does not appear in any replays
            pass

        # Search by name (PRO) FROM RLCS REFEREE
        try:    
            replay = next(self.ballchasing_api.get_replays(player_name=f'"{account_id[1]}"', uploader="76561199225615730", sort_by="replay-date", deep=False, count=1, pro="true"))
            self.platform_player_id = replay_check_teams_for_player(1, replay, account_id)
            print("   - 2: " + self.platform_player_id)
            self.platform, self.player_id = self.platform_player_id.split(":")
            return True
        except StopIteration: # does not appear in any replays
            pass

        
        # If steam url
        if account_id[0] == "steam":
            # Search by Steam (we know it's a Steam account)
            if (steam_id := steam_get_id_from_vanity(account_id[1])) is not None:
                self.platform_player_id = "steam:" + steam_id
                print("   - 3: " + self.platform_player_id)
                self.platform, self.player_id = self.platform_player_id.split(":")
                return True
            
        # Search by id (w/o platform)
        if account_id[0] == "any":
            for platform in config.PLATFORMS:
                self.platform_player_id = platform + ":" + account_id[1]
                print("   - 4: " + self.platform_player_id)
                try:
                    replay = next(self.ballchasing_api.get_replays(player_id=self.platform_player_id, sort_by="replay-date", deep=False, count=1))
                    if platform != "ps4":
                        print("   - 5: " + self.platform_player_id)
                        self.platform, self.player_id = self.platform_player_id.split(":")
                        return True
                except StopIteration: # does not appear in any replays
                    pass

        # Search by name (PRO)
        try:
            replay = next(self.ballchasing_api.get_replays(player_name=f'"{account_id[1]}"', sort_by="replay-date", deep=False, count=1, pro="true"))
            self.platform_player_id = replay_check_teams_for_player(1, replay, account_id)
            print("   - 6: " + str(self.platform_player_id))
            self.platform, self.player_id = self.platform_player_id.split(":")
            return True
        except StopIteration: # does not appear in any replays
            pass

        # Search by name (non PRO) (specific platform)
        if account_id[0] != "any":
            try:    
                replay = next(self.ballchasing_api.get_replays(player_name=f'"{account_id[1]}"', sort_by="replay-date", deep=False, count=1))
                self.platform_player_id = replay_check_teams_for_player(2, replay, account_id)
                print("   - 7: " + str(self.platform_player_id))
                self.platform, self.player_id = self.platform_player_id.split(":")
                return True
            except StopIteration: # does not appear in any replays
                pass

        # Search by Steam (we don't know if it's a Steam account)
        if (steam_id := steam_get_id_from_vanity(account_id[1])) is not None:
            try:
                next(self.ballchasing_api.get_replays(player_name=f'"steam:{steam_id}"', sort_by="replay-date", deep=False, count=1))
                self.platform_player_id = "steam:" + steam_id
                print("   - 8: " + self.platform_player_id)
                self.platform, self.player_id = self.platform_player_id.split(":")
                return True
            except StopIteration:
                pass

        # Search by name (non PRO) ("any" platform)
        try:
            replay = next(self.ballchasing_api.get_replays(player_name=f'"{account_id[1]}"', sort_by="replay-date", deep=False, count=1))
            self.platform_player_id = replay_check_teams_for_player(0, replay, account_id)
            print("   - 9: " + str(self.platform_player_id))
            self.platform, self.player_id = self.platform_player_id.split(":")
            return True
        except StopIteration: # does not appear in any replays
            pass

        # No player found
        print("   - 10: " + str(self.platform_player_id))
        self.platform_player_id = None
        print("   - final: " + str(self.platform_player_id))
        return False

    ''' Get a player object by id (steam:76561198438198955) '''
    def update_replay_object(self):
        '''
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
        '''
        
        # Get the player's latest replay (using deep=True to get all stats)
        replay = next(self.ballchasing_api.get_replays(player_id=self.platform_player_id, playlist=config.REPLAY_PLAYLIST, sort_by="replay-date", deep=True, count=1))
        # We are not concerned with StopIteration error, as we know there will be a replay if we got this far
        
        # Find player in the replay
        target_player = None
        for player in replay['blue']['players']: # blue
            if player is None: continue
            if str(player['id']['platform'] + ":" + player['id']['id']) == self.platform_player_id \
            and "player_number" not in player['id']: # Make sure to ignore splitscreen
                target_player = player
                break
        if target_player is None:
            for player in replay['orange']['players']: # orange
                if player is None: continue
                if str(player['id']['platform'] + ":" + player['id']['id']) == self.platform_player_id \
                and "player_number" not in player['id']: # Make sure to ignore splitscreen
                    target_player = player
                    break
        target_player["replaydate"] = replay["date"].split("T")[0]
        self.replay_object = target_player

    ''' Update the relevant links (steam, ballchasing...) '''
    def update_links(self):
        ballchasing_url = "https://ballchasing.com/player/{}/{}".format(self.platform, self.player_id)

        # Get the target's Steam link if applicable
        steam_url = "~~Steam~~"
        avatar_url = ""
        if self.platform == "steam":

            steam_api_request = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={os.getenv('TOKEN_STEAM')}&steamids={self.player_id}"
            
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
        self.links.update({"Ballchasing": ballchasing_url,
                "Steam": steam_url,
                "Avatar": avatar_url})

    ''' Check whether the player uploads replays to ballchasing.com '''
    def update_uploader(self):
        try:
            player_id = int(self.player_id) # Throws a ValueError if the user is not on Steam
            next(self.ballchasing_api.get_replays(uploader=player_id, sort_by="replay-date", deep=False, count=1)) # throws a StopIteration error if there are no items in the generator
            self.is_uploader = True
        except (ValueError, StopIteration): # User is not a uploader
            self.is_uploader = False

    ''' Retrieve deep stats from all the replays that the target appears in '''
    def update_history(self):
        ''' Helper function defining how to parse the teams in a replay object '''
        def iter_teams(replay, colour):
            is_player_team = False
            team_members = [] # List of players in this team

            try:
                # Loop through the players in this team
                for player in (replay[colour]['players']):
                        try:
                            # Add the relevant player information to the team_members list
                            team_members.append((f"{player['id']['platform']}:{player['id']['id']}", player['name'], True if "pro" in player.keys() else False))

                            if player['id']['id'] == self.player_id:
                                ''' Perform actions on TARGET '''
                                self.names_time[replay['date']] = player['name']

                                # Is the target a pro, or listed as a pro already?
                                if not self.is_pro: self.is_pro = True if "pro" in player.keys() else False
                                ''' End actions on TARGET '''

                                # Set the flag to confirm that we are currently looping through the target's team
                                is_player_team = True
                                continue

                        except KeyError:
                            ''' Occasionally, a ghost player exists in a replay that does not appear in the team, 
                            but does make the "team size" greater - often if someone spectates or changes team '''
                            continue
            except KeyError:
                ''' In rare instances, there are no players present on a team
                We need to make sure the code just skips along if this happens '''
                return

            
            if is_player_team:
                ''' Perform actions on TEAM '''
                # Loop back through the players
                for i in range(0, len(replay[colour]['players'])):
                    try:
                        # Skip the target player since they aren't their own teammate
                        if team_members[i][0] == self.platform_player_id: continue

                        # Initialise an empty list in case this is the player's first appearance
                        name_list = []
                        # Check whether the player is a pro (1) from this iteration
                        pro = True if team_members[i][2] else False

                        # Check whether the player has appeared in previous iterations
                        if team_members[i][0] in self.team_names_raw.keys():
                            # Add the player's name to their list of other names (duplicates allowed)
                            name_list = self.team_names_raw[team_members[i][0]]
                            # Check whether player is a pro (2) from previous iterations
                            pro = True if pro or self.team_pro[team_members[i][0]] else False
                        
                        # Update the master lists of teammates to include the player's current appearance
                        self.team_names_raw[team_members[i][0]] = name_list + [team_members[i][1]]
                        self.team_pro[team_members[i][0]] = pro

                    except (KeyError, IndexError):
                        ''' Occasionally, a ghost player exists in a replay that does not appear in the team, 
                        but does make the "team size" greater - often if someone spectates or changes team '''
                        continue
                ''' End actions on TEAM '''

            else:
                ''' Perform actions on OPPOSITION '''
                # Loop back through the players
                for i in range(0, len(replay[colour]['players'])):
                    try:
                        # Initialise an empty list in case this is the player's first appearance
                        name_list = []
                        # Check whether the player is a pro (1) from this iteration
                        pro = True if team_members[i][2] else False

                        # Check whether the player has appeared in previous iterations
                        if team_members[i][0] in self.opp_names_raw.keys():
                            # Add the player's name to their list of other names (duplicates allowed)
                            name_list = self.opp_names_raw[team_members[i][0]]
                            # Check whether player is a pro (2) from previous iterations
                            pro = True if pro or self.opp_pro[team_members[i][0]] else False
                        
                        # Update the master lists of teammates to include the player's current appearance
                        self.opp_names_raw[team_members[i][0]] = name_list + [team_members[i][1]]
                        self.opp_pro[team_members[i][0]] = pro

                    except IndexError:
                        ''' Occasionally, a ghost player exists in a replay that does not appear in the team, 
                        but does make the "team size" greater - often if someone spectates or changes team '''
                        continue
                ''' End actions on OPPOSITION '''
                pass
        
        ''' Helper function to format the timestamps present in replays and check for duplicates '''
        def is_same_time(x, y) -> bool:
            # First replay gets caught here, other errors will be caught too
            if x is None or y is None:
                return False
            
            # Some replays are formatted with a "Z" on the end and datetime module doesn't like that
            x = x.removesuffix("Z")
            y = y.removesuffix("Z")

            # Set the default timezone (Most OCE are in Melbourne timezone)
            tz = pytz.timezone("Australia/Melbourne")

            # Convert string to datetime object for calculations
            x = datetime.fromisoformat(x)
            y = datetime.fromisoformat(y)

            # Check if timezone info needs to be added and add it
            if x.tzinfo is None or x.tzinfo.utcoffset(x) is None:
                x = tz.localize(x)
            if y.tzinfo is None or y.tzinfo.utcoffset(y) is None:
                y = tz.localize(y)

            # How close together replays have to be to be considered duplicates
            # We would use the match GUID, but the simple search we're using from ballchasing doesn't include that
            # and a deep search would take 20x as long
            allowance = 60 # seconds

            try:
                # Check if the times are within the allowance
                if abs((x-y).total_seconds()) < allowance:
                    return True # The replays have been determined to be the same match: skip this replay
            except TypeError:
                ''' Catches instances where either date is in an invalid format '''
                pass
            
            # The replays have been determined to be separate matches: continue as normal
            return False
        
        # Get replays from ballchasing.com - returns a generator
        replays = self.ballchasing_api.get_replays(player_id=self.platform_player_id, deep=False, count=50000) # count can be unlimited
        
        # If it's the first replay, there isn't a last replay date
        last_replay_date = None

        try:
            for replay in replays:
                # Use helper func to determine whether current replay is the same match as the previous replay
                if is_same_time(last_replay_date, replay['date']): continue
                # Set the last replay date to this replay's date for next iteration
                last_replay_date = replay['date']

                # Print a value every 1000 replays for monitoring purposes
                if self.replay_count % 1000 == 0: print(f"   - {self.replay_count}: {replay['date']}")
                self.replay_count += 1

                # Use helper func to iterate through the blue and orange team, getting relevant stats
                iter_teams(replay, "blue")
                iter_teams(replay, "orange")

        except StopIteration:
            ''' If generator object runs out of values, catch it here '''
            print(f"   - {self.replay_count}") # Total replays parsed
            pass
        
        # Data transformations to develop stats profile from raw data

        '''{date: name}         =>      {asc(date): name} 
        names_time = {          =>      names_time = {
            "date2": "name1",                "date1": "name1",
            "date1": "name1",                "date2": "name1",
            "date3": "name2",                "date3": "name2",
            "date4": "name3"                 "date4"...
        }                               }'''
        self.names_time = dict(sorted(self.names_time.items(), key=lambda i: i, reverse=False))

        '''{date: name}         =>      {name: count(names)}    =>      {name: desc(count(names))}
        names_time = {          =>      names_count = {                 names_count = {
            "date": "name2",                "name1": "1",                   "name2": "2",
            "date": "name1",                "name2": "2",                   "name1": "1",
            "date": "name2",                "name3": "1",                   "name3": "1",
            "date": "name3"                 "name4": ...                    "name4": ...
        }                               }                               }'''
        # Middle is defined as = {i: list(self.names_time.values()).count(i) for i in self.names_time.values()}
        self.names_count = dict(sorted( {i: list(self.names_time.values()).count(i) for i in self.names_time.values()}.items(), key=lambda i: i[1], reverse=True))

        '''{id: [names]}                    =>      {id: popular(name)}
        team_names_raw = {                  =>      team_names = {
            "id": "[name1, name2, ...]",                "id": "name1",
            "id": "[name1, name2, ...]",                "id": "name5",
            "id": "[name1, name2, ...]",                "id": "name2",
            "id": "[name1, name2, ...]"                 "id": ...
        }                                           }'''
        self.team_names = { i: max(set(self.team_names_raw[i]), key=list(self.team_names_raw[i]).count) for i in self.team_names_raw.keys()}

        '''{id: [names]}                    =>      {id: count(names)}      =>      {id: desc(count(names))}
        team_names = {                      =>      middle = {              =>     team_count = {
            "id": "[name1, name2, ...]",                "id": "10",                     "id": "13",
            "id": "[name1, name2, ...]",                "id": "6",                      "id": "10",
            "id": "[name1, name2, ...]",                "id": "13",                     "id": "6",
            "id": "[name1, name2, ...]"                 "id": ...                       "id": ...
        }                                           }                               }'''
        # Middle is defined as = {i: len(list(self.team_names[i])) for i in self.team_names.keys()}
        self.team_count = dict(sorted( {i: len(list(self.team_names_raw[i])) for i in self.team_names_raw.keys()}.items(), key=lambda i: i[1], reverse=True))

        '''{id: [names]}                    =>      {id: popular(name)}
        opp_names_raw = {                   =>      opp_names = {
            "id": "[name1, name2, ...]",                "id": "name1",
            "id": "[name1, name2, ...]",                "id": "name5",
            "id": "[name1, name2, ...]",                "id": "name2",
            "id": "[name1, name2, ...]"                 "id": ...
        }                                           }'''
        self.opp_names = { i: max(set(self.opp_names_raw[i]), key=list(self.opp_names_raw[i]).count) for i in self.opp_names_raw.keys()}

        '''{id: [names]}                    =>      {id: count(names)}      =>      {id: desc(count(names))}
        opp_names = {                       =>      middle = {              =>     opp_count = {
            "id": "[name1, name2, ...]",                "id": "10",                     "id": "13",
            "id": "[name1, name2, ...]",                "id": "6",                      "id": "10",
            "id": "[name1, name2, ...]",                "id": "13",                     "id": "6",
            "id": "[name1, name2, ...]"                 "id": ...                       "id": ...
        }                                           }                               }'''
        # Middle is defined as = {i: len(list(self.opp_names[i])) for i in self.opp_names.keys()}
        self.opp_count = dict(sorted( {i: len(list(self.opp_names_raw[i])) for i in self.opp_names_raw.keys()}.items(), key=lambda i: i[1], reverse=True))



## Helper functions ##
''' Run the first (shallow) search to get basic info about the player '''
async def run_shallow_search(interaction, target: str = None):
    embed = discord.Embed(
        title="Help",
        description=f"*↓ Help for the command*",
        color=config.ORANGE
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
        text=config.BOT_FOOTER_TEXT
    )
    
    if target is None:
        await interaction.followup.send(embed=embed)
        return None

    player = Player(target)
    located = player.locate_target()
    if not located:
        embed.title = f"\"{target}\" not found."
        embed.color = config.RED
        await interaction.followup.send(embed=embed)
        return None
    player.update_replay_object()
    date = player.replay_object["replaydate"]
    camera = player.replay_object['camera']
    pro = False # Feature to be added during a future Liquipedia update
    player.update_links()
    player.update_uploader()

    # Create the Discord embed using the gathered information
    embed = discord.Embed(
        title=f"{player.replay_object['name']}",
        description=f"{config.EMOJI_TYPE_PRO if pro else ''}```{player.replay_object['id']['platform']}:{player.replay_object['id']['id']}```",
        url=player.links['Ballchasing'],
        color=config.BLUE
    )
    embed.set_thumbnail(
        url=player.links['Avatar'] # Dynamic image only if Steam
    )
    embed.add_field(
        name="**Statistics**",
        value=f"Uploader: `{player.is_uploader}`    Last Used Car: `{player.replay_object['car_name'] if 'car_name' in player.replay_object.keys() else 'Not Applicable'}`    Date: `{date}`",
        inline=False
    )
    embed.add_field(
        name="**Settings**",
        value=f"```📸 {camera['fov']} {camera['distance']} {camera['height']} {camera['pitch']} {camera['stiffness']} {camera['swivel_speed']} {camera['transition_speed']}   ⚙️ {player.replay_object['steering_sensitivity']}```",
        inline=False
    )
    embed.add_field(
        name="**Links**",
        value=f"- {player.links['Steam']}\n- {player.links['Ballchasing']}",
        inline=False
    )
    embed.set_footer(
        text=config.BOT_FOOTER_TEXT
    )
    await interaction.followup.send(embed=embed)

    return player

''' Run the second (deep) search to get the full stats from the player's entire replay history '''
async def run_deep_search(interaction, player: Player):

    # Update the player object to include the deep history
    player.update_history()

    # Format the responses

    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    name_string = "```" + ", ".join(list(player.names_count.keys())[:50]) + "```"
    name_leaderboard = ""
    count = 1
    for name in list(player.names_count.keys())[:3]:
        name_leaderboard = name_leaderboard + f"   {config.EMOJI_COUNT[count]} `{name}` {str(player.names_count[name]).translate(SUB)}"
        count += 1

    team_list = [list(player.team_count.keys())[:5], list(player.team_count.keys())[5:10], list(player.team_count.keys())[10:15]]
    team_string = ["", "", ""]
    for i in range(len(team_list)):
        for platform_player_id in team_list[i]:
            subscript = str(player.team_count[platform_player_id]).translate(SUB)
            platform, player_id = platform_player_id.split(":")
            team_string[i] = team_string[i] + f"[{player.team_names[platform_player_id]}](<https://ballchasing.com/player/{platform}/{player_id}>) {config.EMOJI_TYPE_PRO if player.team_pro[platform_player_id] else ''} {subscript} ,  "
        team_string[i] = team_string[i].removesuffix(" , ")

    opp_list = [list(player.opp_count.keys())[:5], list(player.opp_count.keys())[5:10], list(player.opp_count.keys())[10:15]]
    opp_string = ["", "", ""]
    for i in range(len(opp_list)):
        for platform_player_id in opp_list[i]:
            subscript = str(player.opp_count[platform_player_id]).translate(SUB)
            platform, player_id = platform_player_id.split(":")
            opp_string[i] = opp_string[i] + f"[{player.opp_names[platform_player_id]}](<https://ballchasing.com/player/{platform}/{player_id}>) {config.EMOJI_TYPE_PRO if player.opp_pro[platform_player_id] else ''} {subscript} ,  "
        opp_string[i] = opp_string[i].removesuffix(" , ")

    # Create the Discord embeds using the gathered information

    name_embed = discord.Embed(
        title="",
        description="",
        color=config.BLUE
    )
    name_embed.add_field(
        name=f"**Pro**",
        value=f"`{player.is_pro}` {config.EMOJI_TYPE_PRO if player.is_pro else ''}",
        inline=True
    )
    name_embed.add_field(
        name=f"**Replays**",
        value=f"`{player.replay_count}`",
        inline=True
    )
    name_embed.add_field(
        name=f"**Names**   {name_leaderboard}",
        value=name_string,
        inline=False
    )

    team_embed = discord.Embed(
        title="",
        description="",
        color=config.BLUE
    )
    team_embed.add_field(
        name=f"**Friends**  `{len(list(player.team_count.keys()))}`",
        value=team_string[0],
        inline=False
    )
    team_embed.add_field(
        name="",
        value=team_string[1],
        inline=False
    )
    team_embed.add_field(
        name="",
        value=team_string[2],
        inline=False
    )

    opp_embed = discord.Embed(
        title="",
        description="",
        color=config.BLUE
    )
    opp_embed.add_field(
        name=f"**Opps**  `{len(list(player.opp_count.keys()))}`",
        value=opp_string[0],
        inline=False
    )
    opp_embed.add_field(
        name="",
        value=opp_string[1],
        inline=False
    )
    opp_embed.add_field(
        name="",
        value=opp_string[2],
        inline=False
    )
    opp_embed.set_footer(
        text=f"Details for: {player.replay_object['name']}"
    )

    await interaction.followup.send(embeds=[name_embed, team_embed, opp_embed])

