import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
import random
from datetime import datetime
from dotenv import load_dotenv
import os

# ===============================
# Dashboard Title
# ===============================
st.title("📊 Instagram Posts Dashboard")

# ===============================
# Username Input
# ===============================
st.markdown("### 👤 Enter Username")
selected_user = st.text_input("Enter Instagram Username").strip()

# ===============================
# Date Selection
# ===============================
from_date = st.date_input("From", value=None)
to_date = st.date_input("To", value=None)

# ===============================
# Initialize session state for "Get Report"
# ===============================
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# ===============================
# Instagram Scraping Function
# ===============================
load_dotenv()
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME") or "adiadiadi1044"
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD") or "Heybro@"

def scrape_instagram(username, from_date, to_date):
    """
    Scrape Instagram posts, captions, likes, and comments for a given username within date range.
    Returns a DataFrame.
    """
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
    all_data = []

    try:
        # --- LOGIN ---
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(3, 5))
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        username_field.send_keys(INSTAGRAM_USERNAME)
        password_field.send_keys(INSTAGRAM_PASSWORD)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        login_button.click()
        time.sleep(random.uniform(5, 7))

        # Dismiss popups
        for _ in range(2):
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Not Now")]'))
                )
                not_now_button.click()
                time.sleep(random.uniform(2, 3))
            except TimeoutException:
                pass

        # --- GO TO PROFILE ---
        driver.get(profile_url)
        time.sleep(random.uniform(4, 6))

        # --- COLLECT POST URLS ---
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

        # --- SCRAPE POSTS ---
        for post_url in post_urls:
            driver.get(post_url)
            time.sleep(random.uniform(4, 6))

            # --- Get post date ---
            try:
                time_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "time"))
                )
                post_datetime_str = time_elem.get_attribute("datetime")  # e.g., "2025-10-03T08:15:00.000Z"
                post_datetime = datetime.fromisoformat(post_datetime_str.replace("Z", "+00:00"))
            except Exception:
                post_datetime = None

            # Skip posts outside the selected range
            if post_datetime:
                post_date = post_datetime.date()
                if post_date < from_date or post_date > to_date:
                    continue

            # --- Get caption ---
            try:
                caption_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.C4VMK > span"))
                )
                caption_text = caption_elem.text.strip()
            except TimeoutException:
                caption_text = ""

            # --- Get likes ---
            try:
                likes_elem = driver.find_element(By.CSS_SELECTOR, "section.EDfFK span")
                likes_text = likes_elem.text.strip().replace(",", "")
            except Exception:
                likes_text = "0"

            # --- Get comments ---
            comments_list = []
            try:
                comment_elems = driver.find_elements(By.CSS_SELECTOR, "ul.XQXOT li")
                for c in comment_elems:
                    try:
                        username_c = c.find_element(By.CSS_SELECTOR, "h3._a0ze._a0zf").text
                        comment_text_c = c.find_element(By.CSS_SELECTOR, "span").text
                        comments_list.append({"Username": username_c, "Comment": comment_text_c})
                    except Exception:
                        continue
            except Exception:
                comments_list = []

            all_data.append({
                "username": username,
                "URL": post_url,
                "Captions": caption_text,
                "Likes": likes_text,
                "Comments": comments_list,
                "Date": post_datetime.date() if post_datetime else None,
                "Time": post_datetime.time() if post_datetime else None
            })

    except Exception as e:
        st.error(f"Error scraping Instagram: {e}")

    finally:
        driver.quit()

    df = pd.DataFrame(all_data)
    return df

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
    if selected_user:
        with st.spinner(f"Scraping Instagram data for {selected_user}... This may take a few minutes."):
            df = scrape_instagram(selected_user, from_date, to_date)

    if df.empty:
        st.warning(f"No data found for user: {selected_user}")
    else:
        # ---- Continue your existing dashboard logic exactly as-is ----
        # Use `df` from scraped data
        # Everything below your existing "Display Report" section remains unchanged
        st.write("Data successfully scraped! You can now view your report below.")
        st.dataframe(df)
