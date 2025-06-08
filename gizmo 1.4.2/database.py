''' 

Author: Kian Mortimer
Date: 17/12/22

Description:
Interact with the local database.

'''


# IMPORTS
import mysql.connector

import scraping # Only for getting player object for reconditioning

## DATABASE CLASS ##

class Database(object):
    '''
    Class responsible for ALL interaction with the SQL Database
    '''

    def __init__(self):
        self.con = None

    ''' UTILITY '''

    def connect(self):
        '''
        @return
         - Boolean indicating if connection was successful
        '''
        
        try:
            self.con = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="rocket_league"
            )
        except:
            print(" ! Database Offline")
            return False
        return True

    def close(self):
        '''
        It is COMPULSORY to close the connection after use.
        '''
        self.con.close()

    ''' QUERY '''

    def identify(self, player_object):
        '''
        @param
         - player_object : Dictionary of player data from replay

        @return
         - List of relevant information (3 elements)
        '''

        def to_percent(record, player_object):
            '''
            @param
             - record        : Player information from database record
             - player_object : Dictionary of player data from replay

            @return
             - Float representing the camera similarity

            The equation here is completely arbitrary and just an
            interpretation of how to calculate similarity.
            '''

            ''' 
            Start at 0
            for each relevant setting:
                total_percentage += (weight - max(0, abs(setting1 - setting2) * normal_variance))

            Broken down:
            1: abs(setting1 - setting2) 
                Gets the difference between the two values and makes sure its positive
            2: X * normal_variance
                This determines a normal variance for a setting (i.e. 1 is a big variance in terms of fov but not distance)
                Thus with a difference of 1 in fov (109 vs 110) the percentage added to the total will be 10 out of a possible 15
                And a difference of 2 would give 5/15 | 3 would give 0/15 | 4 would give 0/15
            3: max(0, X)
                Makes sure the added percentage is never less than 0
                (There is a bug in here that makes negative similarities possible but it doesnt really matter)
            4: weight - X
                The weight just determines the importance of a setting (i.e. fov is more important than swivel speed etc.)

            What can be improved?
            1: The bug allowing for negative values is just an oversight where I have not specified that the maximum value 
                should be equal to the weight (i.e. min(max(0,X), weight) )
            2: The weight and normal_variance variables are arbitrarily decided on by me
            3: There are certain values that are actually more important than normal
                If the player in question has a steering sensitivity of 1.83 and a player in the database has the 
                same steering sensitivity of 1.83 it makes them way more likely to be the same player. But the same 
                cannot be said for someone with a steering sensitivity of 1.5 as this is far more common.
            4: Some values have too much importance
                People often have random swivel speeds across their accounts because it's an arbitrary setting 
                and with the current formula, this could make someone's similarity go from 100% to 90% and stop 
                them from showing up in the top 4. I do not know what the best solutions for these issues are.
            '''
            
            total_percentage = 0
            total_percentage = total_percentage + (15 - max(0, abs(player_object["camera"]["fov"] - record[5]) / 1 * 5))
            total_percentage = total_percentage + (15 - max(0, abs(player_object["camera"]["distance"] - record[6]) / 10 * 5))
            total_percentage = total_percentage + (15 - max(0, abs(player_object["camera"]["height"] - record[7]) / 10 * 5))
            total_percentage = total_percentage + (15 - max(0, abs(abs(player_object["camera"]["pitch"]) - abs(record[8])) / 1 * 5))
            total_percentage = total_percentage + (10 - max(0, abs(player_object["camera"]["stiffness"] - record[9]) * 10 * 2))
            total_percentage = total_percentage + (10 - max(0, abs(player_object["camera"]["swivel_speed"] - record[10]) * 10 * 1))
            total_percentage = total_percentage + (10 - max(0, abs(player_object["camera"]["transition_speed"] - record[11]) * 10 * 2))
            total_percentage = total_percentage + (10 - max(0, abs(player_object["steering_sensitivity"] - record[12]) * 100 * 0.2))
            return total_percentage
            
        # Create the cursor
        cursor = self.con.cursor()
        identify_results = [None, None]
        flags_player_id = None
        player_original = None

        # First query to see if the player exists in the table
        query_does_player_exist = (
            "SELECT players.Name, accounts.Main, players.ID, players.Original "
            "FROM accounts "
            "INNER JOIN players ON accounts.PlayerID=players.ID "
            f"WHERE accounts.Platform='{player_object['id']['platform']}' "
            f"AND accounts.AccountID='{player_object['id']['id']}'"
        )
        cursor.execute(operation=query_does_player_exist)
        results = cursor.fetchall()
        if len(results) > 0:
            identify_results[0] = results[0][0]
            identify_results[1] = results[0][1]
            flags_player_id = results[0][2]
            player_original = results[0][3]

        # Second query to get flags for the account
        flags = None
        try:
            query_get_flags = (
                "SELECT * FROM flags "
                f"WHERE PlayerID = {flags_player_id}"
            )
            cursor.execute(operation=query_get_flags)
            flags = cursor.fetchall()
            if len(flags) == 0: flags = None
        except:
            pass
        
        # Third query to get all accounts for comparing
        query_all_accounts = (
            "SELECT accounts.*, players.Name, region.Code FROM accounts "
            "INNER JOIN players ON accounts.PlayerID=players.ID "
            "INNER JOIN region ON players.Region=region.ID "
        )
        cursor.execute(operation=query_all_accounts)
        results = cursor.fetchall()

        # Close cursor
        cursor.close()

        if len(results) == 0: return [None, None, None, None, None, None]

        '''
        [2] > AccountID
        [3] > Platform
        [4] > Main
        [5:12] > Camera
        [13] > Date
        [14] > Player
        [15] > Region
        
        for i in range(0,len(results[0])):
            print(f"{i} > {results[0][i]}")
        '''
        
        # Dictionary Creation
        player_dict = {
            results[i][4] == 1 and results[i][14] : results[i] for i in range(0,len(results))
        }

        # Convert to similarity percentages
        player_dict_as_percentages = dict(
            map(lambda item: (
                    item[0], to_percent(item[1], player_object)
                ),
                player_dict.items()
            )
        )
        identify_results.append(player_dict_as_percentages)

        # Sort dictionary by similarity (ASC)
        sorted_keys = sorted(
            player_dict_as_percentages,
            key=player_dict_as_percentages.get
        )
        identify_results.append(sorted_keys)
        identify_results.append(flags)
        identify_results.append(player_original)

        return identify_results
        
    ''' MAINTENANCE '''

    def get(self, player):
        '''
        @param
         - player : String name of player to search

        @return
         - List of matching players
        '''
        if player == None: return None
        player = player.strip()
        cursor = self.con.cursor()

        # Generate the query
        query = (
            "SELECT players.Name, region.Code, players.Original, "
            "accounts.Platform, accounts.AccountID, accounts.Main "
            "FROM players "
            "INNER JOIN region ON players.Region=region.ID "
            "LEFT JOIN accounts ON players.ID=accounts.PlayerID "
            f"WHERE UPPER(players.Name) LIKE UPPER('{player}%') "
            "ORDER BY players.Name ASC, accounts.Main DESC, "
            "accounts.Platform DESC"
        )
        cursor.execute(operation=query)
        results = cursor.fetchall()
        
        # Close cursor
        cursor.close()
        
        return results if len(results) > 0 else None

    def set(self, account, player):
        '''
        @param
         - account : String account to be added
         - player  : String name of player to add

        @return
         - Boolean indicating if operation successful
        '''
        if player == None: return False
        player = player.strip()
        cursor = self.con.cursor()
        
        # Get player object
        player_object, date_updated = scraping.get_player_object(account)

        # Does player exist (not account)
        player_exists = True
        query_get_player_id = f"SELECT ID FROM players WHERE UPPER(Name) = UPPER('{player}')"
        cursor.execute(operation=query_get_player_id)
        player_id = cursor.fetchall()
        if player_id != None and len(player_id) != 0:
            player_id = player_id[0][0]
        else:
            # Create new player record
            query_create_player = f"INSERT INTO players (Name) VALUES ('{player}')"
            cursor.execute(operation=query_create_player)
            cursor.execute(operation=query_get_player_id)
            player_id = cursor.fetchall()[0][0]
            player_exists = False
        
        # INSERT INTO accounts
        camera = player_object['camera']
        fields = (
            "PlayerID, AccountID, Platform, "
            "Main, FOV, Distance, Height, Angle, Stiffness, "
            "SwivelSpeed, TransitionSpeed, "
            "SteeringSensitivity, DateUpdated"
        )
        values = (
            f"{player_id}, '{player_object['id']['id']}', "
            f"'{player_object['id']['platform']}', "
            f"{0 if player_exists else 1}, "
            f"{camera['fov']}, {camera['distance']}, "
            f"{camera['height']}, {camera['pitch']}, "
            f"{camera['stiffness']}, {camera['swivel_speed']}, "
            f"{camera['transition_speed']}, "
            f"{player_object['steering_sensitivity']}, '{date_updated}'"
        )
        query_create_account = (
            f"INSERT INTO accounts ({fields}) VALUES ({values})"
        )
        cursor.execute(operation=query_create_account)

        # Commit and close
        cursor.close()
        self.con.commit()
        return True
    
    def flag(self, player):
        '''
        @param
         - player  : String name of player

        @return
         - Boolean indicating if operation successful
         - Int player_id
        '''
        if player == None: return False, None
        player = player.strip()
        cursor = self.con.cursor()

        # Does player exist (not account)
        query_get_player_id = f"SELECT ID FROM players WHERE UPPER(Name) = UPPER('{player}')"
        cursor.execute(operation=query_get_player_id)
        player_id = cursor.fetchall()
        if player_id != None and len(player_id) != 0:
            player_id = player_id[0][0]
        else:
            # Player doesn't exist: return false
            cursor.close()
            return False, 0
            
        # Already in flag table?
        query_get_id_from_player_id = f"SELECT ID FROM flags WHERE PlayerID = {player_id}"
        cursor.execute(operation=query_get_id_from_player_id)
        flag_id = cursor.fetchall()
        if flag_id != None and len(flag_id) != 0: # Player already in flag table
            cursor.close()
            return False, player_id
        else:
            # Add the player to the flag table
            query_create_player = f"INSERT INTO flags (PlayerID) VALUES ('{player_id}')"
            cursor.execute(operation=query_create_player)

        # Commit and close
        cursor.close()
        self.con.commit()
        return True, player_id

    def recondition(self):
        '''
        @return
         - Boolean indicating if/when reconditioning successful
        '''
        
        # Create cursor
        cursor = self.con.cursor()

        # Query to get all the accounts
        query_all_accounts = f"SELECT Platform, AccountID FROM accounts"
        cursor.execute(operation=query_all_accounts)
        results = cursor.fetchall()
        cursor.close()
        
        print(f" - Number to recondition: {len(results)}")
        for i in range(0, len(results)):
            if i % (len(results)/10) == 0:
                print(f" - {int(i / len(results) * 100)}%")
            player_object = None
            try:
                player_object, date_updated = scraping.get_player_object(f"{results[i][0]}:{results[i][1]}")
            except:
                print(f" ! get_player_object {results[i][0]}:{results[i][1]}")
                continue
            response = self.update_account(player_object, date_updated)
            if response:
                print(f" - {i}  {results[i][0]}:{results[i][1]}")
            else:
                print(f" ! update_account {results[i][0]}:{results[i][1]}")

        print(f" - 100%")
        return True

    def update_account(self, player_object, date_updated):
        '''
        @param
         - player_object : Dictionary containing player object
         - date_updated : String containing date of replay
         
        @return
         - Boolean indicating if update was successful
        '''

        if player_object == None: return False
        cursor = self.con.cursor()

        # Query to update account with the new information gained
        camera = player_object['camera']
        query_update_account = (
            f"UPDATE accounts "
            f"SET FOV='{camera['fov']}', Distance='{camera['distance']}', "
            f"Height='{camera['height']}', "
            f"Angle='{camera['pitch']}', Stiffness='{camera['stiffness']}', "
            f"SwivelSpeed='{camera['swivel_speed']}', "
            f"TransitionSpeed='{camera['transition_speed']}', "
            f"SteeringSensitivity='{player_object['steering_sensitivity']}', "
            f"DateUpdated='{date_updated}' "
            f"WHERE Platform='{player_object['id']['platform']}' "
            f"AND AccountID='{player_object['id']['id']}'"
        )
        cursor.execute(operation=query_update_account)
    
        # Commit and close
        cursor.close()
        self.con.commit()
        return True
