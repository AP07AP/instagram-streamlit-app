import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import re
from instagrapi import Client
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
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
st.markdown("### 👤 Enter Instagram Username")
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
# Function to Scrape Instagram Data
# ===============================
def scrape_instagram_data(target_user, start_date, end_date):
    cl = Client()
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

    user_id = cl.user_id_from_username(target_user)
    medias = cl.user_medias(user_id, 100)  # Adjust number of posts

    all_rows = []
    for media in medias:
        post_date = media.taken_at
        if start_date <= post_date.date() <= end_date:
            url = f"https://www.instagram.com/p/{media.code}/"
            likes = media.likes_count
            caption = media.caption_text or ""

            # Add caption row
            all_rows.append({
                "username": target_user,
                "commentor": target_user,
                "URL": url,
                "Date": post_date.date(),
                "Time": post_date.time(),
                "Likes": likes,
                "Captions": caption,
                "Comments": None
            })

            # Add comments
            comments = cl.media_comments(media.id)
            for c in comments:
                all_rows.append({
                    "username": target_user,
                    "commentor": c.user.username,
                    "URL": url,
                    "Date": c.created_at.date(),
                    "Time": c.created_at.time(),
                    "Likes": None,
                    "Captions": None,
                    "Comments": c.text
                })

    df = pd.DataFrame(all_rows)

    # --- Format captions and hashtags ---
    def extract_hashtags(caption):
        if pd.isna(caption):
            return None
        return " ".join(re.findall(r"#\w+", caption))

    def remove_hashtags(caption):
        if pd.isna(caption):
            return None
        return re.sub(r"#\w+", "", caption).strip()

    df["Caption_Text"] = df["Captions"].apply(remove_hashtags)
    df["Caption_Hashtags"] = df["Captions"].apply(extract_hashtags)

    return df

# ===============================
# Sentiment Analysis Setup
# ===============================
@st.cache_resource
def load_sentiment_model():
    model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_sentiment_model()
labels = ['negative', 'neutral', 'positive']

def preprocess(text):
    if pd.isna(text) or text.strip() == "":
        return ""
    return text

def predict_sentiment(text):
    text = preprocess(text)
    if text == "":
        return None, None
    encoded_input = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        output = model(**encoded_input)
    scores = torch.nn.functional.softmax(output.logits, dim=1)
    label_idx = torch.argmax(scores)
    label = labels[label_idx]
    score = scores[0, label_idx].item()
    return label, score

# ===============================
# Display Report
# ===============================
if st.session_state.show_report:
    with st.spinner("Fetching Instagram posts... ⏳"):
        try:
            df = scrape_instagram_data(selected_user, from_date, to_date)
        except Exception as e:
            st.error(f"Error fetching posts: {e}")
            st.stop()

    if df.empty:
        st.warning(f"No posts found for user {selected_user} in the selected date range.")
    else:
        # Apply sentiment analysis to Comments
        df[["Comment_Label", "Comment_Score"]] = df["Comments"].apply(lambda x: pd.Series(predict_sentiment(x)))

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
        total_likes = df["Likes"].sum(skipna=True)
        total_comments = df["Comments"].notna().sum()

        formatted_posts = format_indian_number(total_posts)
        formatted_likes = format_indian_number(total_likes)
        formatted_comments = format_indian_number(total_comments)

        # Sentiment overview
        all_comments = df[df["Comments"].notna()]
        sentiment_counts = (all_comments["Comment_Label"].value_counts(normalize=True) * 100)
        pos_pct = sentiment_counts.get("positive", 0.0)
        neg_pct = sentiment_counts.get("negative", 0.0)
        neu_pct = sentiment_counts.get("neutral", 0.0)

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
                f"🙂 Positive: {pos_pct:.1f}%  \n"
                f"😡 Negative: {neg_pct:.1f}%  \n"
                f"😐 Neutral: {neu_pct:.1f}%"
            )

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
                caption_row = post_group[post_group["Captions"].notna()]
                if not caption_row.empty:
                    row = caption_row.iloc[0]
                    st.markdown(
                        f"**Caption:** {row['Captions']}  \n"
                        f"📅 {row['Date']} 🕒 {row['Time']} ❤️ Likes: {format_indian_number(row['Likes'])}  \n"
                        f"🔗 [View Post]({url})"
                    )

                    # Optional button to show sentiment split for this post
                    show_sentiment = st.checkbox(f"Show Sentiment Split for this post?", key=f"sentiment_{url}")
                    if show_sentiment:
                        comments_only = post_group[post_group["Comments"].notna()].copy()
                        if not comments_only.empty:
                            st.dataframe(
                                comments_only[["Comments", "Comment_Label", "Comment_Score"]].reset_index(drop=True),
                                use_container_width=True
                            )

                            sentiment_counts_post = comments_only["Comment_Label"].value_counts(normalize=True) * 100
                            st.markdown(
                                f"**Sentiment Summary:**  \n"
                                f"🙂 Positive: {sentiment_counts_post.get('positive', 0):.1f}% | "
                                f"😡 Negative: {sentiment_counts_post.get('negative', 0):.1f}% | "
                                f"😐 Neutral: {sentiment_counts_post.get('neutral', 0):.1f}%"
                            )
                        else:
                            st.info("No comments available for this post.")
                st.markdown("---")
