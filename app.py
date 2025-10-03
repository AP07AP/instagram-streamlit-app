import streamlit as st
import pandas as pd
import os
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
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
# Scraping Function
# ===============================
def scrape_instagram_user(username):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    profile_url = f"https://www.instagram.com/{username}/"
    post_data = []

    try:
        # Login
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(3, 5))
        username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        username_field.send_keys(INSTAGRAM_USERNAME)
        password_field.send_keys(INSTAGRAM_PASSWORD)
        login_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        login_button.click()
        time.sleep(random.uniform(5, 7))

        # Dismiss popups
        for _ in range(2):
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Not Now")]'))
                )
                not_now_button.click()
                time.sleep(random.uniform(2, 4))
            except TimeoutException:
                pass

        # Open profile
        driver.get(profile_url)
        time.sleep(random.uniform(4, 6))

        # Collect post URLs
        post_urls = set()
        prev_count = 0
        same_count_times = 0
        while True:
            anchors = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/p/"]')
            for a in anchors:
                href = a.get_attribute("href")
                if href and "/p/" in href:
                    post_urls.add(href)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            if len(post_urls) == prev_count:
                same_count_times += 1
            else:
                same_count_times = 0
            prev_count = len(post_urls)
            if same_count_times >= 5:
                break

        # Scrape post captions
        for post_url in post_urls:
            driver.get(post_url)
            time.sleep(random.uniform(5, 7))
            try:
                caption_elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.C4VMK > span"))
                )
                caption_text = caption_elem.text.strip()
            except TimeoutException:
                caption_text = ""
            post_data.append({
                "Post_URL": post_url,
                "Username": "Caption",
                "Comment": caption_text,
                "Timestamp": pd.Timestamp.now(),
                "Likes": None
            })

    except Exception as e:
        st.error(f"Scraping error: {e}")
    finally:
        driver.quit()

    # Convert to DataFrame
    df = pd.DataFrame(post_data)

    # ===============================
    # Data Cleaning
    # ===============================
    # Extract main username from URL
    df["username"] = username

    # Split Timestamp into Date & Time
    df["Date"] = pd.to_datetime(df["Timestamp"]).dt.date
    df["Time"] = pd.to_datetime(df["Timestamp"]).dt.time

    # Identify caption rows
    df["is_caption"] = df["Username"] == "Caption"

    # Captions column: only for caption row
    df["Captions"] = df.apply(lambda row: row["Comment"] if row["is_caption"] else None, axis=1)

    # Comments column
    df["Comments"] = df.apply(lambda row: None if row["is_caption"] else row["Comment"], axis=1)

    # Rename final columns
    df = df.rename(columns={"Post_URL": "URL"})[["username", "URL", "Date", "Time", "Captions", "Comments"]]
    return df

# ===============================
# Load Sentiment Model
# ===============================
@st.cache_resource
def load_sentiment_model():
    model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_sentiment_model()
labels = ['negative', 'neutral', 'positive']

def predict_sentiment(text):
    if pd.isna(text) or text.strip() == "":
        return None, None
    encoded_input = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        output = model(**encoded_input)
    scores = torch.nn.functional.softmax(output.logits, dim=1)
    label_idx = torch.argmax(scores)
    return labels[label_idx], scores[0, label_idx].item()

# ===============================
# Streamlit Dashboard
# ===============================
st.title("📊 Instagram Posts Dashboard")
selected_user = st.text_input("Enter Instagram Username").strip()
from_date = st.date_input("From", value=None)
to_date = st.date_input("To", value=None)

if st.button("📑 Get Report"):
    if not selected_user or not from_date or not to_date:
        st.warning("Please enter username and select date range.")
    else:
        with st.spinner("Scraping Instagram data... ⏳"):
            df_scraped = scrape_instagram_user(selected_user)

            # Filter by date
            df_filtered = df_scraped[
                (df_scraped["Date"] >= from_date) & (df_scraped["Date"] <= to_date)
            ].copy()

            # Sentiment analysis on comments
            df_filtered["Sentiment_Label"], df_filtered["Sentiment_Score"] = zip(
                *df_filtered["Comments"].apply(predict_sentiment)
            )

            st.success(f"✅ Scraped {len(df_filtered)} posts for {selected_user}")
            st.dataframe(df_filtered)
