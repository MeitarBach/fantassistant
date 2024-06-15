import streamlit as st
import pandas as pd
import requests
import plotly.express as px

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

# Function to fetch data for a single game
@st.cache_data
def fetch_game_data(game_code):
    api_endpoint = f"https://live.euroleague.net/api/Boxscore?gamecode={game_code}&seasoncode=E2023"
    response = requests.get(api_endpoint)
    try:
        data = response.json()
        if 'Stats' in data:
            return data['Stats']
    except Exception as e:
        return None
    return None

# Initialize an empty list to store player data from all games
all_player_data = []

# Start from game code 1 and increment until no valid data is returned
game_code = 1
progress_bar = st.progress(0)
while True:
    game_data = fetch_game_data(game_code)
    if game_data is not None:
        for team_stat in game_data:
            for player in team_stat['PlayersStats']:
                player_info = {
                    'PlayerID': player['Player_ID'].strip(),
                    'PlayerName': player['Player'],
                    'GameCode': game_code,
                    'PIR': player['Valuation']
                }
                all_player_data.append(player_info)
        game_code += 1
        progress_bar.progress(game_code / (game_code + 10))  # Progress bar range handling
    else:
        break

# Create a DataFrame from the collected player data
df = pd.DataFrame(all_player_data)

def calculate_pir_stats(df, last_x_games):
    # Sort the DataFrame by 'GameCode' in descending order so the most recent games are first
    df_sorted = df.sort_values('GameCode', ascending=False)
    
    # Handle the case where only one game is selected
    if last_x_games == 1:
        last_games_stats = df_sorted.groupby('PlayerName').head(last_x_games).groupby('PlayerName').agg({
            'PIR': 'mean'
        }).reset_index()
        last_games_stats['StdDev_PIR'] = 0  # Set standard deviation to 0 for a single game
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'StdDev_PIR']
    else:
        # Group by 'PlayerName' and take the first x games for each player
        last_games_stats = df_sorted.groupby('PlayerName').head(last_x_games).groupby('PlayerName').agg({
            'PIR': ['mean', 'std']
        }).reset_index()
        # Flatten the columns from the MultiIndex
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'StdDev_PIR']
    
    return last_games_stats

def plot_pir_stats(df, last_x_games):
    last_games_stats = calculate_pir_stats(df, last_x_games)

    # Create a Plotly figure with this data
    fig = px.scatter(last_games_stats, x='StdDev_PIR', y='Average_PIR',
                     hover_data={'PlayerName': True, 'Average_PIR': ':.2f', 'StdDev_PIR': ':.2f'},
                     title=f'Average PIR vs. Standard Deviation of PIR (Last {last_x_games} Games)' if last_x_games > 0 else 'Average PIR vs. Standard Deviation of PIR (All Games)',
                     labels={'StdDev_PIR': 'Standard Deviation of PIR', 'Average_PIR': 'Average PIR'},
                     color='Average_PIR',
                     color_continuous_scale=px.colors.sequential.Plasma)

    # Customize the hover template
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br><br>Average PIR: %{y:.2f}<br>StdDev PIR: %{x:.2f}"
    )

    # Improve layout
    fig.update_layout(autosize=False, width=900, height=700, plot_bgcolor='white')

    return fig

def recommend_players(df, last_x_games):
    last_games_stats = calculate_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    top_players = last_games_stats.sort_values(by='Average_PIR', ascending=False).head(10)
    st.subheader("Top 10 Recommended Players")
    st.write(top_players)
    st.write("These players were chosen based on their high average PIR over the selected number of games, indicating consistent high performance.")

# Selection input for the number of games
game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
selected_option = st.selectbox("Select the number of games to consider:", game_options)

if selected_option == 'All games':
    last_x_games = None
    title_option = "All Games"
else:
    last_x_games = int(selected_option.split()[1])
    title_option = f"Last {last_x_games} Games"

# Create tabs for view options
tab2, tab1 = st.tabs(["PIR over StdDev", "PIR Averages DataFrame"])

with tab1:
    last_games_stats = calculate_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    st.subheader(f"Player Performance Statistics ({title_option})")
    st.write(last_games_stats)

with tab2:
    fig = plot_pir_stats(df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    st.plotly_chart(fig)

# Add button for recommending top players
if st.button("Recommend Top 10 Players"):
    recommend_players(df, last_x_games)

# Optional: Provide an option to download the data
st.subheader("Download Player Stats Data")
csv = df.to_csv(index=False)
st.download_button(label="Download CSV", data=csv, file_name='player_stats.csv', mime='text/csv')
