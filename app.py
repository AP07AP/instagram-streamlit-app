import streamlit as st
import pandas as pd

# ===============================
# Load dataset
# ===============================
try:
    df = pd.read_csv("data/sentiment_final.csv")
except FileNotFoundError:
    st.error("CSV file not found! Make sure 'sentiment_1.csv' exists.")
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
# Username Input
# ===============================
st.markdown("### 👤 Enter Username")
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
# Display Report
# ===============================
if st.session_state.show_report:
    # Filter user data
    user_data = df[df["username"] == selected_user].copy()
    if user_data.empty:
        st.warning(f"No data found for user: {selected_user}")
    else:
        profile_url = ""
        first_post_url = user_data["URL"].iloc[0] if not user_data.empty else ""
        profile_url = first_post_url.split("/p/")[0] + "/" if first_post_url else ""

        # Apply date & time filters
        filtered = user_data[
            (user_data["Date"] >= pd.to_datetime(from_date)) &
            (user_data["Date"] <= pd.to_datetime(to_date))
        ]

        min_time, max_time = filtered["Time"].min(), filtered["Time"].max()
        time_range = st.slider(
            "Select Time Range",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time)
        )

        filtered = filtered[
            (filtered["Time"] >= time_range[0]) &
            (filtered["Time"] <= time_range[1])
        ]

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
        # Drill-down Explorer (Multiple URLs + Sentiment Filter)
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

                                # Keep sentiment summary **static** for all selected options
                                sentiment_counts_post_all = post_group[post_group["Comments"].notna()]["Sentiment_Label"].astype(str).str.strip().str.title().value_counts(normalize=True) * 100
                                st.markdown(
                                    f"**Sentiment Summary:**  \n"
                                    f"🙂 Positive: {sentiment_counts_post_all.get('Positive', 0):.1f}% | "
                                    f"😡 Negative: {sentiment_counts_post_all.get('Negative', 0):.1f}% | "
                                    f"😐 Neutral: {sentiment_counts_post_all.get('Neutral', 0):.1f}%"
                                )
                            else:
                                st.info("No comments available for the selected filter.")

                        st.markdown("---")
