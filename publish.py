"""Publish today's LouMath posts and reel on Instagram (@loumath2025).

Reads schedule.json (date in Morocco time -> list of items) and publishes each item
through the Instagram API with Instagram Login. An item whose caption already
appears on the account is skipped, so running the script twice never double-posts.

Environment: IG_TOKEN (long-lived Instagram token).
Usage: python publish.py [YYYY-MM-DD] [--dry-run]
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://graph.instagram.com/v21.0"
TOKEN = os.environ.get("IG_TOKEN", "").strip()


def call(method, path, **params):
    """Standard library only, so the cloud task needs nothing installed."""
    params["access_token"] = TOKEN
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method=method), timeout=120) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        data = json.load(e)
    if "error" in data:
        raise RuntimeError(f"{path}: {data['error'].get('message')}")
    return data


def wait_until_ready(container, kind):
    """Videos are processed by Instagram before they can be published."""
    for _ in range(60):
        status = call("GET", container, fields="status_code,status")["status_code"]
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"{kind} container {container}: {status}")
        time.sleep(10)
    raise RuntimeError(f"{kind} container {container}: still processing after 10 minutes")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    # Morocco is UTC+1 (outside Ramadan, when it moves to UTC+0; the 13:00 run is unaffected).
    today = args[0] if args else (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).date().isoformat()

    schedule = json.loads((Path(__file__).parent / "schedule.json").read_text(encoding="utf-8"))
    items = schedule.get(today)
    if not items:
        print(f"Nothing scheduled for {today}. Last scheduled day: {max(schedule)}")
        return
    if not TOKEN:
        sys.exit("IG_TOKEN is not set.")

    me = call("GET", "me", fields="user_id,username")
    recent = call("GET", "me/media", fields="caption", limit=30).get("data", [])
    published = {(m.get("caption") or "").strip() for m in recent}
    print(f"Account @{me['username']} — {today}: {len(items)} item(s)")

    for item in items:
        label = f"{item['kind']} {item['url'].rsplit('/', 1)[-1]}"
        if item["caption"].strip() in published:
            print(f"  skip   {label} (already on the account)")
            continue
        if dry:
            print(f"  ready  {label}")
            continue
        if item["kind"] == "reel":
            c = call("POST", f"{me['user_id']}/media", media_type="REELS", video_url=item["url"],
                     caption=item["caption"], share_to_feed="true")["id"]
        else:
            c = call("POST", f"{me['user_id']}/media", image_url=item["url"], caption=item["caption"])["id"]
        wait_until_ready(c, item["kind"])
        post = call("POST", f"{me['user_id']}/media_publish", creation_id=c)["id"]
        link = call("GET", post, fields="permalink").get("permalink", "")
        print(f"  posted {label} -> {link}")
        time.sleep(5)


if __name__ == "__main__":
    main()
