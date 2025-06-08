''' 
Author: Kian Mortimer
Date: 18/05/25

Description:
Data such as guilds, users and colours.
'''

# IMPORTS
import discord

# PREFIX
PREFIX = "." # Only applies to non-slash commands

# USERS
DEVELOPERS = [
    "Redacted"
]
ADMINS = [
    "Redacted"
]
BLACKLIST = [
    ""
]

# GUILDS
GUILDS = [
    "Redacted",
    "Redacted",
    "Redacted",
]

# COLOURS
WHITE = 16777215
RED = 16711680
ORANGE = 16759040
YELLOW = 16776960
GREEN = 65280
BLUE = 41215

# EMOJIS
EMOJI_TYPE_PRO = "<:playerpro:1373632063663771648>"
EMOJI_TYPE_MAIN = "<:playermain:1373631979559321640>"
EMOJI_TYPE_ALT = "<:playeralt:1373632027391295500>"
EMOJI_COUNT = ["0️⃣","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣", "9️⃣", "🔟"]

# MISCELLANEOUS
BOT_FOOTER_TEXT = "Powered by the blood of Balls I"

# STATUSES / ACTIVITIES
ACTIVITY = {
    "Omniscience": {
        "Status": discord.Status.online, # Online
        "Name": "Omniscience",
        "Type": 5, # Competing
        "State": "The Quest for the Golden Balls™"
    },
    "Error": {
        "Status": discord.Status.idle, # Idle
        "Name": "404 Not Found",
        "Type": 4, # Custom
        "State": "The balls have broken..."
    },
    "Thinking": {
        "Status": discord.Status.dnd, # Do Not Disturb
        "Name": "Calculating... 🤓",
        "Type": 1, # Streaming
        "State": "Using a calc (\"calc\" is short for calculator)"
    },
    "RLPlay": {
        "Status": discord.Status.online, # Online
        "Name": "Rocket League",
        "Type": 0, # Playing
        "State": "InGame 1:1 [Overtime 1:33]"
    },
    "RLStream": {
        "Status": discord.Status.online, # Online
        "Name": "Rocket League",
        "Type": 1, # Streaming
        "State": "InGame 1:1 [Overtime 1:33]"
    },
    "RLWatch": {
        "Status": discord.Status.online, # Online
        "Name": "Rocket League",
        "Type": 3, # Watching
        "State": "Monitoring your poor performance..."
    },
    "RLCS": {
        "Status": discord.Status.dnd, # Do Not Disturb
        "Name": "RLCS 2025",
        "Type": 5, # Competing
        "State": "InGame 2:1 [Overtime 1:33]"
    },
    "GoldenBalls": {
        "Status": discord.Status.idle, # Idle
        "Name": "Seeking the Golden Balls™",
        "Type": 4, # Custom
        "State": "Seeking the Golden Balls™"
    }
}
DEFAULT_ACTIVITY = ACTIVITY['RLPlay']


# BALLCHASING
REPLAY_PLAYLIST = [
    "ranked-duels", "ranked-doubles", "ranked-standard"
]
REPLAY_PLAYLIST_EXTRAS = [
    "ranked-duels", "ranked-doubles", "ranked-standard", "ranked-snowday", "ranked-hoops", "ranked-rumble", "ranked-dropshot"
]
PLATFORMS = [
    "steam", "epic", "xbox", "ps4"
]

BOT_NAMES = [
    "Armstrong",
    "Bandit",
    "Beast",
    "Boomer",
    "Buzz",
    "C-Block",
    "Casper",
    "Caveman",
    "Centice",
    "Chipper",
    "Cougar",
    "Dude",
    "Foamer",
    "Fury",
    "Gerwin",
    "Goose",
    "Heater",
    "Hollywood",
    "Hound",
    "Iceman",
    "Imp",
    "Jester",
    "Junker",
    "Khan",
    "Marley",
    "Maverick",
    "Merlin",
    "Middy",
    "Mountain",
    "Myrtle",
    "Outlaw",
    "Poncho",
    "Rainmaker",
    "Raja",
    "Rex",
    "Roundhouse",
    "Sabretooth",
    "Saltie",
    "Samara",
    "Scout",
    "Shepard",
    "Slider",
    "Squall",
    "Sticks",
    "Stinger",
    "Storm",
    "Sultan",
    "Sundown",
    "Swabbie",
    "Tex",
    "Tusk",
    "Viper",
    "Wolfman",
    "Yuri",
    "Sundow",
    "Player 0",
    "Player 1",
    "Player 2",
    "Player 3",
    "Player 4",
    "Player 5"
]
