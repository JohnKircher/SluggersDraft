from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import ast
from utils import min_max_scale_scores, calculate_chemistry_metric, create_player_tuples, get_chemistry_links, get_hate_links
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Load data
chem_data = pd.read_excel('data/sortedmasterchem.xlsx')
player_stats = pd.read_excel('data/Player Statistics.xlsx')
season_data = pd.read_excel('data/Season Data.xlsx')

# Convert Chemistry and Hate to python list instead of string
chem_data['Chemistry'] = chem_data['Chemistry'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
chem_data['Hate'] = chem_data['Hate'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# Hardcoded team names and initial picks
teams = {
    "BenR": [],
    "Julian": [],
    "Tom": [],
    "Harry": [],
    "Kircher": [],
    "BenT": [],
    "Carbone": [],
    "Jmo": []
}

# List of captains
captains = ["Mario", "Luigi", "Peach", "Daisy", "Yoshi", "Birdo", "Wario", "Waluigi", "Donkey Kong", "Diddy Kong", "Bowser", "Bowser Jr"]

# Initialize a dictionary to track if each team has a captain
teams_with_captain = {team: False for team in teams}

# Initialize draft order
draft_order = list(teams.keys())
remaining_players = list(player_stats['Character'])
remaining_captains = [player for player in remaining_players if player in captains]

# Function to reset the draft
def reset_draft():
    global teams, teams_with_captain, draft_order, remaining_players, remaining_captains
    teams = {team: [] for team in teams}  # Reset all teams' rosters
    teams_with_captain = {team: False for team in teams}  # Reset captain status
    draft_order = list(teams.keys())  # Reset draft order
    remaining_players = list(player_stats['Character'])  # Reset remaining players
    remaining_captains = [player for player in remaining_players if player in captains]  # Reset remaining captains

# Function to calculate player scores
def calculate_scores(players, team_players, chem_data, player_stats, season_data):
    # If there are no remaining players, return an empty list
    if not players:
        return []

    scores = {}
    for player in players:
        chem_score = calculate_chemistry_metric(team_players, player, players, chem_data)
        stats = player_stats.loc[player_stats['Character'] == player]
        season_stats = season_data.loc[season_data['First Name'] == player]
        
        # Use 25% of average stats if player is missing in season_data
        if season_stats.empty:
            slugging = season_data['Slugging Percentage'].mean() * 0.25
            home_runs = season_data['Home Runs'].mean() * 0.25
        else:
            slugging = season_stats['Slugging Percentage'].mean()
            home_runs = season_stats['Home Runs'].sum()
        
        if stats.empty:
            charge_hit_power = player_stats['Charge Hit Power'].mean() * 0.25
            slap_hit_power = player_stats['Slap Hit Power'].mean() * 0.25
            speed = player_stats['Speed'].mean() * 0.25
            pitching_stamina = player_stats['Pitching Stamina'].mean() * 0.25
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
    final_scores = create_player_tuples(scores)
    return final_scores

# Updated Function to recommend outfielders
def recommend_outfielders(team_players, remaining_players, chem_data, player_stats, cf_player=None):
    """
    Recommends outfielders (LF and RF) based on speed and chemistry with the designated CF.
    - If a CF is designated, players with chemistry and speed >= 50 are shown first, followed by the fastest players.
    - If no CF is designated, only the top 10 fastest players are shown.
    """
    # Get all players sorted by speed (highest first)
    all_players_sorted = sorted(
        remaining_players,
        key=lambda x: player_stats.loc[player_stats['Character'] == x, 'Speed'].values[0],
        reverse=True
    )

    # If a CF is designated, prioritize players with chemistry and speed >= 50
    if cf_player:
        # Get players with chemistry to the CF and speed >= 50
        players_with_chem = []
        for player in all_players_sorted:
            speed = player_stats.loc[player_stats['Character'] == player, 'Speed'].values[0]
            if speed >= 50:  # Only consider players with speed >= 50
                chemistry_links = get_chemistry_links(player, [cf_player], chem_data)
                if chemistry_links:
                    players_with_chem.append((player, speed, f"(Chemistry with {cf_player})"))

        # Get the remaining players (without chemistry or speed < 50) sorted by speed
        players_without_chem = [
            (player, player_stats.loc[player_stats['Character'] == player, 'Speed'].values[0], "")
            for player in all_players_sorted
            if player not in [p[0] for p in players_with_chem]  # Exclude players already in the chemistry list
        ]

        # Combine the two lists: chemistry players first, then the rest
        recommendations = players_with_chem + players_without_chem
    else:
        # If no CF is designated, just return the top 10 players with their speed
        recommendations = [
            (player, player_stats.loc[player_stats['Character'] == player, 'Speed'].values[0], "")
            for player in all_players_sorted[:10]
        ]

    # Return the top 10 players
    return recommendations[:10]

@app.route('/')
def index():
    return render_template('index.html', teams=teams)

@app.route('/draft/<team>', methods=['GET', 'POST'])
def draft(team):
    if request.method == 'POST':
        pick = request.form['pick']
        
        # Check if the team is required to pick a captain
        teams_missing_captain = [team for team, has_captain in teams_with_captain.items() if not has_captain]
        must_pick_captain = len(teams_missing_captain) == len(remaining_captains)
        
        # Validate the pick
        if must_pick_captain:
            if not teams_with_captain[team] and pick not in remaining_captains:
                flash("You must pick a captain!", "warning")
                return redirect(url_for('draft', team=team))
            elif teams_with_captain[team] and pick in remaining_captains:
                flash("You already have a captain and cannot pick another!", "warning")
                return redirect(url_for('draft', team=team))
        
        # Handle the pick
        teams[team].append(pick)
        remaining_players.remove(pick)
        if pick in captains:
            teams_with_captain[team] = True
            remaining_captains.remove(pick)
        
        # Determine the next team for the snake draft
        current_index = draft_order.index(team)
        if current_index == len(draft_order) - 1:
            # Reverse the draft order for the next round
            draft_order.reverse()
            next_team = team  # The same team picks again
        else:
            next_team = draft_order[current_index + 1]
        
        # If no players are left, redirect to final rosters
        if not remaining_players:
            return redirect(url_for('final_rosters'))
        
        return redirect(url_for('draft', team=next_team))
    
    # Get the CF designation for the current team
    cf_player = session.get(f'cf_player_{team}', None)
    
    # Calculate player scores for recommendations
    player_scores = calculate_scores(remaining_players, teams[team], chem_data, player_stats, season_data)
    player_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Check if the team needs to pick a captain
    teams_missing_captain = [team for team, has_captain in teams_with_captain.items() if not has_captain]
    must_pick_captain = len(teams_missing_captain) == len(remaining_captains)
    
    # Check if the team needs outfielders
    outfield_recommendations = []
    if not any(player in teams[team] for player in ['RF', 'CF', 'LF']):
        outfield_recommendations = recommend_outfielders(teams[team], remaining_players, chem_data, player_stats, cf_player)
    
    # Pass get_chemistry_links, get_hate_links, and chem_data to the template
    return render_template(
        'draft.html',
        team=team,
        players=player_scores[:5],
        roster=teams[team],
        must_pick_captain=must_pick_captain,
        outfield_recommendations=outfield_recommendations,
        get_chemistry_links=get_chemistry_links,
        get_hate_links=get_hate_links,
        chem_data=chem_data,  # Pass chem_data to the template
        remaining_players=remaining_players,  # Pass remaining players for the collapsible menu
        remaining_captains=remaining_captains,  # Pass remaining captains for the warning
        teams_with_captain=teams_with_captain  # Pass teams_with_captain to the template
    )

@app.route('/roster/<team>')
def roster(team):
    return render_template('roster.html', team=team, roster=teams[team])

@app.route('/final_rosters')
def final_rosters():
    # Export the draft results to an Excel file
    export_draft_results(teams)
    
    return render_template('final_rosters.html', teams=teams)

@app.route('/reset_draft', methods=['POST'])
def reset_draft_route():
    reset_draft()
    flash("Draft has been reset!", "success")
    return redirect(url_for('index'))

@app.route('/designate_cf/<team>', methods=['POST'])
def designate_cf(team):
    cf_player = request.form['cf_player']
    session[f'cf_player_{team}'] = cf_player  # Store the CF in the session for the current team
    return redirect(url_for('draft', team=team))

def export_draft_results(teams, filename='draft_results.xlsx'):
    # Create a dictionary to store the picks for each round
    draft_results = {}
    
    # Determine the maximum number of picks made by any team
    max_picks = max(len(team) for team in teams.values())
    
    # Iterate through each round
    for round_num in range(1, max_picks + 1):
        round_picks = {}
        for team, players in teams.items():
            if len(players) >= round_num:
                round_picks[team] = players[round_num - 1]
            else:
                round_picks[team] = None  # No pick made in this round
        draft_results[f'Round {round_num}'] = round_picks
    
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(draft_results)
    
    # Export the DataFrame to an Excel file
    df.to_excel(filename, index=True)

if __name__ == '__main__':
    app.run(debug=True)