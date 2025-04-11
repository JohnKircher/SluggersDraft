import math
import ast
import pandas as pd
from colorama import Fore, Style  # For colored text
from utils import min_max_scale_scores, calculate_chemistry_metric, create_player_tuples

# Load data
chem_data = pd.read_excel('sortedmasterchem.xlsx')
player_stats = pd.read_excel('Player Statistics.xlsx')
season_data = pd.read_excel('Season Data.xlsx')

# Convert Chemistry and Hate to python list instead of string
chem_data['Chemistry'] = chem_data['Chemistry'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
chem_data['Hate'] = chem_data['Hate'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Hardcoded team names and initial picks
teams = {
    "HarryKirch": [],
    "BenR": [],
    "Carbone": [],
    "Julian": [],
    "Tom": [],
    "Kircher": [],
    "Jmo": [],
    "BenT": []
}

# List of captains
captains = ["Mario", "Luigi", "Peach", "Daisy", "Yoshi", "Birdo", "Wario", "Waluigi", "Donkey Kong", "Diddy Kong", "Bowser", "Bowser Jr"]
# Initialize a dictionary to track if each team has a captain
teams_with_captain = {team: False for team in teams}

# Calculate average stats for missing players
average_slugging = season_data['Slugging Percentage'].mean()
average_charge_hit_power = player_stats['Charge Hit Power'].mean()
average_slap_hit_power = player_stats['Slap Hit Power'].mean()
average_speed = player_stats['Speed'].mean()
average_home_runs = season_data['Home Runs'].mean()
average_pitching_stamina = player_stats['Pitching Stamina'].mean()

# Function to calculate player scores for a list of players
def calculate_scores(players, team_players, chem_data, player_stats, season_data):
    scores = []
    """
    scores: dictionary of the players as keys and the values as dictionaries of keys with chem_score, slugging, charge_hit power etc. and values as their value
    scores = {'Mario': {'chem_score': .8},...}
    
    """
    scores = {}
    for player in players:
        chem_score = calculate_chemistry_metric(team_players, player, players, chem_data)
        """# Calculate chemistry score
        chem_score = 0
        for team_player in team_players:
            # Check if player exists in chem_data
            player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
            if not player_chem_data.empty:
                chemistry_list = player_chem_data['Chemistry'].values[0] if player_chem_data['Chemistry'].values[0] else []
                hate_list = player_chem_data['Hate'].values[0] if player_chem_data['Hate'].values[0] else []
                if team_player in chemistry_list:
                    chem_score += 1
                if team_player in hate_list:
                    chem_score -= 1"""
        
        # Get player stats
        stats = player_stats.loc[player_stats['Character'] == player]
        season_stats = season_data.loc[season_data['First Name'] == player]
        
        # Use 25% of average stats if player is missing in season_data
        if season_stats.empty:
            slugging = average_slugging * 0.25
            home_runs = average_home_runs * 0.25
        else:
            slugging = season_stats['Slugging Percentage'].mean()
            home_runs = season_stats['Home Runs'].sum()
        
        if stats.empty:
            charge_hit_power = average_charge_hit_power * 0.25
            slap_hit_power = average_slap_hit_power * 0.25
            speed = average_speed * 0.25
            pitching_stamina = average_pitching_stamina * 0.25
        else:
            charge_hit_power = stats['Charge Hit Power'].values[0]
            slap_hit_power = stats['Slap Hit Power'].values[0]
            speed = stats['Speed'].values[0]
            pitching_stamina = stats['Pitching Stamina'].values[0]
            
        
        scores[player] = {
            'chem_score': chem_score,
            'slugging': slugging,
            'charge_hit_power': charge_hit_power,
            'slap_hit_power': slap_hit_power,
            'speed': speed,
            'home_runs': home_runs,
            'pitching_stamina': pitching_stamina,
        }
        
    scores = min_max_scale_scores(scores)
        
    # Weighted score (chemistry is the primary factor)
    """total_score = (chem_score * 50) + (slugging * 5) + (charge_hit_power * 3) + (slap_hit_power * 3) + (speed * 2) + (home_runs * 4) + (pitching_stamina * 2)"""

    final_scores = create_player_tuples(scores)

    """# Append player's score and components to the list
        scores.append((player, total_score, chem_score, slugging, charge_hit_power, slap_hit_power, speed, home_runs, pitching_stamina))"""
    
    return final_scores

# Function to check if a player hates anyone on the team
def check_hate(player, team_players, chem_data):
    hate_count = 0
    player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
    if not player_chem_data.empty:
        hate_list = player_chem_data['Hate'].values[0] if player_chem_data['Hate'].values[0] else []
        for team_player in team_players:
            if team_player in hate_list:
                hate_count += 1
    return hate_count


# Add this function to draft.py
def recommend_outfielders(team_players, remaining_players, chem_data, player_stats, cf_player=None):
    """
    Recommends outfielders (LF and RF) based on speed and chemistry with the designated CF.
    """
    # Filter players with speed >= 50
    fast_players = [player for player in remaining_players if player_stats.loc[player_stats['Character'] == player, 'Speed'].values[0] >= 50]
    
    if cf_player:
        # If a CF is designated, filter players with chemistry links to the CF
        players_with_chem_to_cf = []
        for player in fast_players:
            chemistry_links = get_chemistry_links(player, [cf_player], chem_data)
            if chemistry_links:  # If the player has chemistry with the CF
                speed = player_stats.loc[player_stats['Character'] == player, 'Speed'].values[0]
                players_with_chem_to_cf.append((player, speed))
        
        # Sort players by speed (highest first)
        players_with_chem_to_cf.sort(key=lambda x: x[1], reverse=True)
        
        # Display top 5 outfield recommendations
        print(f"\nTop 5 outfield recommendations (with chemistry to {cf_player}):")
        for i, (player, speed) in enumerate(players_with_chem_to_cf[:5], start=1):
            print(f"{i}. {player} (Speed: {speed})")
    else:
        # If no CF is designated, recommend based on speed only
        fast_players_sorted = sorted(fast_players, key=lambda x: player_stats.loc[player_stats['Character'] == x, 'Speed'].values[0], reverse=True)
        print("\nTop 5 outfield recommendations (based on speed only):")
        for i, player in enumerate(fast_players_sorted[:5], start=1):
            print(f"{i}. {player} (Speed: {player_stats.loc[player_stats['Character'] == player, 'Speed'].values[0]})")

def get_chemistry_links(player, team_players, chem_data):
    """
    Returns a list of players on the team that the given player has chemistry with.
    """
    player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
    if not player_chem_data.empty:
        chemistry_list = player_chem_data['Chemistry'].values[0] if player_chem_data['Chemistry'].values[0] else []
        # Find intersection between chemistry list and team players
        chemistry_links = [team_player for team_player in team_players if team_player in chemistry_list]
        return chemistry_links
    return []

def get_hate_links(player, team_players, chem_data):
    """
    Returns a list of players on the team that the given player hates or is hated by.
    """
    player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
    if not player_chem_data.empty:
        hate_list = player_chem_data['Hate'].values[0] if player_chem_data['Hate'].values[0] else []
        # Find intersection between hate list and team players
        hate_links = [team_player for team_player in team_players if team_player in hate_list]
        return hate_links
    return []

def designate_cf(team_players, remaining_players, chem_data, player_stats):
    """
    Allows the team to designate a Center Fielder (CF) from their current roster.
    """
    print("\nDesignate a Center Fielder (CF) from your current roster:")
    for i, player in enumerate(team_players, start=1):
        print(f"{i}. {player}")
    
    while True:
        try:
            cf_index = int(input("Enter the number of the player you want to designate as CF: ")) - 1
            if 0 <= cf_index < len(team_players):
                cf_player = team_players[cf_index]
                print(f"{cf_player} has been designated as the Center Fielder (CF).")
                return cf_player
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Main draft loop
remaining_players = list(player_stats['Character'])  # Use all players from Player Statistics
remaining_captains = [player for player in remaining_players if player in captains]  # Track remaining captains

for team in teams:
    remaining_players = [player for player in remaining_players if player not in teams[team]]

# Print characters missing in Season Data
missing_players = [player for player in remaining_players if player not in season_data['First Name'].values]
print("\nCharacters missing in Season Data:")
for player in missing_players:
    print(player)

# Initialize draft order
draft_order = list(teams.keys())
counter = 0

# Modify the main draft loop in draft.py
while remaining_players:
    current_team = draft_order.pop(0)  # Get the next team in the draft order
    draft_order.append(current_team)  # Add the team back to the end of the draft order
    counter += 1
    
    if counter % 8 == 0:
        draft_order = list(reversed(draft_order))
        
    # Display current roster with hate relationships
    # Modify the current roster display section in the main draft loop
    print(f"\nTeam {current_team}'s current roster:")
    for i, player in enumerate(teams[current_team], start=1):
        # Get hate links for the player
        hate_links = get_hate_links(player, teams[current_team], chem_data)
        hate_text = f"{Fore.RED}(Hates: {', '.join(hate_links)}){Style.RESET_ALL}" if hate_links else ""
        
        # Get chemistry links for the player
        chemistry_links = get_chemistry_links(player, teams[current_team], chem_data)
        chem_text = f"{Fore.GREEN}(Chemistry with: {', '.join(chemistry_links)}){Style.RESET_ALL}" if chemistry_links else ""
        
        print(f"{i}. {player} {hate_text} {chem_text}")
    
    # Check if the team needs to pick a captain
    teams_missing_captain = [team for team, has_captain in teams_with_captain.items() if not has_captain]
    
    # Only show the warning if there are still captains remaining
    if remaining_captains:
        if len(teams_missing_captain) == len(remaining_captains):
            # If the number of teams missing a captain equals the number of remaining captains
            if not teams_with_captain[current_team]:
                # If the current team does not have a captain, they must pick one
                print(f"\n{Fore.YELLOW}WARNING: The number of teams missing a captain ({len(teams_missing_captain)}) is equal to the number of captains remaining ({len(remaining_captains)}).{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Team {current_team} must pick a captain.{Style.RESET_ALL}")
                
                # Force the team to pick a captain
                while True:
                    pick = input("Enter the name of the captain you want to draft: ").strip()
                    if pick in remaining_captains:
                        teams[current_team].append(pick)
                        remaining_players.remove(pick)
                        remaining_captains.remove(pick)
                        teams_with_captain[current_team] = True
                        break
                    else:
                        print("Invalid captain name. Please pick a captain from the list.")
                continue
            else:
                # If the current team already has a captain, they cannot pick another captain
                print(f"\n{Fore.YELLOW}WARNING: The number of teams missing a captain ({len(teams_missing_captain)}) is equal to the number of captains remaining ({len(remaining_captains)}).{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Team {current_team} already has a captain and cannot draft another captain.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Teams without a captain must pick a captain first.{Style.RESET_ALL}")
                
        elif len(teams_missing_captain) < len(remaining_captains):
            # If there are more captains than teams missing a captain, allow teams to pick captains freely
            pass  # No restrictions, proceed as normal
    
    # Check if the team needs outfielders
    # Check if the team needs outfielders
    has_outfielders = recommend_outfielders(teams[current_team], remaining_players, chem_data, player_stats)
    
    # Allow the team to designate a CF if they don't have one
    cf_player = None
    # In the main draft loop, after designating a CF:
    if not has_outfielders:
        designate_cf_prompt = input("Do you want to designate a Center Fielder (CF)? (yes/no): ").strip().lower()
        if designate_cf_prompt == 'yes':
            cf_player = designate_cf(teams[current_team], remaining_players, chem_data, player_stats)
            # Re-run outfield recommendations with the designated CF
            recommend_outfielders(teams[current_team], remaining_players, chem_data, player_stats, cf_player)
        else:
            # If no CF is designated, recommend based on speed only
            recommend_outfielders(teams[current_team], remaining_players, chem_data, player_stats)
    
    # Find all players with good chemistry links
    good_chemistry_players = []
    for player in remaining_players:
        chem_score = 0
        hate_count = 0
        # Check if player exists in chem_data
        player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
        if not player_chem_data.empty:
            chemistry_list = player_chem_data['Chemistry'].values[0] if player_chem_data['Chemistry'].values[0] else []
            hate_list = player_chem_data['Hate'].values[0] if player_chem_data['Hate'].values[0] else []
            for team_player in teams[current_team]:
                if team_player in chemistry_list:
                    chem_score += 1
                if team_player in hate_list:
                    hate_count += 1
            if chem_score > 0:  # Only include players with positive chemistry
                good_chemistry_players.append((player, chem_score, hate_count))
    
    # Display good chemistry links
    # Modify the good chemistry links display section in the main draft loop
    # Modify the good chemistry links display section in the main draft loop
    print(f"\nTeam {current_team}, players with good chemistry links:")
    for i, (player, chem_score, hate_count) in enumerate(good_chemistry_players, start=1):
        # Get hate links for the player
        hate_links = get_hate_links(player, teams[current_team], chem_data)
        hate_text = f"{Fore.RED}(Hates: {', '.join(hate_links)}){Style.RESET_ALL}" if hate_links else ""
        
        # Get chemistry links for the player
        chemistry_links = get_chemistry_links(player, teams[current_team], chem_data)
        chem_text = f"{Fore.GREEN}(Chemistry with: {', '.join(chemistry_links)}){Style.RESET_ALL}" if chemistry_links else ""
        
        print(f"{i}. {player} {chem_text} {hate_text}")
    
    # Calculate best available players for this team
    player_scores = calculate_scores(remaining_players, teams[current_team], chem_data, player_stats, season_data)
    
    # Sort by score (chemistry is the primary factor)
    player_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Modify the top 5 recommendations display section in the main draft loop
    print(f"\nTeam {current_team}, top 5 best available players:")
    for i, (player, total_score, chem_score, slugging, charge_hit_power, slap_hit_power, speed, home_runs, pitching_stamina) in enumerate(player_scores[:5], start=1):
        # Get hate links for the player
        hate_links = get_hate_links(player, teams[current_team], chem_data)
        hate_text = f"{Fore.RED}(Hates: {', '.join(hate_links)}){Style.RESET_ALL}" if hate_links else ""
        
        # Get chemistry links for the player
        chemistry_links = get_chemistry_links(player, teams[current_team], chem_data)
        chem_text = f"{Fore.GREEN}(Chemistry with: {', '.join(chemistry_links)}){Style.RESET_ALL}" if chemistry_links else ""
        
        total_score = round(total_score, 2)
        print(f"{i}. {player} (Score: {total_score}) {chem_text} {hate_text}")
    
    # User makes a pick
    if player_scores:  # Ensure there are players to pick
        while True:
            pick = input("Enter the name of the player you want to draft: ").strip()
            if pick in remaining_players:
                # Prevent teams with a captain from drafting another captain if the condition is met
                if pick in remaining_captains and teams_with_captain[current_team] and len(teams_missing_captain) == len(remaining_captains):
                    print(f"{Fore.RED}Team {current_team} already has a captain and cannot draft another captain.{Style.RESET_ALL}")
                    print(f"{Fore.RED}Please select a non-captain player.{Style.RESET_ALL}")
                    continue
                
                teams[current_team].append(pick)
                remaining_players.remove(pick)
                if pick in captains:
                    teams_with_captain[current_team] = True
                    remaining_captains.remove(pick)
                break
            else:
                print("Invalid player name. Please try again.")
    else:
        print("No valid players to draft. Ending draft.")
        break


print("\nDraft complete!")
print("\nFinal rosters:")
for team, roster in teams.items():
    print(f"\nTeam {team}:")
    for i, player in enumerate(roster, start=1):
        hate_count = check_hate(player, roster, chem_data)
        hate_text = f"{Fore.RED}(Hates {hate_count} teammates){Style.RESET_ALL}" if hate_count > 0 else ""
        print(f"{i}. {player} {hate_text}")