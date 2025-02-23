import pandas as pd
from colorama import Fore, Style  # For colored text

# Load data
chem_data = pd.read_excel('sortedmasterchem.xlsx')
player_stats = pd.read_excel('Player Statistics.xlsx')
season_data = pd.read_excel('Season Data.xlsx')

# Hardcoded team names and initial picks
teams = {
    "Team BenR": ["Donkey Kong", "Baby DK"],
    "Team Julian": ["Bowser", "Baby Luigi"],
    "Team Tom": ["Wario", "Hammer Bro"],
    "Team Harry": ["Birdo", "Baby Peach"],
    "Team Kircher": ["Fire Bro", "Bowser Jr"],
    "Team BenT": ["Yoshi", "King K Rool"],
    "Team Carbone": ["Funky Kong", "Peach"],
    "Team Jmo": ["Petey Piranha", "Mario"]
}

# Calculate average stats for missing players
average_slugging = season_data['Slugging Percentage'].mean()
average_charge_hit_power = player_stats['Charge Hit Power'].mean()
average_slap_hit_power = player_stats['Slap Hit Power'].mean()
average_speed = player_stats['Speed'].mean()
average_home_runs = season_data['Home Runs'].mean()
average_pitching_stamina = player_stats['Pitching Stamina'].mean()

# Function to calculate player score
def calculate_score(player, team_players, chem_data, player_stats, season_data):
    # Calculate chemistry score
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
                chem_score -= 1
    
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
    
    # Weighted score (chemistry is the primary factor)
    total_score = (chem_score * 50) + (slugging * 5) + (charge_hit_power * 3) + (slap_hit_power * 3) + (speed * 2) + (home_runs * 4) + (pitching_stamina * 2)
    
    return total_score

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

# Main draft loop
remaining_players = list(player_stats['Character'])  # Use all players from Player Statistics
for team in teams:
    remaining_players = [player for player in remaining_players if player not in teams[team]]

# Print characters missing in Season Data
missing_players = [player for player in remaining_players if player not in season_data['First Name'].values]
print("\nCharacters missing in Season Data:")
for player in missing_players:
    print(player)

# Initialize draft order
draft_order = list(teams.keys())

while remaining_players:
    current_team = draft_order.pop(0)  # Get the next team in the draft order
    draft_order.append(current_team)  # Add the team back to the end of the draft order
    
    # Display current roster with hate relationships
    print(f"\nTeam {current_team}'s current roster:")
    for i, player in enumerate(teams[current_team], start=1):
        hate_count = check_hate(player, teams[current_team], chem_data)
        hate_text = f"{Fore.RED}(Hates {hate_count} teammates){Style.RESET_ALL}" if hate_count > 0 else ""
        print(f"{i}. {player} {hate_text}")
    
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
    print(f"\nTeam {current_team}, players with good chemistry links:")
    for i, (player, chem_score, hate_count) in enumerate(good_chemistry_players, start=1):
        hate_text = f"{Fore.RED}(Hated by {hate_count}){Style.RESET_ALL}" if hate_count > 0 else ""
        hates_team = check_hate(player, teams[current_team], chem_data)
        hates_team_text = f"{Fore.RED}(Hates {hates_team} teammates){Style.RESET_ALL}" if hates_team > 0 else ""
        print(f"{i}. {player} (Chemistry Links: {chem_score}) {hate_text} {hates_team_text}")
    
    # Calculate best available players for this team
    player_scores = []
    for player in remaining_players:
        score = calculate_score(player, teams[current_team], chem_data, player_stats, season_data)
        if score != -1:  # Only include players with valid scores
            # Calculate chemistry links and hate count for top 5 players
            chem_score = 0
            hate_count = 0
            player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
            if not player_chem_data.empty:
                chemistry_list = player_chem_data['Chemistry'].values[0] if player_chem_data['Chemistry'].values[0] else []
                hate_list = player_chem_data['Hate'].values[0] if player_chem_data['Hate'].values[0] else []
                for team_player in teams[current_team]:
                    if team_player in chemistry_list:
                        chem_score += 1
                    if team_player in hate_list:
                        hate_count += 1
            hates_team = check_hate(player, teams[current_team], chem_data)
            player_scores.append((player, score, chem_score, hate_count, hates_team))
    
    # Sort by score (chemistry is the primary factor)
    player_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Display top 5 suggestions
    print(f"\nTeam {current_team}, top 5 best available players:")
    for i, (player, score, chem_score, hate_count, hates_team) in enumerate(player_scores[:5], start=1):
        hate_text = f"{Fore.RED}(Hated by {hate_count}){Style.RESET_ALL}" if hate_count > 0 else ""
        hates_team_text = f"{Fore.RED}(Hates {hates_team} teammates){Style.RESET_ALL}" if hates_team > 0 else ""
        print(f"{i}. {player} (Score: {score}, Chemistry Links: {chem_score}) {hate_text} {hates_team_text}")
    
    # User makes a pick
    if player_scores:  # Ensure there are players to pick
        while True:
            pick = input("Enter the name of the player you want to draft: ").strip()
            if pick in remaining_players:
                teams[current_team].append(pick)
                remaining_players.remove(pick)
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