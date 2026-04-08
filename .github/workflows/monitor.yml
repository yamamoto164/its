import os
import re
import smtplib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText

TARGET_URL = (
    "https://as.its-kenpo.or.jp/calendar_apply/calendar_select"
    "?s=PWtUTzRRak0zUXpOM0VUUHpWbWNwQkhlbDlWZW1sbWNsWm5KeDBEWnA5VmV5OTJabFJYWWo5VlpqbG1keVYyYw%3D%3D"
)
GMAIL_ADDRESS  = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
NOTIFY_TO      = os.environ["NOTIFY_TO"]


def fetch_calendar(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def find_available_saturdays(soup):
    available = []
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        for cell in cells:
            text = cell.get_text(strip=True)
            if not re.search(r"\d{1,2}", text):
                continue
            cell_class = " ".join(cell.get("class", []))
            is_saturday = "sat" in cell_class.lower()
            has_link = cell.find("a") is not None
            is_not_full = not any(
                kw in text for kw in ["満", "×", "締切", "受付終了"]
            )
            if is_saturday and has_link and is_not_full:
                href = cell.find("a").get("href", "")
                available.append({"date_text": text, "href": href})
    return available


def send_gmail(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = NOTIFY_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        smtp.send_message(msg)
    print("メール送信完了")


def main():
    print(f"[{datetime.now().isoformat()}] 監視開始")
    try:
        soup = fetch_calendar(TARGET_URL)
    except requests.RequestException as e:
        print(f"ページ取得失敗: {e}")
        return

    available = find_available_saturdays(soup)

    if available:
        lines = ["ITS健保施設 土曜日に空きが出ました!\n"]
        for item in available:
            href = item["href"]
            full_url = (
                f"https://as.its-kenpo.or.jp{href}"
                if href.startswith("/") else href
            )
            lines.append(f"{item['date_text']}\n{full_url}\n")
        lines.append("今すぐ予約を!")
        send_gmail(
            subject="【ITS健保】土曜日に空きが出ました！",
            body="\n".join(lines),
        )
    else:
        print("土曜日の空きなし。通知しません。")

    print("監視完了")


if __name__ == "__main__":
    main()
