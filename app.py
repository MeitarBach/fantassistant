import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY"]
AWS_SECRET_KEY = st.secrets["AWS_SECRET_KEY"]
BUCKET_NAME = 'fantassistant'

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def save_to_s3(filename, df):
    csv_buffer = df.to_csv(index=False)
    try:
        s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=csv_buffer)
        st.success(f"File saved to S3: {filename}")
    except (NoCredentialsError, ClientError) as e:
        st.error(f"Failed to upload {filename} to S3: {e}")

def load_from_s3(filename):
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=filename)
        df = pd.read_csv(response['Body'])
        st.success(f"Loaded file from S3: {filename}")
        return df
    except ClientError as e:
        st.warning(f"File not found in S3: {filename}")
        return pd.DataFrame()

st.title("Euroleague Player Performance")

season_options = ['2023', '2024']
selected_season = st.selectbox("Season:", season_options)

data_file = f'player_stats_{selected_season}.csv'

df = load_from_s3(data_file)
if not df.empty:
    last_stored_game_code = df['GameCode'].max()
    st.write(f"Loaded data up to game code {last_stored_game_code}")
else:
    last_stored_game_code = 0
    st.write("No existing data found. Fetching data from scratch.")

new_game_codes = range(last_stored_game_code + 1, last_stored_game_code + 1000)  # Set a high limit

all_player_data = []

if new_game_codes:
    progress_bar = st.progress(0)
    for idx, game_code in enumerate(new_game_codes, start=1):
        api_endpoint = f"https://live.euroleague.net/api/Boxscore?gamecode={game_code}&seasoncode=E{selected_season}"
        response = requests.get(api_endpoint)
        try:
            data = response.json()
            if 'Stats' in data:
                for team_stat in data['Stats']:
                    for player in team_stat['PlayersStats']:
                        player_info = {
                            'Season': selected_season,
                            'GameCode': game_code,
                            'Team': team_stat['Team'],
                            'PlayerID': player.get('Player_ID', '').strip(),
                            'PlayerName': player.get('Player', '').strip(),
                            'PIR': player.get('Valuation', None)
                        }
                        for key, value in player.items():
                            if key not in ['Player_ID', 'Player', 'Valuation']:
                                player_info[key] = value
                        all_player_data.append(player_info)
                progress_bar.progress(idx / len(new_game_codes))
        except Exception as e:
            st.warning(f"Error fetching data for game code {game_code}: {e}")
            break

    if all_player_data:
        new_df = pd.DataFrame(all_player_data)
        df = pd.concat([df, new_df], ignore_index=True)
        save_to_s3(data_file, df)
else:
    st.write("Data is already up to date.")

def calculate_pir_stats(df, last_x_games):
    if 'PIR' not in df.columns:
        st.warning("PIR data is not available. Some features may be limited.")
        return pd.DataFrame()
    df_sorted = df.sort_values('GameCode', ascending=False)
    if last_x_games == 1:
        last_games_stats = df_sorted.groupby('PlayerName').head(last_x_games).groupby('PlayerName').agg({
            'PIR': 'mean'
        }).reset_index()
        last_games_stats['StdDev_PIR'] = 0
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'StdDev_PIR']
    else:
        last_games_stats = df_sorted.groupby('PlayerName').head(last_x_games).groupby('PlayerName').agg({
            'PIR': ['mean', 'std']
        }).reset_index()
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'StdDev_PIR']
    return last_games_stats

game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
selected_option = st.selectbox("Select the number of games to consider:", game_options)

if selected_option == 'All games':
    last_x_games = None
else:
    last_x_games = int(selected_option.split()[1])

show_dominant = st.checkbox("Show Only Dominant Players")

tab1, tab2, tab3 = st.tabs(["PIR over StdDev", "PIR Averages DataFrame", "Detailed Boxscores"])

with tab2:
    last_games_stats = calculate_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    st.subheader("Player Performance Statistics")
    st.write(last_games_stats)

with tab1:
    last_games_stats = calculate_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    if not last_games_stats.empty:
        if show_dominant:
            last_games_stats = get_dominant_players(last_games_stats)
        fig = px.scatter(last_games_stats, x='StdDev_PIR', y='Average_PIR',
                         hover_data={'PlayerName': True, 'Average_PIR': ':.2f', 'StdDev_PIR': ':.2f'},
                         title=f'Average PIR vs. Standard Deviation of PIR (Last {last_x_games} Games)' if last_x_games else 'Average PIR vs. Standard Deviation of PIR (All Games)',
                         labels={'StdDev_PIR': 'Standard Deviation of PIR', 'Average_PIR': 'Average PIR'},
                         color='Average_PIR',
                         color_continuous_scale=px.colors.sequential.Plasma)
        fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Average PIR: %{y:.2f}<br>StdDev PIR: %{x:.2f}")
        fig.update_layout(autosize=False, width=900, height=700, plot_bgcolor='white')
        st.plotly_chart(fig)
    else:
        st.warning("No data available to plot PIR stats.")

with tab3:
    st.header("Detailed Boxscores")
    boxscore_game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
    boxscore_selected_option = st.selectbox("Select the games to view:", boxscore_game_options, key='boxscore_games')

    if boxscore_selected_option == 'All games':
        filtered_df = df.copy()
    else:
        last_x_games = int(boxscore_selected_option.split()[1])
        latest_game_codes = sorted(df['GameCode'].unique(), reverse=True)[:last_x_games]
        filtered_df = df[df['GameCode'].isin(latest_game_codes)]

    st.subheader(f"Boxscore Stats ({boxscore_selected_option})")
    st.write(filtered_df)

    if st.checkbox("Show Average Stats", key='average_stats'):
        numeric_cols = filtered_df.select_dtypes(include=np.number).columns.tolist()
        avg_stats = filtered_df.groupby(['PlayerName'])[numeric_cols].mean().reset_index()
        st.subheader("Average Stats")
        st.write(avg_stats)

def recommend_players(df, last_x_games):
    last_games_stats = calculate_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    if last_games_stats.empty:
        st.warning("No data available to recommend players.")
        return
    top_players = last_games_stats.sort_values(by='Average_PIR', ascending=False).head(10)
    st.subheader("Top 10 Recommended Players")
    st.write(top_players[['PlayerName', 'Average_PIR', 'StdDev_PIR']])

if st.button("Recommend Top 10 Players"):
    recommend_players(df, last_x_games)

csv = df.to_csv(index=False)
st.subheader("Download Player Stats Data")
st.download_button(label="Download CSV", data=csv, file_name='player_stats.csv', mime='text/csv')
