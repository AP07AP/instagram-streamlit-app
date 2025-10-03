import streamlit as st
import pandas as pd
from datetime import datetime
import os
from instagrapi import Client

# ===============================
# Dashboard Title
# ===============================
st.title("📊 Instagram Posts Dashboard")

# ===============================
# Instagram Login (Environment Variables Recommended)
# ===============================
INSTAGRAM_USERNAME = os.getenv("adiadiadi1044")
INSTAGRAM_PASSWORD = os.getenv("Heybro@")

if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
    st.warning("Please set your Instagram credentials in environment variables.")
    st.stop()

# ===============================
# Username Input (Target User)
# ===============================
st.markdown("### 👤 Enter Target Instagram Username")
selected_user = st.text_input("Enter Instagram Username").strip()

# Initialize session state for "Get Report"
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# ===============================
# Date Selection
# ===============================
from_date = st.date_input("From", value=None)
to_date = st.date_input("To", value=None)

# ===============================
# Get Report Button
# ===============================
if st.button("📑 Get Report"):
    if not selected_user:
        st.warning("Please enter a username.")
    elif not from_date or not to_date:
        st.warning("Please select both start and end dates.")
    else:
        st.session_state.show_report = True

# ===============================
# Function to Fetch Instagram Posts
# ===============================
def fetch_posts(username, password, target_user, start_date, end_date):
    cl = Client()
    cl.login(username, password)

    user_id = cl.user_id_from_username(target_user)
    medias = cl.user_medias(user_id, 100)  # Fetch up to 100 posts

    posts = []
    for media in medias:
        post_date = media.taken_at
        if start_date <= post_date.date() <= end_date:
            posts.append({
                "URL": f"https://www.instagram.com/p/{media.code}/",
                "Date": post_date.date(),
                "Time": post_date.time(),
                "Likes": media.likes_count,
                "Comments": media.comments_count,
                "Captions": media.caption_text if media.caption_text else ""
            })

    return pd.DataFrame(posts)

# ===============================
# Display Report
# ===============================
if st.session_state.show_report:
    with st.spinner("Fetching Instagram posts... ⏳"):
        try:
            df = fetch_posts(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, selected_user, from_date, to_date)
        except Exception as e:
            st.error(f"Error fetching posts: {e}")
            st.stop()

    if df.empty:
        st.warning(f"No posts found for user {selected_user} in the selected date range.")
    else:
        # -------------------------------
        # Number Formatting (Indian style)
        # -------------------------------
        def format_indian_number(number):
            try:
                s = str(int(number))
            except:
                return "0"
            if len(s) <= 3:
                return s
            else:
                last3 = s[-3:]
                remaining = s[:-3]
                parts = []
                while len(remaining) > 2:
                    parts.append(remaining[-2:])
                    remaining = remaining[:-2]
                if remaining:
                    parts.append(remaining)
                return ','.join(reversed(parts)) + ',' + last3

        # -------------------------------
        # User Overview
        # -------------------------------
        total_posts = df["URL"].nunique()
        total_likes = df["Likes"].sum()
        total_comments = df["Comments"].sum()

        formatted_posts = format_indian_number(total_posts)
        formatted_likes = format_indian_number(total_likes)
        formatted_comments = format_indian_number(total_comments)

        st.markdown("## User Overview")
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col1:
            img_path = f"{selected_user}.jpg"
            try:
                st.image(img_path, width=180, caption=selected_user)
            except Exception:
                st.markdown(f"**Name:** {selected_user}")

        with col2:
            st.write(f"📄 **Total Posts:** {formatted_posts}")
        with col3:
            st.write(f"❤️ **Total Likes:** {formatted_likes}")
        with col4:
            st.write(f"💬 **Total Comments:** {formatted_comments}")

        st.markdown("---")

        # ===============================
        # Drill-down Explorer
        # ===============================
        st.markdown("## 📌 Explore Posts")

        selected_post_urls = st.multiselect(
            "🔗 Select one or more Posts (URLs)",
            df["URL"].unique().tolist()
        )

        if selected_post_urls:
            multi_posts = df[df["URL"].isin(selected_post_urls)]
            st.subheader("📝 Selected Posts Details")
            for url in selected_post_urls:
                post_group = multi_posts[multi_posts["URL"] == url]
                row = post_group.iloc[0]
                st.markdown(
                    f"**Caption:** {row['Captions']}  \n"
                    f"📅 {row['Date']} 🕒 {row['Time']} ❤️ Likes: {format_indian_number(row['Likes'])}  \n"
                    f"🔗 [View Post]({url})"
                )

