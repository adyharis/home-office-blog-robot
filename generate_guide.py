#!/usr/bin/env python3
"""
Buyer's Guide Generator - NVIDIA Edition
Reads a topic from topics.txt, generates a 600-word buyer's guide via NVIDIA API,
inserts your Amazon affiliate tag, saves as markdown, and emails clean HTML to Blogger.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from pathlib import Path
import requests

NVIDIA_API_KEY     = os.environ.get("NVIDIA_API_KEY")
AMAZON_TAG         = os.environ.get("AMAZON_TAG", "defaulttag-20")
BLOGGER_EMAIL      = os.environ.get("BLOGGER_EMAIL")
GMAIL_USER         = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

TOPICS_FILE = Path("topics.txt")
OUTPUT_DIR  = Path("posts")

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def read_topic():
    if not TOPICS_FILE.exists():
        print(f"topics.txt not found")
        sys.exit(1)
    topics = [line.strip() for line in TOPICS_FILE.read_text().splitlines() if line.strip()]
    if not topics:
        print("topics.txt is empty.")
        sys.exit(1)
    return topics[0]


def generate_guide(topic):
    prompt = f"""Write a helpful, informative buyer's guide about the following topic.

Topic: {topic}

Requirements:
- Aim for approximately 600 words.
- Use a helpful, conversational tone.
- Include practical buying advice and key factors a shopper should consider.
- Naturally mention 3-5 specific products with Amazon links using this format: https://www.amazon.com/dp/PRODUCTID?tag={AMAZON_TAG}
- Use HTML formatting: h2 tags for section headings, p tags for paragraphs, ul/li for lists, strong for bold text.
- End the article with the exact line: "As an Amazon Associate I earn from qualifying purchases."
- Do NOT wrap the entire article in a code block. Output raw HTML ready to paste.
- No meta-commentary. Output ONLY the article HTML."""

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    response = requests.post(NVIDIA_URL, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"NVIDIA API error: {response.status_code}")
        print(response.text)
        sys.exit(1)

    article = response.json()["choices"][0]["message"]["content"].strip()

    disclaimer = '<p><em>As an Amazon Associate I earn from qualifying purchases.</em></p>'
    if "As an Amazon Associate" not in article:
        article += f"\n{disclaimer}"

    return article


def save_article(article):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filepath = OUTPUT_DIR / f"buyers-guide-{today}.md"
    filepath.write_text(article, encoding="utf-8")
    print(f"Saved article to {filepath}")
    return filepath


def email_article(article, topic):
    if not all([GMAIL_USER, GMAIL_APP_PASSWORD, BLOGGER_EMAIL]):
        print("Missing email credentials - skipping email.")
        return

    today = date.today().strftime("%B %d, %Y")
    subject = f"{topic} ({today})"

    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_USER
    msg["To"] = BLOGGER_EMAIL
    msg["Subject"] = subject

    # Wrap in clean HTML
    full_html = f"""<html>
<head><meta charset="UTF-8"></head>
<body>
<h1>{topic}</h1>
{article}
</body>
</html>"""

    msg.attach(MIMEText(full_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"Emailed article to {BLOGGER_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)


def main():
    if not NVIDIA_API_KEY:
        print("NVIDIA_API_KEY not set.")
        sys.exit(1)

    topic = read_topic()
    print(f"Generating buyer's guide for: {topic}")

    article = generate_guide(topic)
    print(f"Word count: {len(article.split())}")

    filepath = save_article(article)
    email_article(article, topic)

    print(f"Done! Article saved to {filepath}")


if __name__ == "__main__":
    main()
