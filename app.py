import streamlit as st
import pandas as pd

# Load dataset
df = pd.read_csv("data/posts.csv", parse_dates=["date"])

st.title("Instagram Posts")

# Username dropdown
usernames = df["username"].unique()
selected_user = st.selectbox("Select Username", usernames)

# Timeline range
user_data = df[df["username"] == selected_user]
min_date, max_date = user_data["date"].min(), user_data["date"].max()

timeline = st.date_input(
    "Select Timeline Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filter
if isinstance(timeline, list) and len(timeline) == 2:
    start_date, end_date = timeline
    filtered_posts = user_data[
        (user_data["date"] >= pd.to_datetime(start_date)) &
        (user_data["date"] <= pd.to_datetime(end_date))
    ]
else:
    filtered_posts = user_data

# Show posts
st.subheader(f"Posts by {selected_user}")
for _, row in filtered_posts.iterrows():
    st.write(f"📅 {row['date'].date()} - {row['post']}")
    st.caption(row['caption'])
    st.markdown("---")
