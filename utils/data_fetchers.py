# utils/data_fetchers.py

import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from .s3_utils import load_from_s3, save_to_s3

def fetch_and_save_cr_data():
    """
    Fetch CR data from the dunkest API and save it to S3.
    """
    api_url = ("https://www.dunkest.com/api/stats/table?"
    "season_id=23&"
    "mode=dunkest&"
    "stats_type=tot&"
    "weeks%5B%5D=1&"
    "rounds%5B%5D=1&"
    "rounds%5B%5D=2&"
    "teams%5B%5D=32&"
    "teams%5B%5D=33&"
    "teams%5B%5D=34&"
    "teams%5B%5D=35&"
    "teams%5B%5D=36&"
    "teams%5B%5D=37&"
    "teams%5B%5D=38&"
    "teams%5B%5D=39&"
    "teams%5B%5D=40&"
    "teams%5B%5D=41&"
    "teams%5B%5D=42&"
    "teams%5B%5D=43&"
    "teams%5B%5D=44&"
    "teams%5B%5D=45&"
    "teams%5B%5D=46&"
    "teams%5B%5D=47&"
    "teams%5B%5D=48&"
    "teams%5B%5D=56&"
    "teams%5B%5D=60&"
    "teams%5B%5D=75&"
    "positions%5B%5D=1&"
    "positions%5B%5D=2&"
    "positions%5B%5D=3&"
    "player_search=&"
    "min_cr=4&"
    "max_cr=35&"
    "sort_by=pdk&"
    "sort_order=desc&"
    "iframe=yes")

    response = requests.get(api_url)
    cr_data = response.json()

    cr_df = pd.DataFrame(cr_data)
    cr_df['PlayerName'] = cr_df['first_name'] + ' ' + cr_df['last_name']
    cr_df = cr_df[['PlayerName', 'cr', 'position']].rename(columns={'cr': 'CR'})
    cr_df['CR'] = pd.to_numeric(cr_df['CR'], errors='coerce')
    cr_df['position'] = cr_df['position'].astype(str)

    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"player_cr_data_{today}.csv"

    save_to_s3(filename, cr_df)
    print(f"Player CR and Position data saved to {filename}")
    return cr_df

def fetch_and_update_player_stats(data_file, season_code):
    """
    Fetch new game data from the Euroleague API and update the player stats file in S3
    with deduplication at the player+game level.
    """
    # Load existing data from S3
    df = load_from_s3(data_file)
    if not df.empty:
        print(f"Loaded existing data with {len(df)} rows.")
    else:
        print("No existing data found.")

    last_stored_game_code = df['GameCode'].max() if not df.empty else 0

    # Define game codes to fetch, starting from the last stored one
    new_game_codes = range(last_stored_game_code + 1, last_stored_game_code + 1000)
    all_player_data = []
    consecutive_failures = 0  # Counter for consecutive failures
    max_failures = 5          # Stop fetching after 5 consecutive failures

    for game_code in new_game_codes:
        print(f"Fetching game; gameCode={game_code}")
        api_endpoint = f"https://live.euroleague.net/api/Boxscore?gamecode={game_code}&seasoncode={season_code}"

        try:
            response = requests.get(api_endpoint, timeout=10)
            response.raise_for_status()  # Raises error if status code is not 200

            data = response.json()

            if 'Stats' not in data:
                # If 'Stats' is missing, treat it as a failure
                print(f"No stats found for gameCode={game_code}.")
                consecutive_failures += 1
            else:
                # Reset failure counter on success
                consecutive_failures = 0  

                # Process data into a flat structure
                for team_stat in data['Stats']:
                    for player in team_stat['PlayersStats']:
                        player_info = {
                            'Season': season_code,
                            'GameCode': game_code,
                            'Team': team_stat['Team'],
                            'PlayerID': player.get('Player_ID', '').strip(),
                            'PlayerName': player.get('Player', '').strip(),
                            'PIR': player.get('Valuation', None)
                        }
                        all_player_data.append(player_info)

        except requests.exceptions.ReadTimeout:
            print(f"Timeout for gameCode={game_code}.")
            consecutive_failures += 1
        except (ValueError, requests.exceptions.RequestException) as e:
            print(f"Error for gameCode={game_code}: {e}")
            consecutive_failures += 1
        except Exception as e:
            print(f"Unexpected error for gameCode={game_code}: {e}")
            consecutive_failures += 1

        # Stop fetching if consecutive failures reach the limit
        if consecutive_failures >= max_failures:
            print(f"Reached {max_failures} consecutive failures. Stopping fetch.")
            break

    # Create a new DataFrame for fetched data
    if all_player_data:
        new_df = pd.DataFrame(all_player_data)

        # Combine existing data with new data
        if not df.empty:
            combined_df = pd.concat([df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        # Deduplicate by GameCode + PlayerID
        deduplicated_df = combined_df.drop_duplicates(subset=['GameCode', 'PlayerID'], keep='last')

        # Save deduplicated data back to S3
        save_to_s3(data_file, deduplicated_df)
        print(f"Updated stats file saved with {len(deduplicated_df)} unique rows.")
        return deduplicated_df

    # If no new data was fetched, return the existing df
    return df
