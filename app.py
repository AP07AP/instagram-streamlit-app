mport streamlit as st
import pandas as pd

# ===============================
# Load dataset
# ===============================
try:
    df = pd.read_csv("data/sentiment_1.csv")
except FileNotFoundError:
    st.error("CSV file not found! Make sure 'sentiments.csv' exists.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error("CSV file is empty! Please provide a valid CSV with data.")
    st.stop()

# --- Clean Likes column ---
df["Likes"] = df["Likes"].astype(str).str.replace(",", "").str.strip()
df["Likes"] = pd.to_numeric(df["Likes"], errors="coerce").fillna(0)

# --- Convert Date & Time ---
df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
df["Time"] = pd.to_datetime(df["Time"], format='%H:%M:%S', errors="coerce").dt.time

# ===============================
# Dashboard Title
# ===============================
st.title("📊 Instagram Posts Dashboard")

# ===============================
# Username Filter
# ===============================
st.markdown("### 👤 Username")
usernames = df["username"].dropna().unique()
selected_user = st.selectbox("Select Username", usernames)

user_data = df[df["username"] == selected_user].copy()

# Extract profile URL
first_post_url = user_data["URL"].iloc[0] if not user_data.empty else ""
profile_url = first_post_url.split("/p/")[0] + "/" if first_post_url else ""

# ===============================
# Date & Time Filter
# ===============================
st.markdown("### 📅 Date & Time")

if not user_data.empty:
    min_date, max_date = user_data["Date"].min().date(), user_data["Date"].max().date()
else:
    min_date, max_date = pd.to_datetime("today").date(), pd.to_datetime("today").date()

col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with col2:
    to_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

min_time, max_time = user_data["Time"].min(), user_data["Time"].max()
time_range = st.slider(
    "Select Time Range",
    min_value=min_time,
    max_value=max_time,
    value=(min_time, max_time)
)

# ===============================
# Apply Filters
# ===============================
filtered = user_data[
    (user_data["Date"] >= pd.to_datetime(from_date)) &
    (user_data["Date"] <= pd.to_datetime(to_date)) &
    (user_data["Time"] >= time_range[0]) &
    (user_data["Time"] <= time_range[1])
]

# ===============================
# Number Formatting (Indian style)
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

# ===============================
# User Overview
# ===============================
total_posts = filtered["URL"].nunique()
total_likes = filtered["Likes"].sum()
total_comments = filtered["Comments"].notna().sum()

formatted_posts = format_indian_number(total_posts)
formatted_likes = format_indian_number(total_likes)
formatted_comments = format_indian_number(total_comments)

# Sentiment overview
all_comments = filtered[filtered["Comments"].notna()]
sentiment_counts = (
    all_comments["Sentiment_Label"].astype(str).str.strip().str.title().value_counts(normalize=True) * 100
)
pos_pct = sentiment_counts.get("Positive", 0.0)
neg_pct = sentiment_counts.get("Negative", 0.0)
neu_pct = sentiment_counts.get("Neutral", 0.0)

st.markdown("## User Overview")
col1, col2, col3, col4, col5 = st.columns([2,1,1,1,2])
with col1:
    img_path = f"{selected_user}.jpg"
    try:
        st.image(img_path, width=180, caption=f"[{selected_user}]({profile_url})" if profile_url else selected_user)
    except Exception:
        if profile_url:
            st.markdown(f"**Name:** [{selected_user}]({profile_url})")
        else:
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
# Posts Summary Table
# ===============================
summary_list = []
for url, post_group in filtered.groupby("URL"):
    comments_only = post_group[post_group["Comments"].notna()]
    caption_row = post_group[post_group["Captions"].notna()]
    caption_text = caption_row.iloc[0]["Captions"] if not caption_row.empty else ""
    likes = caption_row.iloc[0]["Likes"] if not caption_row.empty else 0
    total_post_comments = comments_only.shape[0]

    # Sentiment per post
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
        "Overall Sentiment": overall_sentiment,
        "Positive (%)": f"{pos_pct_post:.1f}%",
        "Negative (%)": f"{neg_pct_post:.1f}%",
        "Neutral (%)": f"{neu_pct_post:.1f}%"
    })

summary_df = pd.DataFrame(summary_list)
if not summary_df.empty:
    summary_df = summary_df.sort_values(by="Likes", key=lambda x: x.str.replace(",", "").astype(int), ascending=False)

st.markdown("## Posts Summary")
st.dataframe(summary_df, use_container_width=True)
st.markdown("---")

# ===============================
# Drill-down Explorer
# ===============================
# ===============================
# Drill-down Explorer (Multiple URLs)
# ===============================
# ===============================
# Drill-down Explorer (Multiple URLs + Optional Sentiment Split)
# ===============================
st.markdown("## 📌 Explore Posts")

if not summary_df.empty:
    selected_post_urls = st.multiselect(
        "🔗 Select one or more Posts (URLs)",
        summary_df["URL"].tolist()
    )

    if selected_post_urls:
        multi_posts = filtered[filtered["URL"].isin(selected_post_urls)]

        # --- Show captions & meta info for each post ---
        st.subheader("📝 Selected Posts Details")
        for url in selected_post_urls:
            post_group = multi_posts[multi_posts["URL"] == url]
            caption_row = post_group[post_group["Captions"].notna()]
            if not caption_row.empty:
                row = caption_row.iloc[0]
                st.markdown(
                    f"**Caption:** {row['Captions']}  \n"
                    f"📅 {row['Date'].date()} 🕒 {row['Time']} ❤️ Likes: {format_indian_number(row['Likes'])}  \n"
                    f"🔗 [View Post]({url})"
                )

                # Optional button to show sentiment split for this post
                show_sentiment = st.checkbox(f"Show Sentiment Split for this post?", key=f"sentiment_{url}")
                if show_sentiment:
                    comments_only = post_group[post_group["Comments"].notna()].copy()
                    comments_only["Sentiment_Label"] = comments_only["Sentiment_Label"].astype(str).str.strip().str.title()

                    # Sentiment Filter Dropdown per post
                    sentiment_filter = st.selectbox(
                        "Filter comments by Sentiment", 
                        ["All", "Positive", "Negative", "Neutral"],
                        key=f"filter_{url}"
                    )
                    if sentiment_filter != "All":
                        comments_only = comments_only[comments_only["Sentiment_Label"] == sentiment_filter]

                    if not comments_only.empty:
                        st.dataframe(
                            comments_only[["Comments", "Sentiment_Label", "Sentiment_Score"]].reset_index(drop=True),
                            use_container_width=True
                        )

                        # Sentiment Summary
                        sentiment_counts_post = comments_only["Sentiment_Label"].value_counts(normalize=True) * 100
                        st.markdown(
                            f"**Sentiment Summary:**  \n"
                            f"🙂 Positive: {sentiment_counts_post.get('Positive', 0):.1f}% | "
                            f"😡 Negative: {sentiment_counts_post.get('Negative', 0):.1f}% | "
                            f"😐 Neutral: {sentiment_counts_post.get('Neutral', 0):.1f}%"
                        )
                    else:
                        st.info("No comments available for the selected filter.")

                st.markdown("---")
