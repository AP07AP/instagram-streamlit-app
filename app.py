import streamlit as st
import pandas as pd

# --- Load dataset ---
try:
    df = pd.read_csv("data/sentiment_1.csv", parse_dates=["Date"])
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
st.title("📊 Instagram Posts Dashboard")

# --- Username filter ---
st.markdown("### 👤 Username")
usernames = df["username"].unique()
selected_user = st.selectbox("Select Username", usernames)
user_data = df[df["username"] == selected_user]

# --- Extract profile URL from first post URL ---
first_post_url = user_data["URL"].iloc[0] if not user_data.empty else ""
profile_url = first_post_url.split("/p/")[0] + "/" if first_post_url else ""

# --- Date filter with From and To ---
st.markdown("### 📅 Date & Time")

# Ensure Date is in datetime format
user_data["Date"] = pd.to_datetime(user_data["Date"], format="%d-%m-%Y", errors="coerce")

min_date, max_date = user_data["Date"].min().date(), user_data["Date"].max().date()

col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with col2:
    to_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

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
    (user_data["Date"] >= pd.to_datetime(from_date)) &
    (user_data["Date"] <= pd.to_datetime(to_date)) &
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

# --- Beautiful User Overview ---
total_posts = filtered["URL"].nunique()
total_likes = filtered["Likes"].sum()
total_comments = filtered["Comments"].notna().sum()

formatted_posts = format_indian_number(total_posts)
formatted_likes = format_indian_number(total_likes)
formatted_comments = format_indian_number(total_comments)

# Overall sentiment for all comments
all_comments = filtered[filtered["Comments"].notna()]
sentiment_counts = all_comments["Sentiment_Label"].astype(str).str.strip().str.title().value_counts(normalize=True) * 100
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

# --- Post filter dropdown with checkboxes (multiselect) ---
st.markdown("### 📝 Select Posts")
# "Select All" checkbox
select_all = st.checkbox("Select All Posts")

post_options = filtered["URL"].unique().tolist()
selected_posts = st.multiselect(
    "Select Posts",
    options=post_options,
    default=post_options if select_all else []
)


if selected_posts:
    for post_url in selected_posts:
        post_group = filtered[filtered["URL"] == post_url]

        # Get caption row (first row with a caption)
        caption_row = post_group[post_group["Captions"].notna()]
        if not caption_row.empty:
            caption_row = caption_row.iloc[0]
            caption_text = caption_row["Captions"]
            post_date = caption_row["Date"].date()
            post_time = caption_row["Time"]
            likes = format_indian_number(caption_row.get("Likes", 0))
        else:
            caption_text = ""
            post_date = ""
            post_time = ""
            likes = 0

        # --- Display Post Header ---
        st.markdown(f"📌 [View Post]({post_url})")
        st.write("**Caption:**")
        st.write(caption_text)
        st.write(f"📅 {post_date} 🕒 {post_time} ❤️ Likes: {likes}")

        # --- Display comments table ---
        post_comments = post_group[post_group["Comments"].notna()][["Comments", "Sentiment_Label", "Sentiment_Score"]]
        if not post_comments.empty:
            st.dataframe(post_comments.reset_index(drop=True))
        else:
            st.write("No comments available for this post.")

        st.markdown("---")  # separator between posts
else:
    st.write("Select one or more posts from the dropdown to see comments.")

 # below
import io

# --- Prepare wide-format Excel file for download ---
if selected_posts:
    excel_rows = []
    for post_url in selected_posts:
        post_group = filtered[filtered["URL"] == post_url]

        # Get caption row
        caption_row = post_group[post_group["Captions"].notna()]
        if not caption_row.empty:
            caption_text = caption_row.iloc[0]["Captions"]
            post_date = caption_row.iloc[0]["Date"].date()
            post_time = caption_row.iloc[0]["Time"]
            likes = caption_row.iloc[0]["Likes"]
        else:
            caption_text = ""
            post_date = ""
            post_time = ""
            likes = 0

        # Prepare post dictionary
        post_dict = {
            "URL": post_url,
            "Date": post_date,
            "Time": post_time,
            "Likes": likes,
            "Caption": caption_text
        }

        # Add comments dynamically
        comments_only = post_group[post_group["Comments"].notna()]
        for i, (_, row) in enumerate(comments_only.iterrows(), start=1):
            post_dict[f"Comment_{i}"] = row["Comments"]
            post_dict[f"Sentiment_Comment_{i}"] = row.get("Sentiment_Label", "")

        excel_rows.append(post_dict)

    # Convert to DataFrame
    excel_df = pd.DataFrame(excel_rows)

    # Convert to Excel in-memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        excel_df.to_excel(writer, index=False, sheet_name='Instagram_Posts')
    output.seek(0)

# Download button with username as file name
st.download_button(
    label="📥 Download Selected Posts Data as Excel",
    data=output,
    file_name=f"{selected_user}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
