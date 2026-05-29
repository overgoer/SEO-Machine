#!/usr/bin/env python3
"""
SEO Pipeline - full cycle: content to article to SEO to publish.
Usage:
  python3 pipeline/pipeline.py --topic "HTTP 204" --source "post..."
  python3 pipeline/pipeline.py --list-drafts
"""
import argparse, re, sys
from datetime import datetime as dt
from pathlib import Path

BASE_DIR = Path("/root/SEO-Machine")
sys.path.insert(0, str(BASE_DIR / "data_sources" / "modules"))
from agent_runner import run_all_agents
from config import OUTPUT_DIR

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def extract_meta(text):
    """Parse meta fields from agent output. Tries multiple formats."""
    meta = {"title": "", "description": "", "keywords": ""}

    # Format 1: explicit "Meta Title:" / "Meta Description:" / "Primary Keyword:" lines
    m = re.search(r"Meta Title:\s*(.+)", text)
    if m: meta["title"] = m.group(1).strip()
    m = re.search(r"Meta Description:\s*(.+)", text)
    if m: meta["description"] = m.group(1).strip()
    m = re.search(r"Primary Keyword:\s*(.+)", text)
    if m: meta["keywords"] = m.group(1).strip()

    # Format 2: "Recommended" title from Meta Creator options
    if not meta["title"]:
        m = re.search(r"\*\*🏆 RECOMMENDED\*\*.*?\n\*\*Title\*\*:\s*(.+)", text, re.DOTALL)
        if m: meta["title"] = m.group(1).strip().rstrip(",").split("\n")[0][:80]

    # Format 3: fallback — first "Title:" line with reasonable content
    if not meta["title"]:
        m = re.search(r"Title:\s*(.+)", text)
        if m: meta["title"] = m.group(1).strip()[:80]

    return meta

def sep():
    print(chr(61) * 60)

def run_pipeline(topic, source_content, keywords="", internal_links="", publish=False):
    slug = slugify(topic)[:60]
    date = dt.now().strftime("%Y-%m-%d")
    sep(); print("  SEO Pipeline: " + topic); sep(); print()

    results = run_all_agents(topic, source_content, keywords, internal_links)

    score = None
    try:
        from content_scorer import ContentScorer
        scorer = ContentScorer()
        score = scorer.score(results["article"])
        print("  Content Score: " + str(score.get("composite", "N/A")) + "/100")
    except Exception as e:
        print("  Content scorer skipped: " + str(e))

    meta = extract_meta(results["article"])
    meta.update(extract_meta(results.get("meta", "")))

    output_file = OUTPUT_DIR / (slug + "-" + date + ".md")
    with open(output_file, "w") as f:
        f.write("---\n" + "title: " + meta.get("title", topic) + "\n")
        f.write("date: " + date + "\n")
        f.write("topic: " + topic + "\n")
        f.write("keywords: " + meta.get("keywords", keywords) + "\n")
        f.write("description: " + meta.get("description", "") + "\n")
        if score:
            f.write("quality_score: " + str(score.get("composite", "N/A")) + "\n")
        f.write("---\n\n" + results["article"])
        f.write("\n\n---\n## SEO Report\n\n" + results.get("seo_report", ""))
        f.write("\n\n---\n## Meta Options\n\n" + results.get("meta", ""))
        f.write("\n\n---\n## Internal Links\n\n" + results.get("links", ""))
        f.write("\n\n---\n## Keyword Analysis\n\n" + results.get("keywords", ""))

    sep()
    print("  Saved: " + str(output_file))
    print("  Words: " + str(len(results["article"].split())))
    print("  Title: " + meta.get("title", topic)[:80])
    sep()

    if publish:
        try:
            from wordpress_publisher import WordPressPublisher
            publisher = WordPressPublisher()
            result = publisher.publish(
                title=meta.get("title", topic),
                content=results["article"],
                slug=slug,
                meta_description=meta.get("description", ""),
                focus_keyword=meta.get("keywords", keywords),
            )
            print("  Published: " + str(result.get("url", "OK")))
        except Exception as e:
            print("  Publish failed: " + str(e))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic"); p.add_argument("--source")
    p.add_argument("--source-file"); p.add_argument("--keywords", default="")
    p.add_argument("--links", default=""); p.add_argument("--publish", action="store_true")
    p.add_argument("--list-drafts", action="store_true"); p.add_argument("--file")

    args = p.parse_args()
    if args.list_drafts:
        for f in sorted(OUTPUT_DIR.glob("*.md")):
            sz = f.stat().st_size // 1024
            mt = dt.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print("  " + f.name + "  (" + str(sz) + "KB, " + mt + ")")
        return
    if args.file:
        src = Path(args.file).read_text()
        topic = args.topic or Path(args.file).stem
    elif args.source:
        src = args.source
    elif args.source_file:
        src = Path(args.source_file).read_text()
    else:
        p.print_help(); print("\nError: need topic + source"); sys.exit(1)
    run_pipeline(args.topic or "untitled", src, args.keywords, args.links, args.publish)

if __name__ == "__main__":
    main()
