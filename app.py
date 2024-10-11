import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np

# Add CSS for hover effect and clickable cursor
st.markdown(
    """
    <style>
    .stSelectbox div[data-baseweb="select"] {
        transition: all 0.2s ease-in-out;
    }
    .stSelectbox div[data-baseweb="select"]:hover {
        box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
        border-color: #007bff;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title of the app
st.title("Euroleague Player Performance")

# Season selection input
season_options = ['2023', '2024']
selected_season = st.selectbox("Select the season:", season_options)

# Function to fetch data for a single game and season
@st.cache_data
def fetch_game_data(game_code, season_code):
    api_endpoint = f"https://live.euroleague.net/api/Boxscore?gamecode={game_code}&seasoncode=E{season_code}"
    response = requests.get(api_endpoint)
    try:
        data = response.json()
        if 'Stats' in data:
            return data['Stats']
    except Exception as e:
        st.warning(f"Failed to fetch data for game code {game_code}: {e}")
        return None
    return None

# Initialize an empty list to store player data from all games
all_player_data = []

# Start from game code 1 and increment until no valid data is returned
game_code = 1
progress_bar = st.progress(0)
max_games = 34  # Assuming a maximum of 34 games per season
while True:
    game_data = fetch_game_data(game_code, selected_season)
    if game_data is not None:
        for team_stat in game_data:
            for player in team_stat['PlayersStats']:
                # Initialize player_info with basic details and map 'Valuation' to 'PIR'
                player_info = {
                    'Season': selected_season,
                    'GameCode': game_code,
                    'Team': team_stat['Team'],
                    'PlayerID': player.get('Player_ID', '').strip(),
                    'PlayerName': player.get('Player', '').strip(),
                    'PIR': player.get('Valuation', None)
                }
                # Include all available stats
                for key, value in player.items():
                    if key not in ['Player_ID', 'Player', 'Valuation']:
                        player_info[key] = value
                all_player_data.append(player_info)
        game_code += 1
        progress_bar.progress(min(game_code / (max_games + 1), 1.0))  # Progress bar range handling
    else:
        break

# Create a DataFrame from the collected player data
df = pd.DataFrame(all_player_data)

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

def get_dominant_players(df):
    if 'PIR' not in df.columns:
        st.warning("Cannot filter dominant players as 'PIR' column is missing.")
        return df
    df_sorted = df.sort_values(['StdDev_PIR', 'Average_PIR'], ascending=[True, False])
    dominant_indices = []
    current_max_pir = -np.inf
    for idx, row in df_sorted.iterrows():
        if row['Average_PIR'] > current_max_pir:
            dominant_indices.append(idx)
            current_max_pir = row['Average_PIR']
    return df_sorted.loc[dominant_indices]

def plot_pir_stats(df, last_x_games, show_dominant):
    last_games_stats = calculate_pir_stats(df, last_x_games)
    if last_games_stats.empty:
        st.warning("No data available to plot PIR stats.")
        return
    if show_dominant:
        last_games_stats = get_dominant_players(last_games_stats)
    fig = px.scatter(last_games_stats, x='StdDev_PIR', y='Average_PIR',
                     hover_data={'PlayerName': True, 'Average_PIR': ':.2f', 'StdDev_PIR': ':.2f'},
                     title=f'Average PIR vs. Standard Deviation of PIR (Last {last_x_games} Games)' if last_x_games > 0 else 'Average PIR vs. Standard Deviation of PIR (All Games)',
                     labels={'StdDev_PIR': 'Standard Deviation of PIR', 'Average_PIR': 'Average PIR'},
                     color='Average_PIR',
                     color_continuous_scale=px.colors.sequential.Plasma)
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br><br>Average PIR: %{y:.2f}<br>StdDev PIR: %{x:.2f}")
    fig.update_layout(autosize=False, width=900, height=700, plot_bgcolor='white')
    st.plotly_chart(fig)

def recommend_players(df, last_x_games):
    last_games_stats = calculate_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    if last_games_stats.empty:
        st.warning("No data available to recommend players.")
        return
    top_players = last_games_stats.sort_values(by='Average_PIR', ascending=False).head(10)
    st.subheader("Top 10 Recommended Players")
    st.write(top_players)
    st.write("These players were chosen based on their high average PIR over the selected number of games, indicating consistent high performance.")

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
    plot_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique(), show_dominant)

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

    st.subheader(f"Boxscore Stats ({selected_option})")
    st.write(filtered_df)

    if st.checkbox("Show Average Stats", key='average_stats'):
        numeric_cols = filtered_df.select_dtypes(include=np.number).columns.tolist()
        avg_stats = filtered_df.groupby(['PlayerName'])[numeric_cols].mean().reset_index()
        st.subheader(f"Average Stats ({selected_option})")
        st.write(avg_stats)

if st.button("Recommend Top 10 Players"):
    recommend_players(df, last_x_games)

csv = df.to_csv(index=False)
st.subheader("Download Player Stats Data")
st.download_button(label="Download CSV", data=csv, file_name='player_stats.csv', mime='text/csv')
