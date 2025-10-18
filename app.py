# app.py

import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# from datetime import datetime
# from utils.pd_utils import select_cols
from views.main_view import main_view
from views.user_sidebar import user_sidebar

# # Import utils
# from utils.data_processing import (
#     load_and_merge_data,
#     filter_by_cr_and_position,
#     calculate_pir_stats,
#     get_dominant_players,
#     load_injuries_df,
#     add_injury_badge
# )
# from utils.recommendations import (recommend_players, recommend_players_v2)

st.set_page_config(
    page_title="EuroGuru",
    page_icon="images/favicon.png"
)

# # ---------- Auth helpers ----------
# def get_user_info():
#     info = st.experimental_user or {}
#     return info, info.get("is_logged_in", False)

# def user_sidebar():
#     user, is_logged_in = get_user_info()

#     # Sidebar header (brand)
#     with st.sidebar:
#         st.markdown(
#             """
#             <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
#               <div style="font-size:22px">🏀</div>
#               <div style="font-weight:700;font-size:18px;">EuroGuru</div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#         # User badge / login
#         with st.container(border=True):
#             if is_logged_in:
#                 pic = user.get("picture")
#                 name = user.get("name") or user.get("email") or "User"
#                 email = user.get("email", "")

#                 cols = st.columns([1, 3])
#                 with cols[0]:
#                     if pic:
#                         st.image(pic, width=44)
#                     else:
#                         st.markdown(
#                             '<div style="font-size:30px;line-height:44px;text-align:center;">👤</div>',
#                             unsafe_allow_html=True,
#                         )
#                 with cols[1]:
#                     st.markdown(f"**{name}**")
#                     if email:
#                         st.caption(email)

#                 st.button("Log out", use_container_width=True, on_click=st.logout)
#             else:
#                 st.markdown("**Not signed in**")
#                 st.caption("Log in to save preferences and personalize recommendations.")
#                 st.button("Log in", use_container_width=True, on_click=lambda: st.login("auth0"))

#         st.divider()

#         # ----- Account / Menu (ready for more items) -----
#         st.subheader("Account")
#         # Example status chip
#         tier = st.session_state.get("subscription_tier", "Free")
#         st.markdown(
#             f"""
#             <span style="padding:4px 8px;border-radius:999px;border:1px solid #ddd;
#                          font-size:12px;background:#f7f7f7;">Plan: <b>{tier}</b></span>
#             """,
#             unsafe_allow_html=True,
#         )
#         st.write("")  # spacer
#         menu = st.radio(
#             "Menu",
#             ["Overview", "Subscription", "Preferences", "Privacy"],
#             label_visibility="collapsed",
#         )

#         # Optional: context-specific sidebar content (placeholder)
#         if menu == "Overview":
#             st.caption("Quick links and recent activity will appear here.")
#         elif menu == "Subscription":
#             st.caption("Manage your plan and billing (coming soon).")
#             st.button("Upgrade to Pro", use_container_width=True, disabled=True)
#         elif menu == "Preferences":
#             st.caption("Personalize recommendations (coming soon).")
#         else:
#             st.caption("Manage data & export (coming soon).")

#         st.divider()
#         with st.expander("Auth debug"):
#             st.json(st.experimental_user or {})

# Call this once, before main content:
user_sidebar()
main_view()

# if "show_advanced" not in st.session_state:
#     st.session_state.show_advanced = False


# st.title("EuroGuru")
# st.header("Euroleague Fantasy Challenge Assistant & Analytics Tool")
# st.markdown("""
#             **EuroGuru is your go-to assistant for the Euroleague Fantasy Challenge.** 
#             Access player stats, boxscores, injury reports, and interactive data visualizations.
#             Explore advanced player analytics, smart filters, lineup recommendations, and performance forecasting.
#             Everything you need to build the perfect Euroleague Fantasy team roster, all in one place.
#             """)

# # 1. Season Selection
# st.markdown("### Season Selection")
# season_options = ['2023', '2024', '2025']
# selected_season = st.selectbox("Pick a season:", season_options, index=(len(season_options)-1))
# season_code = f"E{selected_season}"

# # 2. File Name and Data Loading
# data_file = f'player_stats_{selected_season}.csv'
# cr_file_prefix = 'player_cr_data'
# df = load_and_merge_data(data_file, cr_file_prefix)

# if not df.empty:
#     last_stored_game_code = df['GameCode'].max()
#     print(f"Data loaded up to game code - `{last_stored_game_code}`")
# else:
#     print("No existing data found. Fetching from scratch...")

# # 3. Player Filters
# st.markdown("### Player Filters")
# if not df.empty:
#     min_cr_value = float(df['CR'].min())
#     max_cr_value = float(df['CR'].max())
# else:
#     min_cr_value = 0
#     max_cr_value = 35  # default fallback

# min_cr, max_cr = st.slider(
#     "CR Range:",
#     min_value=min_cr_value,
#     max_value=max_cr_value,
#     value=(min_cr_value, max_cr_value)
# )

# position_options = ["All"] + sorted(df['position'].dropna().unique()) if not df.empty else ["All"]
# selected_position = st.selectbox("Position:", position_options)

# filtered_df = filter_by_cr_and_position(df, min_cr, max_cr, selected_position)

# st.markdown("### Number of Games to Consider")
# game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
# selected_option = st.selectbox("Games to Consider:", game_options)

# if selected_option == 'All games':
#     last_x_games = None
# else:
#     last_x_games = int(selected_option.split()[1])

# show_dominant = st.checkbox("Show Dominant Players Only")

# # 4. Analysis Tabs
# tab1, tab2, tab3, tab4, tab5 = st.tabs([
#     "PIR & Std. Deviation",
#     "PIR & CR",
#     "PIR Averages",
#     "Boxscores",
#     "Injuries"
# ])


# # -- Tab 1: PIR vs. StdDev --
# with tab1:
#     st.subheader("PIR vs. Standard Deviation")
#     last_games = last_x_games if last_x_games else df['GameCode'].nunique()
#     last_games_stats = calculate_pir_stats(filtered_df, last_games)
#     last_games_stats = add_injury_badge(last_games_stats)

#     if not last_games_stats.empty:
#         if show_dominant:
#             last_games_stats = get_dominant_players(last_games_stats)
        
#         fig = px.scatter(
#             last_games_stats,
#             x='StdDev_PIR',
#             y='Average_PIR',
#             color='Average_PIR',
#             hover_data={
#                 'PlayerName': True,
#                 'Average_PIR': ':.2f',
#                 'StdDev_PIR': ':.2f',
#                 'position': True,
#                 'CR': True,
#                 # 'InjuryStatus': True,   # new
#                 # 'Injury': True          # new
#             },
#         custom_data=['PlayerName','Average_PIR','StdDev_PIR','position','CR','InjuryBadge'],
#         title=f'Average PIR vs. Std. Deviation (Last {last_games} Games)',
#         labels={'StdDev_PIR': 'Std. Dev. of PIR', 'Average_PIR': 'Average PIR'},
#         color_continuous_scale=px.colors.sequential.Plasma)
#         fig.update_traces(
#             hovertemplate="<b>%{customdata[0]}</b>"
#                         "<br>Avg PIR: %{customdata[1]:.2f}"
#                         "<br>Std. Dev.: %{customdata[2]:.2f}"
#                         "<br>Position: %{customdata[3]}"
#                         "<br>CR: %{customdata[4]:.2f}"
#                         "%{customdata[5]}"
#         )
#         fig.update_layout(
#             autosize=False,
#             width=900,
#             height=700,
#             plot_bgcolor='white'
#         )
#         st.plotly_chart(fig)
#     else:
#         st.info("Not enough data to display PIR vs. Standard Deviation.")

# # -- Tab 2: PIR vs. CR --
# with tab2:
#     st.subheader("PIR vs. CR (Cost)")
#     last_games = last_x_games if last_x_games else df['GameCode'].nunique()
#     last_games_stats = calculate_pir_stats(filtered_df, last_games)
#     last_games_stats = add_injury_badge(last_games_stats)
#     if not last_games_stats.empty:
#         fig = px.scatter(
#             last_games_stats,
#             x='CR',
#             y='Average_PIR',
#             color='Average_PIR',
#             hover_data={
#                 'PlayerName': True,
#                 'Average_PIR': ':.2f',
#                 'CR': ':.2f',
#                 'position': True
#             },
#             custom_data=['PlayerName', 'Average_PIR', 'CR', 'position', 'InjuryBadge'],
#             title=f'Average PIR vs. CR (Last {last_games} Games)',
#             labels={'CR': 'Cost (CR)', 'Average_PIR': 'Average PIR'},
#             color_continuous_scale=px.colors.sequential.Viridis
#         )
#         fig.update_traces(
#             hovertemplate="<b>%{customdata[0]}</b><br>Avg PIR: %{customdata[1]:.2f}"
#                           "<br>CR: %{customdata[2]:.2f}<br>Position: %{customdata[3]}"
#                           "%{customdata[4]}"
#         )
#         fig.update_layout(
#             autosize=False,
#             width=900,
#             height=700,
#             plot_bgcolor='white'
#         )
#         st.plotly_chart(fig)
#     else:
#         st.info("Not enough data to display PIR vs. CR.")

# # -- Tab 3: PIR Averages DataFrame --
# with tab3:
#     st.subheader("Player Performance (Averages)")
#     last_games = last_x_games if last_x_games else df['GameCode'].nunique()
#     last_games_stats = calculate_pir_stats(filtered_df, last_games)
#     if not last_games_stats.empty:
#         # st.dataframe(last_games_stats)
#         SUMMARY_COLS = ["PlayerName", "Average_PIR", "StdDev_PIR", "CR", "position"]
#         view = select_cols(last_games_stats, SUMMARY_COLS)
#         st.dataframe(view, use_container_width=True, hide_index=True)
#     else:
#         st.info("No average PIR data available.")

# # -- Tab 4: Detailed Boxscores --
# with tab4:
#     st.subheader("Boxscores")
#     boxscore_game_options = ['All games'] + [f'Last {x} games' for x in range(1, 21)]
#     boxscore_selected_option = st.selectbox("Games to Display:", boxscore_game_options, key='boxscore_games')

#     if boxscore_selected_option == 'All games':
#         filtered_df_boxscore = filtered_df.copy()
#     else:
#         last_x_games_boxscore = int(boxscore_selected_option.split()[1])
#         latest_game_codes = sorted(df['GameCode'].unique(), reverse=True)[:last_x_games_boxscore]
#         filtered_df_boxscore = filtered_df[filtered_df['GameCode'].isin(latest_game_codes)]

#     st.markdown(f"**Boxscore Stats** ({boxscore_selected_option})")
#     # st.dataframe(filtered_df_boxscore)
#     BOX_COLS = [
#         "GameCode", "PlayerName", "position", "CR",
#         "PIR", "Points", "Rebounds", "Assists", "Steals", "Blocks", "Turnovers", "Minutes"
#     ]
#     box_view = select_cols(filtered_df_boxscore, BOX_COLS)
#     st.dataframe(box_view, use_container_width=True, hide_index=True)

# # -- Tab 5: Injuries --
# with tab5:
#     st.subheader("Injury Report")
#     inj_df = load_injuries_df()  # change key if you use a dated filename
#     if inj_df.empty:
#         st.info("No injury data available.")
#     else:
#         st.dataframe(inj_df, use_container_width=True, hide_index=True)


# # 5. Recommendations
# st.markdown("### Player Recommendations")
# if st.button("Get Top 10 Recommendations"):
#     # You can also call the old version:
#     # recommend_players(filtered_df, last_x_games)
#     recommendations_df = recommend_players_v2(filtered_df)
#         # Print top 10
#     st.subheader("Top 10 Recommended Players (Exponential-Weighted)")
#     st.write(recommendations_df.head(10))

# ##TEST2###
# if st.button("Advanced Recommendations"):
#     st.session_state.show_advanced = not st.session_state.show_advanced

# if st.session_state.show_advanced:
#     st.markdown("### Advanced Recommendation Settings")

#     # Put your sliders (and CR filter) inside a form
#     with st.form("advanced_recs_form"):
#         st.write("Customize your recommendation parameters below.")

#         # 1) Number of players to display
#         num_recommendations = st.slider(
#             "How many players to recommend?",
#             min_value=5,
#             max_value=30,
#             value=10
#         )
        
#         # 2) How many recent games to consider
#         last_x_games_param = st.slider(
#             "Number of recent games to consider",
#             min_value=1,
#             max_value=20,
#             value=5
#         )
        
#         # 3) Recency emphasis (alpha)
#         alpha_param = st.slider(
#             "Recency factor (alpha)",
#             min_value=0.5,
#             max_value=0.99,
#             value=0.85,
#             step=0.01,
#             help="Higher alpha means older games still matter; lower alpha emphasizes recent games more."
#         )
        
#         # 4) Weights
#         weight_eff = st.slider(
#             "Cost Efficiency Weight",
#             min_value=0.0,
#             max_value=5.0,
#             value=2.0,
#             step=0.1,
#             help="How strongly to reward players with high PIR/CR."
#         )
        
#         weight_mean = st.slider(
#             "Average PIR Weight",
#             min_value=0.0,
#             max_value=5.0,
#             value=1.0,
#             step=0.1,
#             help="How strongly to emphasize raw average PIR."
#         )
        
#         weight_cons = st.slider(
#             "Consistency Penalty Weight",
#             min_value=0.0,
#             max_value=5.0,
#             value=1.0,
#             step=0.1,
#             help="How heavily to penalize volatile players (high StdErr)."
#         )

#         # 5) CR Filter
#         # We'll do a range slider so user can set min/max CR for recommended players
#         min_cr_value = float(df['CR'].min()) if not df.empty else 0.0
#         max_cr_value = float(df['CR'].max()) if not df.empty else 35.0
#         cr_min, cr_max = st.slider(
#             "Filter by CR range:",
#             min_value=min_cr_value,
#             max_value=max_cr_value,
#             value=(min_cr_value, max_cr_value),
#             step=1.0
#         )

#         # Final "Generate" button for the form
#         generate_button = st.form_submit_button("Generate Recommendations")

#     # Only run the recommendation logic after form submission
#     if generate_button:
#         # 1) Filter the DataFrame by CR
#         advanced_filtered_df = df[
#             (df['CR'] >= cr_min) & (df['CR'] <= cr_max)
#         ].copy()
        
#         # 2) Call your recommendation function
#         recs_df = recommend_players_v2(
#             advanced_filtered_df,
#             last_x_games=last_x_games_param,
#             alpha=alpha_param,
#             weight_efficiency=weight_eff,
#             weight_mean_pir=weight_mean,
#             weight_consistency=weight_cons
#         )

#         if recs_df.empty:
#             st.warning("No recommendations found with the chosen parameters.")
#         else:
#             st.subheader(f"Top {num_recommendations} Recommendations")
#             st.dataframe(recs_df.head(num_recommendations))
# ##########

# # # 6. Data Download
# # if not df.empty:
# #     st.markdown("### Download Player Data")
# #     csv = df.to_csv(index=False)
# #     st.download_button(
# #         label="Download CSV",
# #         data=csv,
# #         file_name='player_stats.csv',
# #         mime='text/csv'
# #     )
