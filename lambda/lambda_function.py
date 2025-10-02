from utils.data_fetchers import fetch_and_save_cr_data, fetch_and_update_player_stats
print('Running data fetchers lambda')
fetch_and_save_cr_data()
fetch_and_update_player_stats("player_stats_2025.csv", "E2025")