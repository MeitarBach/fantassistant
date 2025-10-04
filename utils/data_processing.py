# utils/data_processing.py

import pandas as pd
import numpy as np
import streamlit as st
from .s3_utils import load_from_s3
from datetime import datetime, timedelta


def load_and_merge_data(player_stats_file: str,
                        cr_prefix: str = "player_cr_data",
                        max_lookback_days: int = 14):
    """
    Loads player stats and merges with the most recent CR data file named like:
    player_cr_data_YYYY-MM-DD.csv. Walks back day-by-day if today's file is missing.
    """
    player_stats_df = load_from_s3(player_stats_file)

    # Find & load the most recent CR file
    cr_df, cr_key = _load_latest_cr_df(prefix=cr_prefix, max_lookback_days=max_lookback_days)
    print(f"Cr data loaded from file {cr_key}")

    # Align names: "Last, First" -> "First Last"
    def format_name(name: str):
        parts = name.split(", ")
        return f"{parts[1].capitalize()} {parts[0].capitalize()}" if len(parts) == 2 else name

    player_stats_df = player_stats_df.copy()
    player_stats_df['PlayerName'] = player_stats_df['PlayerName'].apply(format_name)

    merged_df = pd.merge(player_stats_df, cr_df, on="PlayerName", how="left")
    merged_df['CR'] = pd.to_numeric(merged_df.get('CR'), errors='coerce')
    if 'position' in merged_df.columns:
        merged_df['position'] = merged_df['position'].astype(str)

    return merged_df

def _load_latest_cr_df(prefix: str = "player_cr_data_", max_lookback_days: int = 14):
    """
    Try to load the most recent CR CSV by walking back from today, up to max_lookback_days.
    Returns (cr_df, key) on success.
    Raises FileNotFoundError if none found.
    """
    today = datetime.today().date()
    last_error = None

    for d in range(max_lookback_days + 1):
        day = today - timedelta(days=d)
        key = f"{prefix}_{day.isoformat()}.csv"
        try:
            cr_df = load_from_s3(key)
            if cr_df is not None and not cr_df.empty:
                return cr_df, key
        except FileNotFoundError as e:
            last_error = e
            # try previous day
        except Exception as e:
            # If some transient/read error occurs, skip this date and try earlier
            last_error = e
            # continue loop

    raise FileNotFoundError(
        f"No CR file found with prefix '{prefix}' in the last {max_lookback_days} days."
    ) from last_error

def filter_by_cr_and_position(df, min_cr, max_cr, position):
    """
    Filter the dataframe by CR range and position.
    """
    if position != "All":
        df = df[df['position'] == position]
    return df[(df['CR'] >= min_cr) & (df['CR'] <= max_cr)]

def calculate_pir_stats(df, last_x_games):
    """
    Calculate average PIR and standard deviation for each player
    considering the last X games.
    """
    if 'PIR' not in df.columns:
        print("PIR data is not available. Some features may be limited.")
        return pd.DataFrame()

    df_sorted = df.sort_values('GameCode', ascending=False)

    # If user selects "1" game, standard deviation is always zero for that single game
    if last_x_games == 1:
        last_games_stats = (
            df_sorted.groupby('PlayerName')
                     .head(last_x_games)
                     .groupby('PlayerName')
                     .agg({'PIR': 'mean', 'CR': 'first', 'position': 'first'})
                     .reset_index()
        )
        last_games_stats['StdDev_PIR'] = 0
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'CR', 'position', 'StdDev_PIR']
    else:
        last_games_stats = (
            df_sorted.groupby('PlayerName')
                     .head(last_x_games)
                     .groupby('PlayerName')
                     .agg({'PIR': ['mean', 'std'], 'CR': 'first', 'position': 'first'})
                     .reset_index()
        )
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'StdDev_PIR', 'CR', 'position']

    return last_games_stats

def get_dominant_players(df):
    """
    Filter out players that are 'dominated' by others in terms of PIR.
    A player A is dominated if another player B has a higher Average_PIR
    and a lower StdDev_PIR.
    """
    if df.empty:
        return df

    dominant_players = []
    for i, player in df.iterrows():
        dominated = False
        for j, other_player in df.iterrows():
            if (other_player['Average_PIR'] > player['Average_PIR'] and
                    other_player['StdDev_PIR'] < player['StdDev_PIR']):
                dominated = True
                break
        if not dominated:
            dominant_players.append(player)
    return pd.DataFrame(dominant_players)