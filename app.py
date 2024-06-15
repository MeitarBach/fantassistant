import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Title of the app
st.title("Euroleague Player Performance")

# Function to fetch data for a single game
@st.cache_data
def fetch_game_data(game_code):
    api_endpoint = f"https://live.euroleague.net/api/Boxscore?gamecode={game_code}&seasoncode=E2023"
    response = requests.get(api_endpoint)
    if response and 'Stats' in response.json():
        return response.json()['Stats']
    else:
        return None

# Initialize an empty list to store player data from all games
all_player_data = []

# Start from game code 1 and increment until no data is returned
game_code = 1
progress_bar = st.progress(0)
while game_code < 253:
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
        progress_bar.progress(game_code / 253)
    else:
        break

# Create a DataFrame from the collected player data
df = pd.DataFrame(all_player_data)

def plot_pir_stats(df, last_x_games):
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

    # Create a Plotly figure with this data
    fig = px.scatter(last_games_stats, x='StdDev_PIR', y='Average_PIR',
                     hover_data={'PlayerName': True, 'Average_PIR': ':.2f', 'StdDev_PIR': ':.2f'},
                     title=f'Average PIR vs. Standard Deviation of PIR (Last {last_x_games} Games)',
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

# Selection input for the number of games
game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
selected_option = st.selectbox("Select the number of games to consider:", game_options)

if selected_option == 'All games':
    # Calculate the average and standard deviation of PIR for each player across all games
    player_stats = df.groupby('PlayerName').agg(
        Average_PIR=pd.NamedAgg(column='PIR', aggfunc='mean'),
        StdDev_PIR=pd.NamedAgg(column='PIR', aggfunc='std')
    ).reset_index()

    # Format the values to two decimal places
    player_stats['Average_PIR'] = player_stats['Average_PIR'].round(2)
    player_stats['StdDev_PIR'] = player_stats['StdDev_PIR'].round(2)

    # Create the plot using Plotly
    fig = px.scatter(
        player_stats, 
        x='StdDev_PIR', 
        y='Average_PIR',
        hover_data={
            'PlayerName': True,
            'Average_PIR': ':.2f',
            'StdDev_PIR': ':.2f'
        },
        title='Average PIR vs. Standard Deviation of PIR (All Games)',
        labels={'StdDev_PIR': 'Standard Deviation of PIR', 'Average_PIR': 'Average PIR'},
        color='Average_PIR',
        color_continuous_scale=px.colors.sequential.Plasma
    )

    # Improve layout
    fig.update_traces(
        marker=dict(size=12, opacity=0.6, line=dict(width=1, color='DarkSlateGrey'))
    )
    fig.update_layout(
        autosize=False, 
        width=900, 
        height=700, 
        plot_bgcolor='white',
        margin=dict(l=40, r=40, b=40, t=40),
        xaxis=dict(title='Standard Deviation of PIR'),
        yaxis=dict(title='Average PIR')
    )

    st.plotly_chart(fig)
else:
    last_x_games = int(selected_option.split()[1])
    fig = plot_pir_stats(df, last_x_games)
    st.plotly_chart(fig)

# Optional: Provide an option to download the data
st.subheader("Download Player Stats Data")
csv = df.to_csv(index=False)
st.download_button(label="Download CSV", data=csv, file_name='player_stats.csv', mime='text/csv')
