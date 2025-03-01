import math
import ast

def min_max_scale_scores(scores):
    # Extract all metric names
    metrics = next(iter(scores.values())).keys()  # Get the keys from the first player's dictionary

    # Find min and max for each metric
    min_max = {metric: (float('inf'), float('-inf')) for metric in metrics}

    for player_stats in scores.values():
        for metric, value in player_stats.items():
            min_val, max_val = min_max[metric]
            min_max[metric] = (min(value, min_val), max(value, max_val))

    # Scale values to range [0,1]
    scaled_scores = {}
    for player, player_stats in scores.items():
        scaled_scores[player] = {}
        for metric, value in player_stats.items():
            min_val, max_val = min_max[metric]
            # Avoid division by zero if all values are the same
            scaled_value = 0 if min_val == max_val else (value - min_val) / (max_val - min_val)
            scaled_scores[player][metric] = round(scaled_value, 2)  # Round to 2 decimals

    return scaled_scores

def calculate_chemistry_metric(current_team, player, remaining_players, df, k=0.9, x0=4.5, neg_chem_weight=.5):
    # Generate available players
    available_players = remaining_players
    available_players = list(set(remaining_players) - set([player]))

    # Calculate the weight based on the size of the current team
    team_size = len(current_team)
    weight_current_team = 1 / (1 + math.exp(-k * (team_size - x0)))
    weight_available_players = 1 - weight_current_team
    weight_unique_chem = weight_available_players

    # Get the player's row from the dataframe
    player_row = df[df['Character Name'] == player]
    
    # Check if the player exists in the DataFrame
    if player_row.empty:
        # Handle missing player (e.g., assign a default chemistry score)
        print(f"Warning: Player '{player}' not found in chemistry data. Assigning default chemistry score.")
        return 0.0  # Default chemistry score for missing players

    player_row = player_row.iloc[0]  # Safe to access now

    # Ensure Chemistry is a list or set
    chemistry_list = player_row['Chemistry'] if isinstance(player_row['Chemistry'], (list, set)) else []
    hate_list = player_row['Hate'] if isinstance(player_row['Hate'], (list, set)) else []

    # Calculate positive and negative chemistry connections with the current team
    positive_chem_current_team = len(set(chemistry_list).intersection(current_team))
    negative_chem_current_team = len(set(hate_list).intersection(current_team)) * neg_chem_weight

    # Calculate positive and negative chemistry connections with the available players
    positive_chem_available_players = len(set(chemistry_list).intersection(available_players))
    negative_chem_available_players = len(set(hate_list).intersection(available_players)) * neg_chem_weight

    # Calculate the number of unique chemistry connections the player would add to the current team
    unique_chem = len(set(chemistry_list) - set([item for string in current_team for item in df.loc[df['Character Name'] == string, 'Chemistry'].values[0] if isinstance(item, (list, set))]))

    # Calculate the chemistry metric
    chemistry_metric = (
        weight_current_team * (positive_chem_current_team - negative_chem_current_team) +
        weight_available_players * (positive_chem_available_players - negative_chem_available_players) +
        weight_unique_chem * (unique_chem)
    )

    # Store the chemistry metric for the player
    chemistry_metric = round(chemistry_metric, 2)

    return chemistry_metric

def create_player_tuples(scores):
    # Define the metrics to extract
    metrics = ['chem_score', 'slugging', 'charge_hit_power', 'slap_hit_power', 'speed', 'home_runs', 'pitching_stamina']

    player_tuples = []
    for player, stats in scores.items():
        # Calculate total score (sum of all metrics, modify as needed)
        total_score = (stats['chem_score'] * 1) + (stats['slugging'] * 1) + (stats['charge_hit_power'] * 1) + (stats['slap_hit_power'] * 1) + (stats['speed'] * 1) + (stats['home_runs'] * 1) + (stats['pitching_stamina'] * 1)

        # Extract values for required metrics, defaulting to 0 if missing
        values = [stats.get(metric, 0) for metric in metrics]

        # Create tuple: (player, total_score, metric values...)
        player_tuples.append((player, total_score, *values))

    return player_tuples

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