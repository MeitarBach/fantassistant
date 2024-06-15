import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Dynamic Plot with Streamlit")

# Sample data
df = pd.DataFrame({
    "x": [1, 2, 3, 4],
    "y": [10, 20, 25, 30]
})

# # Create a plot
fig = px.line(df, x='x', y='y', title='Sample Plot')

# # Display the plot
st.plotly_chart(fig)
st.plotly_chart(fig)
