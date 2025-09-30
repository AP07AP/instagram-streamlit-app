import streamlit as st
import pandas as pd

# --- Load dataset ---
df = pd.read_csv("data/insta_posts.csv", parse_dates=["Date"])

# --- Clean Likes column ---
df["Likes"] = df["Likes"].astype(str).str.replace(",", "").str.strip()
df["Likes"] = pd.to_numeric(df["Likes"], errors="coerce").fillna(0)

# --- Streamlit title ---
st.title("Instagram Posts Dashboard")

# --- Username filter ---
usernames = df["username"].unique()
selected_user = st.selectbox("Select Username", usernames)
user_data = df[df["username"] == selected_user]

# --- Date filter ---
min_date, max_date = user_data["Date"].min(), user_data["Date"].max()
date_range = st.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# --- Time filter ---
user_data["Time"] = pd.to_datetime(user_data["Time"], format='%H:%M:%S').dt.time
min_time, max_time = user_data["Time"].min(), user_data["Time"].max()
time_range = st.slider(
    "Select Time Range",
    min_value=min_time,
    max_value=max_time,
    value=(min_time, max_time)
)

# --- Apply filters ---
filtered = user_data[
    (user_data["Date"] >= pd.to_datetime(date_range[0])) &
    (user_data["Date"] <= pd.to_datetime(date_range[1])) &
    (user_data["Time"] >= time_range[0]) &
    (user_data["Time"] <= time_range[1])
]

# --- User overview ---
total_posts = filtered["URL"].nunique()
total_likes = filtered[filtered["Captions"].notna()]["Likes"].sum()
total_comments = filtered["Comments"].notna().sum()

st.markdown("## User Overview")
st.write(f"**Name:** {selected_user}")
st.write(f"**Total Posts:** {total_posts}  |  **Total Likes:** {total_likes}  |  **Total Comments:** {total_comments}")
st.markdown("---")

# --- Display posts section-wise by URL ---
for url, post_group in filtered.groupby("URL"):
    st.markdown(f"### 📌 [View Post]({url})")
    
    # Display caption (first row where Captions is not empty)
    caption_row = post_group[post_group["Captions"].notna()]
    if not caption_row.empty:
        caption_row = caption_row.iloc[0]
        st.subheader("Caption")
        st.write(caption_row["Captions"])
        st.write(f"📅 {caption_row['Date'].date()} 🕒 {caption_row['Time']} ❤️ Likes: {caption_row.get('Likes', '')}")

    # Display comments (rows where Comments is not empty)
    comments = post_group[post_group["Comments"].notna()]["Comments"].tolist()
    if comments:
        st.subheader("Comments")
        for c in comments:
            st.write(f"- 💬 {c}")

    st.markdown("---")
