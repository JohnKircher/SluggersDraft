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

# Chemistry metric function
def calculate_chemistry_metric(current_team, player, remaining_players, df, k=0.9, x0=4.5, neg_chem_weight=.5):
    # Generate available players
    available_players = remaining_players
    available_players.remove(player)

    # Calculate the weight based on the size of the current team
    team_size = len(current_team)
    weight_current_team = 1 / (1 + math.exp(-k * (team_size - x0)))
    weight_available_players = 1 - weight_current_team
    weight_unique_chem = weight_available_players

    # Get the player's row from the dataframe
    player_row = df[df['Character Name'] == player].iloc[0]

    # Calculate positive and negative chemistry connections with the current team
    positive_chem_current_team = len(set(player_row['Chemistry']).intersection(current_team))
    negative_chem_current_team = len(set(player_row['Hate']).intersection(current_team)) * neg_chem_weight

    # Calculate positive and negative chemistry connections with the available players
    positive_chem_available_players = len(set(player_row['Chemistry']).intersection(available_players))
    negative_chem_available_players = len(set(player_row['Hate']).intersection(available_players)) * neg_chem_weight

    # Calculate the number of unique chemistry connections the player would add to the current team
    unique_chem = len(set(player_row['Chemistry']) - set([item for string in current_team for item in df.loc[df['Character Name'] == string, 'Chemistry'].sum()]))


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