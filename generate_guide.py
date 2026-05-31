
 WRITE  [generate_guide.py]
 └  Created generate_guide.py (141 lines)

       1 │ #!/usr/bin/env python3
       2 │ """
       3 │ Buyer's Guide Generator
       4 │ Reads a topic from topics.txt, generates a 600-word buyer's guide via Google Gemini,
       5 │ inserts your Amazon affiliate tag, saves as markdown with today's date, and emails
       6 │ it to Blogger via Gmail SMTP.
       7 │ """
       8 │
       9 │ import os
      10 │ import sys

    … (131 more lines) [ctrl+o to expand]

✻ Thought for 1 second [ctrl+o to expand]

 WRITE  [.github\workflows\generate-guide.yml]
 └  Created .github\workflows\generate-guide.yml (44 lines)

      1 │ name: Generate Buyer's Guide
      2 │
      3 │ on:
      4 │   schedule:
      5 │     # Every 3 days at 08:00 UTC
      6 │     - cron: "0 8 */3 * *"
      7 │   workflow_dispatch:  # manual trigger
      8 │
      9 │ jobs:
     10 │   generate:

    … (34 more lines) [ctrl+o to expand]

✻ Thought for 1 second [ctrl+o to expand]

# Both files are ready.

  generate_guide.py — The script:

  - Reads the first non-empty line from topics.txt
  - Calls Gemini (gemini-2.0-flash) to write a ~600-word buyer's guide with your affiliate tag baked into
   the prompt
  - Ensures the Amazon disclaimer is always at the end
  - Saves to posts/buyers-guide-YYYY-MM-DD.md
  - Emails the article to your Blogger Mail-to-Blogger address via Gmail SMTP (plain + HTML parts)

  .github/workflows/generate-guide.yml — The workflow:

  - Runs every 3 days at 08:00 UTC (0 8 */3 * *) and supports manual dispatch
  - Installs google-genai (Google's new SDK) via pip
  - Passes all 5 secrets as env vars
  - Commits and pushes the generated posts/ folder back to the repo

  You need to set these GitHub Actions secrets:

  - GEMINI_API_KEY
  - AMAZON_TAG
  - BLOGGER_EMAIL
  - GMAIL_USER
  - GMAIL_APP_PASSWORD

  You also need a topics.txt in the repo root — one topic per line, the script uses the first non-empty
  line each run.

  Gmail SMTP note: Use an App Password (https://support.google.com/accounts/answer/185833) — normal
  passwords won't work with SMTP. And on Blogger, make sure Settings → Email → Mail-to-Blogger is
  configured and "Publish" is selected so emails auto-publish.

> command-code "show me the complete generate_guide.py file"

✻ Thought for 1 second [ctrl+o to expand]

 READ  [generate_guide.py] 141 lines

✻ Thought for 1 second [ctrl+o to expand]

# Here's the complete generate_guide.py:

    #!/usr/bin/env python3
    """
    Buyer's Guide Generator
    Reads a topic from topics.txt, generates a 600-word buyer's guide via Google Gemini,
    inserts your Amazon affiliate tag, saves as markdown with today's date, and emails
    it to Blogger via Gmail SMTP.
    """

    import os
    import sys
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import date
    from pathlib import Path

    from google import genai

    # ── Environment ────────────────────────────────────────────────────────────────
    GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY")
    AMAZON_TAG         = os.environ.get("AMAZON_TAG", "defaulttag-20")
    BLOGGER_EMAIL      = os.environ.get("BLOGGER_EMAIL")
    GMAIL_USER         = os.environ.get("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

    TOPICS_FILE = Path("topics.txt")
    OUTPUT_DIR  = Path("posts")


    # ── Helpers ───────────────────────────────────────────────────────────────────

    def read_topic() -> str:
        """Return the first non-empty line from topics.txt."""
        if not TOPICS_FILE.exists():
            print(f"topics.txt not found at {TOPICS_FILE.resolve()}")
            sys.exit(1)
        topics = [line.strip() for line in TOPICS_FILE.read_text().splitlines() if line.strip()]
        if not topics:
            print("topics.txt is empty.")
            sys.exit(1)
        return topics[0]


    def generate_guide(topic: str) -> str:
        """Ask Gemini to write a ~600‑word buyer's guide with affiliate links."""
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""Write a helpful, informative buyer's guide about the following topic. Follow every
  instruction precisely.

    Topic: {topic}

    Requirements:
    - Aim for approximately 600 words.
    - Use a helpful, conversational tone.
    - Include practical buying advice and key factors a shopper should consider.
    - Naturally mention specific products and link them with the Amazon affiliate tag "{AMAZON_TAG}"
  using the format `?tag={AMAZON_TAG}` in the URL.
    - End the article with the exact line: "As an Amazon Associate I earn from qualifying purchases."
    - Format in Markdown with a single H1 heading for the title and H2 subheadings for sections.
    - Do NOT include any meta‑commentary like "Here is your guide" or "I hope this helps". Output ONLY
  the article itself."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        article = response.text.strip()

        # Ensure the required disclaimer is always present.
        disclaimer = "As an Amazon Associate I earn from qualifying purchases."
        if disclaimer not in article:
            article += f"\n\n{disclaimer}"

        return article


    def save_article(article: str) -> Path:
        """Write the article to posts/buyers-guide-YYYY-MM-DD.md."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        today = date.today().isoformat()
        filepath = OUTPUT_DIR / f"buyers-guide-{today}.md"
        filepath.write_text(article)
        print(f"Saved article to {filepath}")
        return filepath


    def email_article(article: str, topic: str) -> None:
        """Send the article as an email to Blogger's Mail‑to‑Blogger address."""
        if not all([GMAIL_USER, GMAIL_APP_PASSWORD, BLOGGER_EMAIL]):
            print("GMAIL_USER, GMAIL_APP_PASSWORD, or BLOGGER_EMAIL not set — skipping email.")
            return

        today = date.today().strftime("%B %d, %Y")
        subject = f"Buyer's Guide: {topic} ({today})"

        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = BLOGGER_EMAIL
        msg["Subject"] = subject

        # Plain‑text fallback (strip Markdown syntax).
        plain = article.replace("**", "").replace("## ", "").replace("# ", "")
        msg.attach(MIMEText(plain, "plain"))

        # Simple HTML version — Blogger will render it.
        html_body = article.replace("\n", "<br>\n")
        html = f"<html><body>{html_body}</body></html>"
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.send_message(msg)
            print(f"Emailed article to {BLOGGER_EMAIL}")
        except Exception as e:
            print(f"Failed to send email: {e}")
            sys.exit(1)


    # ── Main ──────────────────────────────────────────────────────────────────────

    def main() -> None:
        if not GEMINI_API_KEY:
            print("GEMINI_API_KEY environment variable is not set.")
            sys.exit(1)

        topic = read_topic()
        print(f"Generating buyer's guide for: {topic}")

        article = generate_guide(topic)
        words = len(article.split())
        print(f"Word count: {words}")

        filepath = save_article(article)
        email_article(article, topic)

        print(f"Done! Article saved to {filepath}")


    if __name__ == "__main__":
        main()

  141 lines, no placeholders. Drop a topic into topics.txt, set your env vars, and it runs.
