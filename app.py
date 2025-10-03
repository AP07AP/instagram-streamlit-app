import streamlit as st
import pandas as pd
import os
from instagrapi import Client
from dotenv import load_dotenv
from datetime import datetime
from textblob import TextBlob
import re
import emoji

# ===============================
# Load environment variables
# ===============================
load_dotenv()

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
    st.warning("Please set your Instagram credentials in environment variables.")
    st.stop()

# ===============================
# Dashboard Title
# ===============================
st.title("📊 Instagram Posts Dashboard")

# ===============================
# Username Input
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
# Helper Functions
# ===============================
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

def extract_hashtags(caption):
    if pd.isna(caption):
        return None
    return " ".join(re.findall(r"#\w+", caption))

def remove_hashtags(caption):
    if pd.isna(caption):
        return None
    return re.sub(r"#\w+", "", caption).strip()

def predict_sentiment(text):
    if not text or text.strip() == "":
        return None, None
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "positive", polarity
    elif polarity < 0:
        return "negative", abs(polarity)
    else:
        return "neutral", 0

# ===============================
# Function to Fetch Instagram Posts
# ===============================
def fetch_instagram_data(username, password, target_user, start_date, end_date):
    cl = Client()
    cl.login(username, password)

    user_id = cl.user_id_from_username(target_user)
    medias = cl.user_medias(user_id, 100)  # up to 100 posts

    posts_data = []
    for media in medias:
        post_date = media.taken_at.date()
        if start_date <= post_date <= end_date:
            posts_data.append({
                "URL": f"https://www.instagram.com/p/{media.code}/",
                "Date": post_date,
                "Time": media.taken_at.time(),
                "Likes": media.like_count,
                "Captions": media.caption_text if media.caption_text else "",
                "Comments": media.comment_count,
                "username": target_user
            })
    df = pd.DataFrame(posts_data)
    if df.empty:
        return df

    # Hashtags & cleaned captions
    df["Caption_Text"] = df["Captions"].apply(remove_hashtags)
    df["Caption_Hashtags"] = df["Captions"].apply(extract_hashtags)

    # Sentiment analysis on captions
    df[["Caption_Sentiment_Label", "Caption_Sentiment_Score"]] = df["Caption_Text"].apply(
        lambda x: pd.Series(predict_sentiment(x))
    )

    return df

# ===============================
# Display Report
# ===============================
if st.session_state.show_report:
    with st.spinner("Fetching Instagram posts... ⏳"):
        try:
            df = fetch_instagram_data(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, selected_user, from_date, to_date)
        except Exception as e:
            st.error(f"Error fetching posts: {e}")
            st.stop()

    if df.empty:
        st.warning(f"No posts found for user {selected_user} in the selected date range.")
    else:
        # -------------------------------
        # User Overview
        # -------------------------------
        total_posts = df.shape[0]
        total_likes = df["Likes"].sum()
        total_comments = df["Comments"].sum()

        formatted_posts = format_indian_number(total_posts)
        formatted_likes = format_indian_number(total_likes)
        formatted_comments = format_indian_number(total_comments)

        st.markdown("## User Overview")
        col1, col2, col3, col4 = st.columns([2,1,1,1])
        with col1:
            st.markdown(f"**User:** {selected_user}")
        with col2:
            st.write(f"📄 **Total Posts:** {formatted_posts}")
        with col3:
            st.write(f"❤️ **Total Likes:** {formatted_likes}")
        with col4:
            st.write(f"💬 **Total Comments:** {formatted_comments}")

        st.markdown("---")

        # ===============================
        # Explore Posts
        # ===============================
        st.markdown("## 📌 Explore Posts")

        selected_post_urls = st.multiselect(
            "🔗 Select one or more Posts (URLs)",
            df["URL"].tolist()
        )

        if selected_post_urls:
            multi_posts = df[df["URL"].isin(selected_post_urls)]
            st.subheader("📝 Selected Posts Details")
            for url in selected_post_urls:
                row = multi_posts[multi_posts["URL"] == url].iloc[0]
                st.markdown(
                    f"**Caption:** {row['Captions']}  \n"
                    f"📅 {row['Date']} 🕒 {row['Time']} ❤️ Likes: {format_indian_number(row['Likes'])}  \n"
                    f"💬 Comments: {format_indian_number(row['Comments'])}  \n"
                    f"🔗 [View Post]({url})  \n"
                    f"🙂 Sentiment: {row['Caption_Sentiment_Label'].title()} ({row['Caption_Sentiment_Score']:.2f})"
                )
                st.markdown("---")
