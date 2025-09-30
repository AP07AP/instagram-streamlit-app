import streamlit as st
import pandas as pd

# --- Load dataset ---
try:
    df = pd.read_csv("data/sentiments.csv", parse_dates=["Date"])
except FileNotFoundError:
    st.error("CSV file not found! Make sure 'data/sentiments.csv' exists.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error("CSV file is empty! Please provide a valid CSV with data.")
    st.stop()

# --- Clean Likes column ---
df["Likes"] = df["Likes"].astype(str).str.replace(",", "").str.strip()
df["Likes"] = pd.to_numeric(df["Likes"], errors="coerce").fillna(0)

# --- Streamlit title ---
st.title("Instagram Posts Dashboard")

# --- Username filter ---
usernames = df["username"].unique()
selected_user = st.selectbox("Select Username", usernames)
user_data = df[df["username"] == selected_user]

# --- Extract profile URL from first post URL ---
first_post_url = user_data["URL"].iloc[0] if not user_data.empty else ""
profile_url = first_post_url.split("/p/")[0] + "/" if first_post_url else ""

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

# --- Function to format number in Indian style ---
def format_indian_number(number):
    s = str(int(number))
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

# --- User overview ---
total_posts = filtered["URL"].nunique()
total_likes = filtered["Likes"].sum()
total_comments = filtered["Comments"].notna().sum()

formatted_posts = format_indian_number(total_posts)
formatted_likes = format_indian_number(total_likes)
formatted_comments = format_indian_number(total_comments)

st.markdown("## User Overview")

# Name as clickable link
if profile_url:
    st.markdown(f"**Name:** [{selected_user}]({profile_url})")
else:
    st.write(f"**Name:** {selected_user}")

# --- Overall sentiment for all comments ---
all_comments = filtered[filtered["Comments"].notna()]
sentiment_counts = all_comments["Sentiment_Label"].astype(str).str.strip().str.title().value_counts(normalize=True) * 100
pos_pct = sentiment_counts.get("Positive", 0.0)
neg_pct = sentiment_counts.get("Negative", 0.0)
neu_pct = sentiment_counts.get("Neutral", 0.0)

st.write(
    f"**Total Posts:** {formatted_posts}  |  **Total Likes:** {formatted_likes}  |  "
    f"**Total Comments:** {formatted_comments}  |  "
    f"**Sentiment**: 🙂 Positive: {pos_pct:.1f}% | 😡 Negative: {neg_pct:.1f}% | 😐 Neutral: {neu_pct:.1f}%"
)
st.markdown("---")

# --- Prepare Posts Summary Table ---
summary_list = []
for url, post_group in filtered.groupby("URL"):
    # Only consider comment rows for sentiment
    comments_only = post_group[post_group["Comments"].notna()]
    # Caption row
    caption_row = post_group[post_group["Captions"].notna()]
    caption_text = caption_row.iloc[0]["Captions"] if not caption_row.empty else ""
    likes = caption_row.iloc[0]["Likes"] if not caption_row.empty else 0
    total_post_comments = comments_only.shape[0]

    # Sentiment per post (from comments only)
    sentiment_counts_post = comments_only["Sentiment_Label"].astype(str).str.strip().str.title().value_counts(normalize=True) * 100
    pos_pct_post = sentiment_counts_post.get("Positive", 0.0)
    neg_pct_post = sentiment_counts_post.get("Negative", 0.0)
    neu_pct_post = sentiment_counts_post.get("Neutral", 0.0)
    sentiment_dict = {"Positive": pos_pct_post, "Negative": neg_pct_post, "Neutral": neu_pct_post}
    max_label = max(sentiment_dict, key=sentiment_dict.get)
    max_pct = sentiment_dict[max_label]
    overall_sentiment = f"{max_label} ({max_pct:.1f}%)"

    summary_list.append({
        "Post": caption_text,
        "URL": url,
        "Likes": format_indian_number(likes),
        "Total Comments": format_indian_number(total_post_comments),
        "Overall Sentiment": overall_sentiment
    })

summary_df = pd.DataFrame(summary_list)
summary_df = summary_df.sort_values(by="Likes", key=lambda x: x.str.replace(",", "").astype(int), ascending=False)

st.markdown("## Posts Summary")
st.dataframe(summary_df, use_container_width=True)
st.markdown("---")

# --- Display posts section-wise by URL, sorted by Likes ---
urls_sorted = summary_df.sort_values(by="Likes", key=lambda x: x.str.replace(",", "").astype(int), ascending=False)["URL"]

for url in urls_sorted:
    post_group = filtered[filtered["URL"] == url]
    
    st.markdown(f"### 📌 [View Post]({url})")
    
    # Display caption
    caption_row = post_group[post_group["Captions"].notna()]
    if not caption_row.empty:
        caption_row = caption_row.iloc[0]
        st.subheader("Caption")
        st.write(caption_row["Captions"])
        st.write(f"📅 {caption_row['Date'].date()} 🕒 {caption_row['Time']} ❤️ Likes: {format_indian_number(caption_row.get('Likes', 0))}")

    # Display comments with sentiment
    comments_data = post_group[post_group["Comments"].notna()]
    if not comments_data.empty:
        st.subheader("Comments")
        for _, row in comments_data.iterrows():
            comment_text = row["Comments"]
            sentiment_label = row.get("Sentiment_Label", "")
            sentiment_score = row.get("Sentiment_Score", "")
            st.write(f"- 💬 {comment_text} ({sentiment_label}: {sentiment_score})")
    
    # --- Display overall sentiment for this post (from table) ---
    overall_sentiment = summary_df[summary_df["URL"] == url]["Overall Sentiment"].values[0]
    st.write(f"Overall Sentiment for this post: {overall_sentiment}")

    st.markdown("---")
