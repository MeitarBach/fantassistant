# utils/recommendations.py

import streamlit as st
import pandas as pd
import numpy as np

def recommend_players(df, last_x_games=10, lambda_decay=0.1, w1=1, w2=1, w3=1):
    """
    Recommend top 10 players using a scoring function that takes into account
    average PIR, CR, and standard error of PIR.
    """
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
        position = group['position'].iloc[0] if 'position' in group else "Unknown"
        
        # Normalize PIR and CR for scoring
        pir_norm = (pir_avg - df['PIR'].min()) / (df['PIR'].max() - df['PIR'].min())
        cr_norm = (df['CR'].max() - cr) / (df['CR'].max() - df['CR'].min()) if df['CR'].max() != df['CR'].min() else 0
        
        # Weighted formula: Score = w1*pir_norm + w2*cr_norm - w3*stderr
        score = (w1 * pir_norm) + (w2 * cr_norm) - (w3 * stderr) if cr > 0 else 0
        
        recommendations.append({
            'PlayerName': name,
            'PIR_Avg': pir_avg,
            'StdErr': stderr,
            'CR': cr,
            'position': position,
            'Score': score
        })
    
    recommendations_df = pd.DataFrame(recommendations).sort_values(by='Score', ascending=False)
    st.subheader("Top 10 Recommended Players Based on Weighted Formula")
    st.write(recommendations_df[['PlayerName', 'PIR_Avg', 'StdErr', 'CR', 'position', 'Score']].head(10))