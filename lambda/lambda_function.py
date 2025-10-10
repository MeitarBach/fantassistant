from utils.data_fetchers import fetch_and_save_cr_data, fetch_and_update_player_stats, fetch_and_save_injury_report
print('Running data fetchers lambda')
fetch_and_save_cr_data()
fetch_and_update_player_stats("player_stats_2025.csv", "E2025")
fetch_and_save_injury_report()