import os
import re
import smtplib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.text import MIMEText

# ── 監視するURLをここに追加していく ──────────────────
TARGET_URLS = [
    "https://as.its-kenpo.or.jp/calendar_apply/calendar_select?s=PWtUTzRRak0zUXpOM0VUUHpWbWNwQkhlbDlWZW1sbWNsWm5KeDBEWnA5VmV5OTJabFJYWWo5VlpqbG1keVYyYw%3D%3D",
    "https://as.its-kenpo.or.jp/calendar_apply/calendar_select?s=PUVETXlNek0zUXpOM0VUUHpWbWNwQkhlbDlWZW1sbWNsWm5KeDBEWnA5VmV5OTJabFJYWWo5VlpqbG1keVYyYw%3D%3D",
    # 7月分のURLをここに追加
]
# ─────────────────────────────────────────────────────

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


def check_monthly_reminder():
    now = datetime.now()
    if now.day == 1 and now.hour == 0:
        month = now.month
        year = now.year
        send_gmail(
            subject=f"【ITS健保監視】{year}年{month}月分のURL追加をお忘れなく",
            body=(
                f"{year}年{month}月になりました。\n\n"
                "ITS健保の予約サイトで新しい月のカレンダーURLが追加されている可能性があります。\n\n"
                "以下の手順でURLを追加してください。\n"
                "1. https://as.its-kenpo.or.jp/calendar_apply?s=PUVUUGtsMlg1SjNiblZHZGhOMlhsTldhMkpYWnpaU1oxSkhkOWtIZHcxV1o%3D を開く\n"
                "2. 新しい月のカレンダーページを開いてURLをコピー\n"
                "3. GitHubのmonitor.pyのTARGET_URLSリストに追加する\n"
            )
        )
        print("月次リマインドメール送信完了")


def main():
    print(f"[{datetime.now().isoformat()}] 監視開始")

    check_monthly_reminder()

    all_available = []
    for url in TARGET_URLS:
        try:
            soup = fetch_calendar(url)
            available = find_available_saturdays(soup)
            all_available.extend(available)
        except requests.RequestException as e:
            print(f"ページ取得失敗: {url}\n{e}")

    if all_available:
        lines = ["ITS健保施設 土曜日に空きが出ました!\n"]
        for item in all_available:
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
