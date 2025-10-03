import streamlit as st
import pandas as pd
from datetime import datetime
import instaloader

# ===============================
# Streamlit Dashboard Title
# ===============================
st.title("📊 Instagram Posts Dashboard (Live Scraping)")

# ===============================
# Username Input
# ===============================
st.markdown("### 👤 Enter Instagram Username")
selected_user = st.text_input("Enter Instagram Username").strip()

# Initialize session state for "Get Report"
if "show_report" not in st.session_state:
    st.session_state.show_report = False
if "user_data" not in st.session_state:
    st.session_state.user_data = pd.DataFrame()

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
        # Scrape Instagram using Instaloader
        # ===============================
        with st.spinner("Fetching posts... This may take a few minutes depending on the number of posts."):
            L = instaloader.Instaloader(download_comments=False, save_metadata=False, compress_json=False)
            try:
                profile = instaloader.Profile.from_username(L.context, selected_user)
            except Exception as e:
                st.error(f"Failed to fetch user: {e}")
                st.session_state.show_report = False
            else:
                posts_data = []
                for post in profile.get_posts():
                    post_date = post.date.date()
                    if from_date <= post_date <= to_date:
                        posts_data.append({
                            "URL": f"https://www.instagram.com/p/{post.shortcode}/",
                            "Date": post_date,
                            "Time": post.date.time(),
                            "Likes": post.likes,
                            "Captions": post.caption or "",
                            "Comments": None,  # Comments can be added later if needed
                            "Sentiment_Label": None,
                            "Sentiment_Score": None
                        })
                st.session_state.user_data = pd.DataFrame(posts_data)
                if st.session_state.user_data.empty:
                    st.warning("No posts found in the selected date range.")

# ===============================
# Display Report
# ===============================
if st.session_state.show_report and not st.session_state.user_data.empty:
    filtered = st.session_state.user_data.copy()

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
    total_posts = filtered["URL"].nunique()
    total_likes = filtered["Likes"].sum()
    total_comments = filtered["Comments"].notna().sum()

    formatted_posts = format_indian_number(total_posts)
    formatted_likes = format_indian_number(total_likes)
    formatted_comments = format_indian_number(total_comments)

    st.markdown("## User Overview")
    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,2])
    with col1:
        st.markdown(f"**Name:** {selected_user}")
    with col2:
        st.write(f"📄 **Total Posts:** {formatted_posts}")
    with col3:
        st.write(f"❤️ **Total Likes:** {formatted_likes}")
    with col4:
        st.write(f"💬 **Total Comments:** {formatted_comments}")
    with col5:
        st.markdown(
            f"**Overall Sentiment:**  \n"
            f"🙂 Positive: 0%  \n"
            f"😡 Negative: 0%  \n"
            f"😐 Neutral: 0%"
        )

    st.markdown("---")

    # ===============================
    # Drill-down Explorer (Posts)
    # ===============================
    st.markdown("## 📌 Explore Posts")

    if not filtered.empty:
        selected_post_urls = st.multiselect(
            "🔗 Select one or more Posts (URLs)",
            filtered["URL"].unique().tolist()
        )

        if selected_post_urls:
            multi_posts = filtered[filtered["URL"].isin(selected_post_urls)]
            st.subheader("📝 Selected Posts Details")
            for url in selected_post_urls:
                post_group = multi_posts[multi_posts["URL"] == url]
                row = post_group.iloc[0]
                st.markdown(
                    f"**Caption:** {row['Captions']}  \n"
                    f"📅 {row['Date']} 🕒 {row['Time']} ❤️ Likes: {format_indian_number(row['Likes'])}  \n"
                    f"🔗 [View Post]({url})"
                )
                st.markdown("---")
