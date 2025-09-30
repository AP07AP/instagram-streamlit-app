import streamlit as st
import pandas as pd

# Load Data
df = pd.read_csv("data/sentiments.csv")

# Ensure necessary columns exist
required_cols = ["Captions", "URL", "Likes", "Comments", "Sentiment_Label", "Sentiment_Score"]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"Missing columns in CSV: {missing_cols}")
    st.stop()

# --- USER OVERVIEW ---
total_posts = len(df)
total_likes = df["Likes"].sum()
total_comments = df["Comments"].sum()

# Sentiment Distribution
sentiment_counts = df["Sentiment_Label"].value_counts(normalize=True) * 100
positive_pct = sentiment_counts.get("Positive", 0)
negative_pct = sentiment_counts.get("Negative", 0)
neutral_pct = sentiment_counts.get("Neutral", 0)

st.subheader("User Overview")
st.write(
    f"**Total Posts:** {total_posts} | "
    f"**Total Likes:** {total_likes:,} | "
    f"**Total Comments:** {total_comments:,} | "
    f"**Sentiment:** {positive_pct:.1f}% Positive, {negative_pct:.1f}% Negative, {neutral_pct:.1f}% Neutral"
)

# --- TABLE OF POSTS ---
st.subheader("Posts Overview")

# Sort posts by Likes (highest first)
df_sorted = df.sort_values(by="Likes", ascending=False).copy()

# Make URL clickable with display text "See Post"
df_sorted["Post Link"] = df_sorted["URL"].apply(lambda x: f"[See Post]({x})")

# Select only required columns for display
table_df = df_sorted[["Caption", "Post Link", "Likes", "Comments", "Sentiment_Label", "Sentiment_Score"]]

st.write(table_df.to_markdown(index=False))
