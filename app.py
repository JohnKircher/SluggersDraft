from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import ast
from utils import min_max_scale_scores, calculate_chemistry_metric, create_player_tuples, get_chemistry_links, get_hate_links
from openpyxl import Workbook
import uuid

app = Flask(__name__, static_folder='static', static_url_path='/static')
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
    "Julian": [],
    "Kircher": [],
    "Carby": [],
    "BenT": [],
    "Tom": [],
    "HarryKirch": [],
    "Jmo": [],
    "BenR": []
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

def sort_available_players(remaining_players, current_team, chem_data):
    """
    Sort available players into groups based on their chemistry with the current team:
    1. Good Chemistry
    2. 50/50 Chemistry (neutral)
    3. Hated Chemistry
    4. No Chemistry
    """
    good_chem_players = []
    neutral_chem_players = []
    hated_chem_players = []
    no_chem_players = []

    for player in remaining_players:
        # Get the player's chemistry and hate data
        player_chem_data = chem_data.loc[chem_data['Character Name'] == player]
        if not player_chem_data.empty:
            chemistry_list = player_chem_data['Chemistry'].values[0] if isinstance(player_chem_data['Chemistry'].values[0], (list, set)) else []
            hate_list = player_chem_data['Hate'].values[0] if isinstance(player_chem_data['Hate'].values[0], (list, set)) else []
        else:
            chemistry_list = []
            hate_list = []

        # Check chemistry and hate relationships with the current team
        positive_chem = len(set(chemistry_list).intersection(current_team))
        negative_chem = len(set(hate_list).intersection(current_team))

        if positive_chem > 0:
            good_chem_players.append((player, positive_chem, negative_chem))
        elif negative_chem > 0:
            hated_chem_players.append((player, positive_chem, negative_chem))
        elif positive_chem == 0 and negative_chem == 0:
            neutral_chem_players.append((player, positive_chem, negative_chem))
        else:
            no_chem_players.append((player, positive_chem, negative_chem))

    # Sort each group by positive chemistry (descending) and negative chemistry (ascending)
    good_chem_players.sort(key=lambda x: (x[1], -x[2]), reverse=True)
    neutral_chem_players.sort(key=lambda x: (x[1], -x[2]), reverse=True)
    hated_chem_players.sort(key=lambda x: (x[1], -x[2]), reverse=True)
    no_chem_players.sort(key=lambda x: (x[1], -x[2]), reverse=True)

    # Combine all groups in the desired order
    sorted_players = good_chem_players + neutral_chem_players + hated_chem_players + no_chem_players

    # Extract just the player names for the final list
    sorted_player_names = [player[0] for player in sorted_players]

    return sorted_player_names

@app.route('/draft/<team>', methods=['GET', 'POST'])
def draft(team):
    if 'draft_id' not in session:
        flash("No active draft session. Please start a new draft.", "warning")
        return redirect(url_for('index'))

    # Retrieve session values
    teams = session.get('teams', {})
    remaining_players = session.get('remaining_players', [])
    remaining_captains = session.get('remaining_captains', [])
    teams_with_captain = session.get('teams_with_captain', {})
    draft_order = session.get('draft_order', list(teams.keys()))

    # Validate the team exists
    if team not in teams:
        flash("Invalid team selected!", "error")
        return redirect(url_for('index'))

    # Identify teams that still need a captain
    teams_missing_captain = [t for t, has_captain in teams_with_captain.items() if not has_captain]
    must_pick_captain = len(teams_missing_captain) == len(remaining_captains)

    if request.method == 'POST':
        pick = request.form['pick']

        # Ensure the pick is valid
        if pick not in remaining_players:
            flash("Invalid pick!", "error")
            return redirect(url_for('draft', team=team))

        # **STRICT CAPTAIN SELECTION RULES**
        if must_pick_captain:
            # If the team does not have a captain, they MUST pick a captain
            if not teams_with_captain[team] and pick not in remaining_captains:
                flash("You must pick a captain!", "warning")
                return redirect(url_for('draft', team=team))
            # If the team already has a captain, they CANNOT pick another captain
            elif teams_with_captain[team] and pick in remaining_captains:
                flash("You already have a captain and cannot pick another!", "error")
                return redirect(url_for('draft', team=team))
        else:
            # If must_pick_captain is False, teams can pick any player (including captains)
            pass

        # Assign pick to the team
        teams[team].append(pick)
        remaining_players.remove(pick)
        if pick in remaining_captains:
            teams_with_captain[team] = True
            remaining_captains.remove(pick)

        # Determine the next team for the draft
        current_index = draft_order.index(team)
        if current_index == len(draft_order) - 1:
            draft_order.reverse()  # Reverse for snake draft
            next_team = draft_order[0]  # First team in new order
        else:
            next_team = draft_order[current_index + 1]

        # Save updated session data
        session['teams'] = teams
        session['remaining_players'] = remaining_players
        session['remaining_captains'] = remaining_captains
        session['teams_with_captain'] = teams_with_captain
        session['draft_order'] = draft_order

        return redirect(url_for('draft', team=next_team))

    # Sort available players based on chemistry
    sorted_players = sort_available_players(remaining_players, teams[team], chem_data)

    return render_template(
        'draft.html',
        team=team,
        roster=teams[team],
        must_pick_captain=must_pick_captain,
        get_chemistry_links=get_chemistry_links,
        get_hate_links=get_hate_links,
        chem_data=chem_data,
        remaining_players=sorted_players,
        remaining_captains=remaining_captains,
        teams_with_captain=teams_with_captain
    )

@app.route('/')
def index():
    # Generate a unique draft session if one does not exist
    if 'draft_id' not in session:
        session['draft_id'] = str(uuid.uuid4())  # Assign a unique session ID
        session['teams'] = {team: [] for team in ["Julian", "Kircher", "Carby", "BenT", "Tom", "HarryKirch", "Jmo", "BenR"]}
        session['teams_with_captain'] = {team: False for team in session['teams']}
        session['draft_order'] = list(session['teams'].keys())
        session['remaining_players'] = list(player_stats['Character'])
        session['remaining_captains'] = [p for p in session['remaining_players'] if p in captains]

    return render_template('index.html', teams=session['teams'])

@app.route('/reset_draft')
def reset_draft():
    session.pop('draft_id', None)  # Clear the session
    return redirect(url_for('index'))

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
