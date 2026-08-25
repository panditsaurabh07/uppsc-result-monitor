import requests
from bs4 import BeautifulSoup
import json
import os

# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = "8857388515:AAGbQd7m7rk3AKYULqH6FhKTTMxlgwsixc8"
TELEGRAM_CHAT_ID = "PUT_YOUR_CHAT_ID_HERE"

# ============================================================
# UPPSC CONFIGURATION
# ============================================================

UPPSC_URL = "https://uppsc.up.nic.in/Home"
STATE_FILE = "974914763"


def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": False
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    response.raise_for_status()


def load_seen():

    if not os.path.exists(STATE_FILE):
        return set()

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))

    except Exception:
        return set()


def save_seen(seen):

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            sorted(seen),
            f,
            indent=2,
            ensure_ascii=False
        )


def get_results():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/150.0 Safari/537.36"
        )
    }

    response = requests.get(
        UPPSC_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []

    keywords = [
        "RESULT",
        "LIST OF CANDIDATES",
        "PROVISIONALLY QUALIFIED",
        "MARKSHEET",
        "CUT OFF"
    ]

    for link in soup.find_all("a"):

        text = link.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        text = " ".join(text.split())

        upper_text = text.upper()

        if any(
            keyword in upper_text
            for keyword in keywords
        ):

            href = link.get("href")

            if href:
                href = requests.compat.urljoin(
                    UPPSC_URL,
                    href
                )

            item_id = f"{text}|{href}"

            results.append({
                "id": item_id,
                "text": text,
                "url": href
            })

    return results


def main():

    print("Checking UPPSC...")

    current = get_results()

    print(
        f"Found {len(current)} "
        f"result-related entries."
    )

    seen = load_seen()

    # --------------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------------

    if not seen:

        print(
            "First run - creating baseline."
        )

        for item in current:
            seen.add(item["id"])

        save_seen(seen)

        print(
            "Baseline saved. "
            "No notification sent."
        )

        return

    # --------------------------------------------------------
    # FIND NEW RESULTS
    # --------------------------------------------------------

    new_results = []

    for item in current:

        if item["id"] not in seen:

            new_results.append(item)

            seen.add(item["id"])

    # --------------------------------------------------------
    # SEND TELEGRAM ALERT
    # --------------------------------------------------------

    if new_results:

        print(
            f"Found {len(new_results)} "
            f"new result(s)."
        )

        for item in new_results:

            message = (
                "🚨 UPPSC RESULT ALERT\n\n"
                f"{item['text']}\n\n"
                f"🔗 {item['url']}"
            )

            print(message)

            send_telegram(message)

    else:

        print(
            "No new result found."
        )

    save_seen(seen)


if __name__ == "__main__":
    main()
