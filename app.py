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
        print(f"File saved to S3: {filename}")
    except (NoCredentialsError, ClientError) as e:
        print(f"Failed to upload {filename} to S3: {e}")

def load_from_s3(filename):
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=filename)
        df = pd.read_csv(response['Body'])
        print(f"Loaded file from S3: {filename}")
        return df
    except ClientError as e:
        print(f"File not found in S3: {filename}")
        return pd.DataFrame()

def fetch_and_save_cr_data():
    api_url = "https://www.dunkest.com/api/stats/table?season_id=17&mode=dunkest&stats_type=tot&weeks%5B%5D=2&rounds%5B%5D=1&rounds%5B%5D=2&rounds%5B%5D=3&teams%5B%5D=31&teams%5B%5D=32&teams%5B%5D=33&teams%5B%5D=34&teams%5B%5D=35&teams%5B%5D=36&teams%5B%5D=37&teams%5B%5D=38&teams%5B%5D=39&teams%5B%5D=40&teams%5B%5D=41&teams%5B%5D=42&teams%5B%5D=43&teams%5B%5D=44&teams%5B%5D=45&teams%5B%5D=47&teams%5B%5D=48&teams%5B%5D=60&positions%5B%5D=1&positions%5B%5D=2&positions%5B%5D=3&player_search=&min_cr=4&max_cr=35&sort_by=pdk&sort_order=desc&iframe=yes"
    response = requests.get(api_url)
    cr_data = response.json()
    
    cr_df = pd.DataFrame(cr_data)
    cr_df['PlayerName'] = cr_df['first_name'] + ' ' + cr_df['last_name']
    cr_df = cr_df[['PlayerName', 'CR']]
    save_to_s3("player_cr_data.csv", cr_df)
    return cr_df

def load_and_merge_data(player_stats_file):
    player_stats_df = load_from_s3(player_stats_file)
    cr_df = load_from_s3("player_cr_data.csv")
    if cr_df.empty:
        cr_df = fetch_and_save_cr_data()
    
    def format_name(name):
        parts = name.split(", ")
        return f"{parts[1].capitalize()} {parts[0].capitalize()}" if len(parts) == 2 else name
    
    player_stats_df['PlayerName'] = player_stats_df['PlayerName'].apply(format_name)
    merged_df = pd.merge(player_stats_df, cr_df, on="PlayerName", how="left")
    return merged_df

def filter_by_cr_range(df, min_cr, max_cr):
    """Filter the DataFrame to include players with CR within the specified range."""
    return df[(df['CR'] >= min_cr) & (df['CR'] <= max_cr)]

def calculate_pir_stats(df, last_x_games):
    if 'PIR' not in df.columns:
        print("PIR data is not available. Some features may be limited.")
        return pd.DataFrame()
    df_sorted = df.sort_values('GameCode', ascending=False)
    if last_x_games == 1:
        last_games_stats = df_sorted.groupby('PlayerName').head(last_x_games).groupby('PlayerName').agg({
            'PIR': 'mean',
            'CR': 'first'
        }).reset_index()
        last_games_stats['StdDev_PIR'] = 0
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'CR', 'StdDev_PIR']
    else:
        last_games_stats = df_sorted.groupby('PlayerName').head(last_x_games).groupby('PlayerName').agg({
            'PIR': ['mean', 'std'],
            'CR': 'first'
        }).reset_index()
        last_games_stats.columns = ['PlayerName', 'Average_PIR', 'StdDev_PIR', 'CR']
    return last_games_stats

def recommend_players(df, last_x_games=10, lambda_decay=0.1, w1=4, w2=1.5, w3=1):
    if last_x_games is None or last_x_games <= 0:
        last_x_games = 10

    recommendations = []
    grouped = df.groupby('PlayerName')
    
    for name, group in grouped:
        recent_games = group.tail(last_x_games)
        
        if recent_games.empty:
            continue
        
        pir_avg = recent_games['PIR'].mean() if len(recent_games) > 0 else 0
        pir_std = recent_games['PIR'].std(ddof=1) if len(recent_games) > 1 else 0
        stderr = pir_std / np.sqrt(len(recent_games)) if len(recent_games) > 0 else float('inf')
        
        cr = group['CR'].iloc[0] if 'CR' in group else float('inf')
        score = (w1 * pir_avg) + (w2 / cr) - (w3 * stderr) if cr > 0 else 0
        
        recommendations.append({
            'PlayerName': name,
            'PIR_Avg': pir_avg,
            'StdErr': stderr,
            'CR': cr,
            'Score': score
        })
    
    recommendations_df = pd.DataFrame(recommendations).sort_values(by='Score', ascending=False)
    st.subheader("Top 10 Recommended Players Based on Weighted Formula")
    st.write(recommendations_df[['PlayerName', 'PIR_Avg', 'StdErr', 'CR', 'Score']].head(10))

st.title("Euroleague Player Performance")

season_options = ['2023', '2024']
selected_season = st.selectbox("Season:", season_options, index=1)

data_file = f'player_stats_{selected_season}.csv'
df = load_and_merge_data(data_file)
if not df.empty:
    last_stored_game_code = df['GameCode'].max()
    st.write(f"Loaded data up to game code {last_stored_game_code}")
else:
    last_stored_game_code = 0
    st.write("No existing data found. Fetching data from scratch.")

# CR Range Slider
st.subheader("Filter Players by CR Range")
min_cr, max_cr = st.slider("Select CR range:", min_value=float(df['CR'].min()), max_value=float(df['CR'].max()), value=(float(df['CR'].min()), float(df['CR'].max())))
filtered_df = filter_by_cr_range(df, min_cr, max_cr)

game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
selected_option = st.selectbox("Select the number of games to consider:", game_options)

if selected_option == 'All games':
    last_x_games = None
else:
    last_x_games = int(selected_option.split()[1])

show_dominant = st.checkbox("Show Only Dominant Players")

tab1, tab2, tab3 = st.tabs(["PIR over StdDev", "PIR Averages DataFrame", "Detailed Boxscores"])

with tab2:
    last_games_stats = calculate_pir_stats(filtered_df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    st.subheader("Player Performance Statistics")
    st.write(last_games_stats)

with tab1:
    last_games_stats = calculate_pir_stats(filtered_df, last_x_games if last_x_games is not None else df['GameCode'].nunique())
    if not last_games_stats.empty:
        if show_dominant:
            last_games_stats = get_dominant_players(last_games_stats)
        
        fig = px.scatter(last_games_stats, x='StdDev_PIR', y='Average_PIR',
                         color='Average_PIR',
                         hover_data={'PlayerName': True, 'Average_PIR': ':.2f', 'StdDev_PIR': ':.2f'},
                         custom_data=['PlayerName', 'Average_PIR', 'StdDev_PIR', 'CR'],
                         title=f'Average PIR vs. Standard Deviation of PIR (Last {last_x_games} Games)' if last_x_games else 'Average PIR vs. Standard Deviation of PIR (All Games)',
                         labels={'StdDev_PIR': 'Standard Deviation of PIR', 'Average_PIR': 'Average PIR'},
                         color_continuous_scale=px.colors.sequential.Plasma)
        
        # Update hovertemplate to display CR
        fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Average PIR: %{customdata[1]:.2f}<br>StdDev PIR: %{customdata[2]:.2f}<br>CR: %{customdata[3]:.2f}")
        
        fig.update_layout(autosize=False, width=900, height=700, plot_bgcolor='white')
        st.plotly_chart(fig)
    else:
        print("No data available to plot PIR stats.")

with tab3:
    st.header("Detailed Boxscores")
    boxscore_game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
    boxscore_selected_option = st.selectbox("Select the games to view:", boxscore_game_options, key='boxscore_games')

    if boxscore_selected_option == 'All games':
        filtered_df_boxscore = filtered_df.copy()
    else:
        last_x_games_boxscore = int(boxscore_selected_option.split()[1])
        latest_game_codes = sorted(df['GameCode'].unique(), reverse=True)[:last_x_games_boxscore]
        filtered_df_boxscore = filtered_df[filtered_df['GameCode'].isin(latest_game_codes)]

    st.subheader(f"Boxscore Stats ({boxscore_selected_option})")
    st.write(filtered_df_boxscore)

    if st.checkbox("Show Average Stats", key='average_stats'):
        numeric_cols = filtered_df_boxscore.select_dtypes(include=np.number).columns.tolist()
        avg_stats = filtered_df_boxscore.groupby(['PlayerName'])[numeric_cols].mean().reset_index()
        st.subheader("Average Stats")
        st.write(avg_stats)

# Recommend Top Players using the new scoring formula
if st.button("Recommend Top 10 Players"):
    recommend_players(filtered_df, last_x_games)

# CSV Download Option for Player Stats Data
csv = df.to_csv(index=False)
st.subheader("Download Player Stats Data")
st.download_button(label="Download CSV", data=csv, file_name='player_stats.csv', mime='text/csv')

