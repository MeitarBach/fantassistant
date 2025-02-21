# utils/data_processing.py

import pandas as pd
import numpy as np
import streamlit as st
from .s3_utils import load_from_s3
from .data_fetchers import fetch_and_save_cr_data

def load_and_merge_data(player_stats_file):
    """
    Loads player stats and merges with CR data from 'player_cr_data.csv'.
    If the CR data is missing, fetch it on the fly.
    """
    player_stats_df = load_from_s3(player_stats_file)

    # Attempt to load from S3; if empty, fetch fresh CR data
    cr_df = load_from_s3("player_cr_data.csv")
    if cr_df.empty:
        cr_df = fetch_and_save_cr_data()

    # Format PlayerName in your stats file to match CR dataset
    def format_name(name):
        parts = name.split(", ")
        return f"{parts[1].capitalize()} {parts[0].capitalize()}" if len(parts) == 2 else name

    player_stats_df['PlayerName'] = player_stats_df['PlayerName'].apply(format_name)

    merged_df = pd.merge(player_stats_df, cr_df, on="PlayerName", how="left")
    merged_df['CR'] = pd.to_numeric(merged_df['CR'], errors='coerce')
    merged_df['position'] = merged_df['position'].astype(str)

    return merged_df

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
