#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тянет последние посты публичного Telegram-канала и пишет feed.json
для блока rabdanova.ru/yandex-tg (мини-лента «3 последних поста»).

БЕЗ внешних зависимостей (только стандартная библиотека) — чтобы легко
крутиться в GitHub Actions без pip install.

По умолчанию — ТЕКСТ-ОНЛИ (без картинок): безопасно для модерации
Яндекс.Директа. Картинки постов НЕ сохраняются.

Использование:
    python3 fetch_feed.py --channel dr_rabdanova --out feed.json --limit 3
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch_html(channel: str) -> str:
    url = "https://t.me/s/{}".format(channel)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "ru,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def strip_html(fragment: str) -> str:
    # <br> и блочные теги → пробел, остальные теги убираем
    fragment = re.sub(r"<br\s*/?>", " ", fragment, flags=re.I)
    fragment = re.sub(r"</(p|div)>", " ", fragment, flags=re.I)
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def rel_ru(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    secs = (now - dt).total_seconds()
    if secs < 0:
        secs = 0
    mins = int(secs // 60)
    hours = int(secs // 3600)
    days = int(secs // 86400)
    if mins < 60:
        return "только что" if mins < 5 else "{} мин".format(mins)
    if hours < 24:
        return "{} ч".format(hours)
    if days == 1:
        return "вчера"
    if days < 7:
        return "{} дн".format(days)
    weeks = days // 7
    if weeks < 5:
        return "{} нед".format(weeks)
    months = days // 30
    return "{} мес".format(max(1, months))


def parse_posts(page: str, channel: str):
    posts = []
    # каждый пост — <div class="tgme_widget_message ..." data-post="chan/123" ...> ... </div>
    blocks = re.split(r'(?=<div class="tgme_widget_message[ "])', page)
    for b in blocks:
        m_post = re.search(r'data-post="([^"]+)"', b)
        if not m_post:
            continue
        post_id = m_post.group(1)  # "channel/123"

        # отрезаем реакции/футер, чтобы счётчики (🔥5❤4) не попали в текст
        bcut = re.split(r'<div class="tgme_widget_message_(?:reactions|footer)', b)[0]
        m_text = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            bcut, re.S)
        text = strip_html(m_text.group(1)) if m_text else ""

        if "tgme_widget_message_video_player" in b or "tgme_widget_message_roundvideo" in b:
            ptype = "video"
        elif "tgme_widget_message_photo_wrap" in b:
            ptype = "photo"
        else:
            ptype = "text"

        m_dt = re.search(r'<time[^>]+datetime="([^"]+)"', b)
        iso = m_dt.group(1) if m_dt else None
        ago = ""
        if iso:
            try:
                dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
                ago = rel_ru(dt)
            except ValueError:
                pass

        if not text and ptype == "text":
            continue  # пустой служебный пост — пропускаем

        posts.append({
            "text": text or ("Видео" if ptype == "video" else "Фото"),
            "url": "https://t.me/{}".format(post_id),
            "type": ptype,
            "ago": ago,
            "date": iso or "",
        })
    return posts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="dr_rabdanova")
    ap.add_argument("--out", default="feed.json")
    ap.add_argument("--limit", type=int, default=3)
    args = ap.parse_args()

    try:
        page = fetch_html(args.channel)
    except Exception as e:  # noqa
        print("ERROR fetching channel:", e, file=sys.stderr)
        return 2

    posts = parse_posts(page, args.channel)
    if not posts:
        print("ERROR: no posts parsed (разметка t.me могла измениться)", file=sys.stderr)
        return 3

    # t.me/s отдаёт по возрастанию (свежие внизу) → берём последние N, новые сверху
    latest = list(reversed(posts))[:args.limit]

    out = {
        "channel": args.channel,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "posts": latest,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("OK: wrote {} posts → {}".format(len(latest), args.out))
    for p in latest:
        print("  [{}] {} — {}".format(p["type"], p["ago"], p["text"][:70]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
