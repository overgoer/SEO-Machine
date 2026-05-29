#!/usr/bin/env python3
"""
Fetch top posts from eddytester Telegram channel by engagement.

Usage:
  python3 fetch_top_posts.py                    # fetch last 200, show top 10
  python3 fetch_top_posts.py --limit 500        # fetch 500 posts
  python3 fetch_top_posts.py --top 5            # show top 5
  python3 fetch_top_posts.py --save             # save to JSON
  python3 fetch_top_posts.py --save-obsidian    # save to Obsidian vault
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient

CHANNEL = "@eddytester"
SESSION = "/root/.telethon_edtext"
API_ID = 5
API_HASH = "1c5c96d5edd401b1ed40db3fb5633e2d"
OUT_DIR = Path("/root/blog-analysis/agents/scout/raw")


def engagement_score(msg):
    """Calculate engagement score from available metrics."""
    views = getattr(msg, "views", 0) or 0
    forwards = getattr(msg, "forwards", 0) or 0
    replies = getattr(msg, "replies", None)
    reply_count = replies.replies if replies else 0

    reactions = 0
    if hasattr(msg, "reactions") and msg.reactions:
        results = getattr(msg.reactions, "results", [])
        if results:
            reactions = sum(getattr(r, "count", 0) or 0 for r in results)

    score = views * 0.5 + forwards * 0.2 + reactions * 0.2 + reply_count * 0.1
    return round(score, 1), views, forwards, reactions, reply_count


async def fetch_posts(limit=200):
    print(f"Connecting to {CHANNEL}...", flush=True)
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()

    try:
        entity = await client.get_entity(CHANNEL)
        print(f"Channel: {entity.title if hasattr(entity, 'title') else CHANNEL}", flush=True)

        messages = await client.get_messages(entity, limit=limit)
        print(f"Fetched {len(messages)} messages", flush=True)

        posts = []
        for msg in messages:
            if not msg.text or not msg.text.strip():
                continue

            score, views, forwards, reactions, replies = engagement_score(msg)
            posts.append({
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "text": msg.text[:500] if msg.text else "",
                "views": views,
                "forwards": forwards,
                "reactions": reactions,
                "replies": replies,
                "engagement_score": score,
                "has_media": bool(msg.media),
            })

        posts.sort(key=lambda p: p["engagement_score"], reverse=True)
        return posts

    finally:
        await client.disconnect()


def main():
    limit = 200
    top_n = 10
    save_json = False
    save_obsidian = False

    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
        elif arg.startswith("--top="):
            top_n = int(arg.split("=")[1])
        elif arg == "--save":
            save_json = True
        elif arg == "--save-obsidian":
            save_obsidian = True

    posts = asyncio.run(fetch_posts(limit))
    total = len(posts)

    print()
    print(f"{'='*70}")
    print(f"  @eddytester — Top {top_n} of {total} posts by engagement")
    print(f"{'='*70}")
    print(f"  {'#':>3} │ {'Score':>7} │ {'Views':>6} │ {'Reacts':>6} │ {'Fwd':>4} │ {'Repl':>3} │ Date")
    print(f"{'-'*70}")

    for i, p in enumerate(posts[:top_n], 1):
        text_preview = p["text"][:60].replace("\n", " ")
        print(f"  {i:>3} │ {p['engagement_score']:>7} │ {p['views']:>6} │ {p['reactions']:>6} │ {p['forwards']:>4} │ {p['replies']:>3} │ {p['date'][:10] if p['date'] else 'N/A'}")
        print(f"       {text_preview}...")

    print(f"{'='*70}")

    # Show text of top 1
    if posts:
        print()
        print(f"=== TOP POST (score: {posts[0]['engagement_score']}) ===")
        print(posts[0]["text"][:800])

    # Save
    if save_json:
        date = datetime.now().strftime("%Y%m%d")
        fname = OUT_DIR / f"eddytester_engagement_{date}.json"
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        # Преобразуем datetime в строку для JSON сериализации
        output_data = {
            "exported_at": datetime.now().isoformat(),
            "channel": CHANNEL,
            "total": total,
            "top": posts[:top_n],
            "all": posts,
        }

        # Рекурсивно превращаем datetime в строку
        def serialize(obj):
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(v) for v in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        with open(fname, "w", encoding="utf-8") as f:
            json.dump(serialize(output_data), f, ensure_ascii=False, indent=2)
        print(f"\nSaved to: {fname}")

    if save_obsidian:
        vault = Path("/root/obsidian-vault/eddytester")
        obs_file = vault / "TG топ посты.md"
        with open(obs_file, "w", encoding="utf-8") as f:
            f.write(f"# Топ постов @eddytester по вовлечению\n\n")
            f.write(f"Всего: {total} · Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"| # | Score | Views | Реакции | Репосты | Ответы | Превью |\n")
            f.write(f"|---|---|---|---|---|---|---|\n")
            for i, p in enumerate(posts[:top_n], 1):
                preview = p["text"][:50].replace("\n", " ").replace("|", "/")
                f.write(f"| {i} | {p['engagement_score']} | {p['views']} | {p['reactions']} | {p['forwards']} | {p['replies']} | {preview} |\n")
            f.write(f"\n---\n### Полный текст топа\n\n")
            for i, p in enumerate(posts[:5], 1):
                f.write(f"### {i}. Score: {p['engagement_score']} (views: {p['views']})\n\n")
                f.write(f"{p['text']}\n\n---\n\n")
        print(f"Saved to Obsidian: {obs_file}")


if __name__ == "__main__":
    main()
