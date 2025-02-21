# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Import utils
from utils.data_fetchers import fetch_and_update_player_stats
from utils.data_processing import (
    load_and_merge_data,
    filter_by_cr_and_position,
    calculate_pir_stats,
    get_dominant_players
)
from utils.recommendations import (recommend_players, recommend_players_v2)

st.title("EuroLeague Fantassistant")

# 1. Season Selection
st.markdown("### Season Selection")
season_options = ['2023', '2024']
selected_season = st.selectbox("Pick a season:", season_options, index=1)
season_code = f"E{selected_season}"

# 2. File Name and Data Loading
data_file = f'player_stats_{selected_season}.csv'
df = fetch_and_update_player_stats(data_file, season_code)
df = load_and_merge_data(data_file)

if not df.empty:
    last_stored_game_code = df['GameCode'].max()
    print(f"Data loaded up to game code - `{last_stored_game_code}`")
else:
    print("No existing data found. Fetching from scratch...")

# 3. Player Filters
st.markdown("### Player Filters")
if not df.empty:
    min_cr_value = float(df['CR'].min())
    max_cr_value = float(df['CR'].max())
else:
    min_cr_value = 0
    max_cr_value = 35  # default fallback

min_cr, max_cr = st.slider(
    "CR Range:",
    min_value=min_cr_value,
    max_value=max_cr_value,
    value=(min_cr_value, max_cr_value)
)

position_options = ["All"] + sorted(df['position'].dropna().unique()) if not df.empty else ["All"]
selected_position = st.selectbox("Position:", position_options)

filtered_df = filter_by_cr_and_position(df, min_cr, max_cr, selected_position)

st.markdown("### Number of Games to Consider")
game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
selected_option = st.selectbox("Games to Consider:", game_options)

if selected_option == 'All games':
    last_x_games = None
else:
    last_x_games = int(selected_option.split()[1])

show_dominant = st.checkbox("Show Dominant Players Only")

# 4. Analysis Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "PIR & Std. Deviation",
    "PIR & CR",
    "PIR Averages",
    "Boxscores"
])

# -- Tab 1: PIR vs. StdDev --
with tab1:
    st.subheader("PIR vs. Standard Deviation")
    last_games = last_x_games if last_x_games else df['GameCode'].nunique()
    last_games_stats = calculate_pir_stats(filtered_df, last_games)

    if not last_games_stats.empty:
        if show_dominant:
            last_games_stats = get_dominant_players(last_games_stats)
        
        fig = px.scatter(
            last_games_stats,
            x='StdDev_PIR',
            y='Average_PIR',
            color='Average_PIR',
            hover_data={
                'PlayerName': True,
                'Average_PIR': ':.2f',
                'StdDev_PIR': ':.2f',
                'position': True,
                'CR': True
            },
            custom_data=['PlayerName', 'Average_PIR', 'StdDev_PIR', 'position', 'CR'],
            title=f'Average PIR vs. Std. Deviation (Last {last_games} Games)',
            labels={'StdDev_PIR': 'Std. Dev. of PIR', 'Average_PIR': 'Average PIR'},
            color_continuous_scale=px.colors.sequential.Plasma
        )
        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>Avg PIR: %{customdata[1]:.2f}"
                          "<br>Std. Dev.: %{customdata[2]:.2f}<br>Position: %{customdata[3]}"
                          "<br>CR: %{customdata[4]:.2f}"
        )
        fig.update_layout(
            autosize=False,
            width=900,
            height=700,
            plot_bgcolor='white'
        )
        st.plotly_chart(fig)
    else:
        st.info("Not enough data to display PIR vs. Standard Deviation.")

# -- Tab 2: PIR vs. CR --
with tab2:
    st.subheader("PIR vs. CR (Cost)")
    last_games = last_x_games if last_x_games else df['GameCode'].nunique()
    last_games_stats = calculate_pir_stats(filtered_df, last_games)
    if not last_games_stats.empty:
        fig = px.scatter(
            last_games_stats,
            x='CR',
            y='Average_PIR',
            color='Average_PIR',
            hover_data={
                'PlayerName': True,
                'Average_PIR': ':.2f',
                'CR': ':.2f',
                'position': True
            },
            custom_data=['PlayerName', 'Average_PIR', 'CR', 'position'],
            title=f'Average PIR vs. CR (Last {last_games} Games)',
            labels={'CR': 'Cost (CR)', 'Average_PIR': 'Average PIR'},
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>Avg PIR: %{customdata[1]:.2f}"
                          "<br>CR: %{customdata[2]:.2f}<br>Position: %{customdata[3]}"
        )
        fig.update_layout(
            autosize=False,
            width=900,
            height=700,
            plot_bgcolor='white'
        )
        st.plotly_chart(fig)
    else:
        st.info("Not enough data to display PIR vs. CR.")

# -- Tab 3: PIR Averages DataFrame --
with tab3:
    st.subheader("Player Performance (Averages)")
    last_games = last_x_games if last_x_games else df['GameCode'].nunique()
    last_games_stats = calculate_pir_stats(filtered_df, last_games)
    if not last_games_stats.empty:
        st.dataframe(last_games_stats)
    else:
        st.info("No average PIR data available.")

# -- Tab 4: Detailed Boxscores --
with tab4:
    st.subheader("Boxscores")
    boxscore_game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
    boxscore_selected_option = st.selectbox("Games to Display:", boxscore_game_options, key='boxscore_games')

    if boxscore_selected_option == 'All games':
        filtered_df_boxscore = filtered_df.copy()
    else:
        last_x_games_boxscore = int(boxscore_selected_option.split()[1])
        latest_game_codes = sorted(df['GameCode'].unique(), reverse=True)[:last_x_games_boxscore]
        filtered_df_boxscore = filtered_df[filtered_df['GameCode'].isin(latest_game_codes)]

    st.markdown(f"**Boxscore Stats** ({boxscore_selected_option})")
    st.dataframe(filtered_df_boxscore)

    if st.checkbox("View Average Stats", key='average_stats'):
        numeric_cols = filtered_df_boxscore.select_dtypes(include=np.number).columns.tolist()
        avg_stats = (
            filtered_df_boxscore
            .groupby(['PlayerName', 'position'])[numeric_cols]
            .mean()
            .reset_index()
        )
        st.markdown("**Average Stats by Player & Position**")
        st.dataframe(avg_stats)

# 5. Recommendations
st.markdown("### Player Recommendations")
if st.button("Get Top 10 Recommendations"):
    # You can also call the old version:
    # recommend_players(filtered_df, last_x_games)
    recommend_players_v2(filtered_df)

# 6. Data Download
if not df.empty:
    st.markdown("### Download Player Data")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='player_stats.csv',
        mime='text/csv'
    )
