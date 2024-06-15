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

# Calculate the average and standard deviation of PIR for each player across all games
player_stats = df.groupby('PlayerName').agg(
    Average_PIR=pd.NamedAgg(column='PIR', aggfunc='mean'),
    StdDev_PIR=pd.NamedAgg(column='PIR', aggfunc='std')
).reset_index()

# Format the values to two decimal places
player_stats['Average_PIR'] = player_stats['Average_PIR'].round(2)
player_stats['StdDev_PIR'] = player_stats['StdDev_PIR'].round(2)

st.subheader("Player Performance Statistics")
st.write(player_stats)

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
    title='Average PIR vs. Standard Deviation of PIR',
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

# Customize hover template to show player name, average PIR, and standard deviation
fig.update_traces(hovertemplate='Player: %{customdata[0]}<br>Average PIR: %{y:.2f}<br>StdDev PIR: %{x:.2f}')
fig.update_traces(customdata=player_stats[['PlayerName']])

st.plotly_chart(fig)

# Optional: Provide an option to download the data
st.subheader("Download Player Stats Data")
csv = player_stats.to_csv(index=False)
st.download_button(label="Download CSV", data=csv, file_name='player_stats.csv', mime='text/csv')
