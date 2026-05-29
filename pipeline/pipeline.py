#!/usr/bin/env python3
"""
SEO Pipeline - full cycle: content to article to SEO to publish.
Usage:
  python3 pipeline/pipeline.py --topic "HTTP 204" --source "post..."
  python3 pipeline/pipeline.py --list-drafts
  python3 pipeline/pipeline.py --topic "..." --source "..." --html-only
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import markdown

BASE_DIR = Path("/root/SEO-Machine")
sys.path.insert(0, str(BASE_DIR / "data_sources" / "modules"))
from agent_runner import run_all_agents
from config import OUTPUT_DIR


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{TITLE}</title>
  <meta name="description" content="{DESCRIPTION}" />
  <meta name="keywords" content="{KEYWORDS}" />
  <meta property="og:title" content="{TITLE}" />
  <meta property="og:description" content="{DESCRIPTION}" />
  <meta property="og:type" content="article" />
  <link rel="canonical" href="https://eddytester.com/{FILENAME}" />
  <link rel="stylesheet" href="css/tilda-grid-3.0.min.css" />
  <link rel="stylesheet" href="css/custom.css" />
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&subset=latin,cyrillic" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 0; background: #fafafa; font-family: "Montserrat", Arial, sans-serif; }}
    .article-top {{ background: #1a1a1a; padding: 14px 20px; text-align: center; }}
    .article-top a {{ color: #aaa; text-decoration: none; font-size: 13px; padding: 0 14px; transition: color 0.2s; }}
    .article-top a:hover {{ color: #036cff; }}
    .article-wrap {{ max-width: 780px; margin: 0 auto; padding: 40px 24px 60px; }}
    .article-body {{ font-size: 16px; line-height: 1.8; color: #222; }}
    .article-body h1 {{ font-size: 30px; font-weight: 700; margin: 0 0 12px; color: #111; line-height: 1.3; }}
    .article-body h2 {{ font-size: 22px; font-weight: 600; margin: 36px 0 14px; color: #111; line-height: 1.4; }}
    .article-body h3 {{ font-size: 18px; font-weight: 600; margin: 28px 0 10px; color: #222; }}
    .article-body p {{ margin: 0 0 16px; }}
    .article-body a {{ color: #036cff; text-decoration: none; }}
    .article-body a:hover {{ text-decoration: underline; }}
    .article-body code {{ background: #f0f0f0; padding: 2px 7px; border-radius: 3px; font-size: 0.9em; }}
    .article-body pre {{ background: #1a1a2e; color: #e4e4e4; padding: 18px 20px; border-radius: 8px; overflow-x: auto; font-size: 14px; line-height: 1.6; margin: 0 0 16px; }}
    .article-body pre code {{ background: none; padding: 0; color: inherit; font-size: inherit; }}
    .article-body ul, .article-body ol {{ margin: 0 0 16px; padding-left: 24px; }}
    .article-body li {{ margin: 0 0 6px; }}
    .article-body blockquote {{ border-left: 4px solid #036cff; margin: 0 0 16px; padding: 10px 18px; background: #f0f6ff; color: #333; }}
    .article-body hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 32px 0; }}
    .article-meta {{ color: #888; font-size: 13px; margin-bottom: 28px; letter-spacing: 0.3px; }}
    .article-footer {{ margin-top: 44px; padding-top: 24px; border-top: 1px solid #e0e0e0; text-align: center; font-size: 13px; color: #888; }}
    .article-footer a {{ color: #036cff; }}
    img {{ max-width: 100%; height: auto; border-radius: 6px; margin: 16px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0 0 16px; font-size: 14px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
    th {{ background: #f5f5f5; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="article-top">
    <a href="https://eddytester.com">eddytester.com</a>
    <a href="https://eddytester.com/refactor.html">API Practicum</a>
  </div>
  <div class="article-wrap">
    <div class="article-body">
      <div class="article-meta">{DATE} &middot; {WORDS} слов</div>
      {CONTENT}
    </div>
    <div class="article-footer">
      <p>&copy; 2026 eddytester.com</p>
    </div>
  </div>
</body>
</html>"""


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def extract_meta(text):
    meta = {"title": "", "description": "", "keywords": ""}
    m = re.search(r"Meta Title:\s*(.+)", text)
    if m:
        meta["title"] = m.group(1).strip()
    m = re.search(r"Meta Description:\s*(.+)", text)
    if m:
        meta["description"] = m.group(1).strip()
    m = re.search(r"Primary Keyword:\s*(.+)", text)
    if m:
        meta["keywords"] = m.group(1).strip()
    if not meta["title"]:
        m = re.search(r"\*\*\U0001f3c6 RECOMMENDED\*\*.*?\n\*\*Title\*\*:\s*(.+)", text, re.DOTALL)
        if m:
            meta["title"] = m.group(1).strip().rstrip(",").split("\n")[0][:80]
    if not meta["title"]:
        m = re.search(r"Title:\s*(.+)", text)
        if m:
            meta["title"] = m.group(1).strip()[:80]
    return meta


def extract_article_body(md_text):
    """Strip all YAML frontmatter blocks and trailing sections (SEO Report, etc)."""
    body = md_text
    while body.lstrip("\n").startswith("---"):
        body = body.lstrip("\n")
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
        else:
            break
    for sep in ("\n---\n## SEO Report", "\n---\n## Meta Options",
                "\n---\n## Internal Links", "\n---\n## Keyword Analysis"):
        idx = body.find(sep)
        if idx > 0:
            body = body[:idx]
            break
    return body.strip()


def generate_article_html(md_body, meta, slug, publish_date, word_count):
    md = markdown.Markdown(extensions=["fenced_code", "codehilite", "tables"])
    content_html = md.convert(md_body)

    title = meta.get("title", "Article")
    description = meta.get("description", title)
    keywords = meta.get("keywords", "")
    filename = slug + "-" + publish_date + ".html"

    html = HTML_TEMPLATE.format(
        TITLE=title,
        DESCRIPTION=description,
        KEYWORDS=keywords,
        FILENAME=filename,
        DATE=publish_date,
        WORDS=word_count,
        CONTENT=content_html,
    )
    return html


def sep():
    print(chr(61) * 60)


def run_pipeline(topic, source_content, keywords="", internal_links="", publish=False, html_only=False):
    slug = slugify(topic)[:60]
    date = datetime.now().strftime("%Y-%m-%d")
    sep()
    print("  SEO Pipeline: " + topic)
    sep()
    print()

    word_count = 0
    meta = {}

    if not html_only:
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
        word_count = len(results["article"].split())
        print("  Words: " + str(word_count))
        print("  Title: " + meta.get("title", topic)[:80])
        sep()

        article_body = extract_article_body(results["article"])
    else:
        md_files = sorted(OUTPUT_DIR.glob(slug + "-*.md"))
        if not md_files:
            print("  No .md file found for: " + slug)
            sys.exit(1)
        md_content = md_files[-1].read_text()
        meta = extract_meta(md_content)
        meta.update(extract_meta(md_content))
        word_count = len(extract_article_body(md_content).split())
        article_body = extract_article_body(md_content)

    # Generate HTML
    html = generate_article_html(
        md_body=article_body,
        meta=meta,
        slug=slug,
        publish_date=date,
        word_count=word_count,
    )

    html_file = OUTPUT_DIR / (slug + "-" + date + ".html")
    with open(html_file, "w") as f:
        f.write(html)

    print("  HTML: " + str(html_file))
    sep()

    if publish:
        import subprocess
        remote_path = "/var/www/eddytester.com/"
        filename = slug + "-" + date + ".html"
        cmd = ["rsync", "-avz", str(html_file), "timeweb:" + remote_path + filename]
        sep()
        print("  Deploying to Timeweb...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("  Published: https://eddytester.com/" + filename)
        else:
            print("  Deploy failed:")
            for line in result.stderr.split("\n"):
                if line.strip():
                    print("    " + line.strip())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic")
    p.add_argument("--source")
    p.add_argument("--source-file")
    p.add_argument("--keywords", default="")
    p.add_argument("--links", default="")
    p.add_argument("--publish", action="store_true")
    p.add_argument("--html-only", action="store_true")
    p.add_argument("--list-drafts", action="store_true")
    p.add_argument("--file")

    args = p.parse_args()
    if args.list_drafts:
        for f in sorted(OUTPUT_DIR.glob("*.md")):
            sz = f.stat().st_size // 1024
            mt = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print("  " + f.name + "  (" + str(sz) + "KB, " + mt + ")")
        return
    if args.html_only:
        topic = args.topic
        if not topic:
            p.print_help()
            print("\nError: --topic required with --html-only")
            sys.exit(1)
        run_pipeline(topic, "", args.keywords, args.links, args.publish, args.html_only)
        return
    if args.file:
        src = Path(args.file).read_text()
        topic = args.topic or Path(args.file).stem
    elif args.source:
        src = args.source
    elif args.source_file:
        src = Path(args.source_file).read_text()
    else:
        p.print_help()
        print("\nError: need topic + source")
        sys.exit(1)
    run_pipeline(args.topic or "untitled", src, args.keywords, args.links, args.publish, args.html_only)


if __name__ == "__main__":
    main()
