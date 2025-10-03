from instagrapi import Client
import pandas as pd
import re
import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv

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
# Scrape posts function using instagrapi
# ===============================
def scrape_instagram_data(target_user, start_date, end_date):
    cl = Client()
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

    user_id = cl.user_id_from_username(target_user)
    medias = cl.user_medias(user_id, 100)  # Adjust number of posts as needed

    all_rows = []
    for media in medias:
        post_date = media.taken_at
        if start_date <= post_date.date() <= end_date:
            # Post info
            url = f"https://www.instagram.com/p/{media.code}/"
            likes = media.likes_count
            caption = media.caption_text or ""

            # Comments
            comments = cl.media_comments(media.id)
            if not comments:
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
            else:
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
    return df
