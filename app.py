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

if "show_advanced" not in st.session_state:
    st.session_state.show_advanced = False


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
    recommendations_df = recommend_players_v2(filtered_df)
        # Print top 10
    st.subheader("Top 10 Recommended Players (Exponential-Weighted)")
    st.write(recommendations_df.head(10))


#### TEST ####
# ... the rest of your app code above (tabs, filtering, etc.) ...

# # 5. Enhanced Recommendations UI
# st.markdown("### Enhanced Player Recommendations")

# # Let user set some parameters
# num_recommendations = st.slider(
#     "How many players to display?",
#     min_value=5,
#     max_value=30,
#     value=10
# )

# last_x_games_param = st.slider(
#     "How many recent games to analyze?",
#     min_value=1,
#     max_value=20,
#     value=5
# )

# alpha_param = st.slider(
#     "Recency Emphasis (Alpha)",
#     min_value=0.5,
#     max_value=0.99,
#     value=0.85,
#     step=0.01,
#     help="Higher alpha means older games still have weight; lower alpha emphasizes more recent games."
# )

# weight_eff = st.slider(
#     "Cost Efficiency Weight",
#     min_value=0.0,
#     max_value=5.0,
#     value=2.0,
#     step=0.1,
#     help="How much to reward players who produce a high PIR for a lower CR."
# )

# weight_mean = st.slider(
#     "Average PIR Weight",
#     min_value=0.0,
#     max_value=5.0,
#     value=1.0,
#     step=0.1,
#     help="How important is raw average PIR in the final score?"
# )

# weight_cons = st.slider(
#     "Consistency Penalty Weight",
#     min_value=0.0,
#     max_value=5.0,
#     value=1.0,
#     step=0.1,
#     help="How heavily to penalize high standard error (volatile performance)."
# )

# # Recommendation Button
# if st.button("Get Recommendations"):
#     recs = recommend_players_v2(
#         filtered_df,
#         last_x_games=last_x_games_param,
#         alpha=alpha_param,
#         weight_efficiency=weight_eff,
#         weight_mean_pir=weight_mean,
#         weight_consistency=weight_cons
#     )
#     if recs.empty:
#         st.warning("No recommendations available with the current filters.")
#     else:
#         # Show only top N
#         st.subheader(f"Top {num_recommendations} Recommendations")
#         st.dataframe(recs.head(num_recommendations))

##############

##TEST2###
if st.button("Advanced Recommendations"):
    st.session_state.show_advanced = not st.session_state.show_advanced

if st.session_state.show_advanced:
    st.markdown("### Advanced Recommendation Settings")

    # Put your sliders (and CR filter) inside a form
    with st.form("advanced_recs_form"):
        st.write("Customize your recommendation parameters below.")

        # 1) Number of players to display
        num_recommendations = st.slider(
            "How many players to display?",
            min_value=5,
            max_value=30,
            value=10
        )
        
        # 2) How many recent games to consider
        last_x_games_param = st.slider(
            "Number of recent games",
            min_value=1,
            max_value=20,
            value=5
        )
        
        # 3) Recency emphasis (alpha)
        alpha_param = st.slider(
            "Recency factor (alpha)",
            min_value=0.5,
            max_value=0.99,
            value=0.85,
            step=0.01,
            help="Higher alpha means older games still matter; lower alpha emphasizes recent games more."
        )
        
        # 4) Weights
        weight_eff = st.slider(
            "Cost Efficiency Weight",
            min_value=0.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="How strongly to reward players with high PIR/CR."
        )
        
        weight_mean = st.slider(
            "Average PIR Weight",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="How strongly to emphasize raw average PIR."
        )
        
        weight_cons = st.slider(
            "Consistency Penalty Weight",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="How heavily to penalize volatile players (high StdErr)."
        )

        # 5) CR Filter
        # We'll do a range slider so user can set min/max CR for recommended players
        min_cr_value = float(df['CR'].min()) if not df.empty else 0.0
        max_cr_value = float(df['CR'].max()) if not df.empty else 35.0
        cr_min, cr_max = st.slider(
            "Filter by CR range:",
            min_value=min_cr_value,
            max_value=max_cr_value,
            value=(min_cr_value, max_cr_value),
            step=1.0
        )

        # Final "Generate" button for the form
        generate_button = st.form_submit_button("Generate Recommendations")

    # Only run the recommendation logic after form submission
    if generate_button:
        # 1) Filter the DataFrame by CR
        advanced_filtered_df = df[
            (df['CR'] >= cr_min) & (df['CR'] <= cr_max)
        ].copy()
        
        # 2) Call your recommendation function
        recs_df = recommend_players_v2(
            advanced_filtered_df,
            last_x_games=last_x_games_param,
            alpha=alpha_param,
            weight_efficiency=weight_eff,
            weight_mean_pir=weight_mean,
            weight_consistency=weight_cons
        )

        if recs_df.empty:
            st.warning("No recommendations found with the chosen parameters.")
        else:
            st.subheader(f"Top {num_recommendations} Recommendations")
            st.dataframe(recs_df.head(num_recommendations))
##########

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
