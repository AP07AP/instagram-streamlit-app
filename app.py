import streamlit as st
import pandas as pd
import html  # for escaping captions

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
total_likes = filtered[filtered["Captions"].notna()]["Likes"].sum()
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

st.write(f"**Total Posts:** {formatted_posts}  |  **Total Likes:** {formatted_likes}  |  **Total Comments:** {formatted_comments}")
st.markdown("---")

# --- Posts Summary Table with clickable 'Click URL' ---
st.markdown("## Posts Summary")

table_html = """
<div style="overflow-x:auto;">
<table style="width:100%; border-collapse: collapse;">
<tr>
<th style="border: 1px solid black; padding: 8px; text-align:left;">Post</th>
<th style="border: 1px solid black; padding: 8px; text-align:left;">URL</th>
<th style="border: 1px solid black; padding: 8px; text-align:left;">Likes</th>
<th style="border: 1px solid black; padding: 8px; text-align:left;">Total Comments</th>
</tr>
"""

for url, post_group in filtered.groupby("URL"):
    caption_row = post_group[post_group["Captions"].notna()]
    if not caption_row.empty:
        caption_text = caption_row.iloc[0]["Captions"]
        # Escape HTML and replace newlines with <br>
        caption_text = html.escape(str(caption_text)).replace("\n", "<br>")
    else:
        caption_text = ""
    
    likes = caption_row.iloc[0]["Likes"] if not caption_row.empty else 0
    total_post_comments = post_group["Comments"].notna().sum()
    
    table_html += f"""
    <tr>
    <td style="border: 1px solid black; padding: 8px; word-wrap: break-word; max-width:400px;">{caption_text}</td>
    <td style="border: 1px solid black; padding: 8px;"><a href="{url}" target="_blank">Click URL</a></td>
    <td style="border: 1px solid black; padding: 8px;">{format_indian_number(likes)}</td>
    <td style="border: 1px solid black; padding: 8px;">{format_indian_number(total_post_comments)}</td>
    </tr>
    """

table_html += "</table></div>"

st.markdown(table_html, unsafe_allow_html=True)
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
        st.write(f"📅 {caption_row['Date'].date()} 🕒 {caption_row['Time']} ❤️ Likes: {format_indian_number(caption_row.get('Likes', 0))}")

    # Display comments (rows where Comments is not empty)
    comments = post_group[post_group["Comments"].notna()]["Comments"].tolist()
    if comments:
        st.subheader("Comments")
        for c in comments:
            st.write(f"- 💬 {c}")

    st.markdown("---")
