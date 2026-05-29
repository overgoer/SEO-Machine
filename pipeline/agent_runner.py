"""Loads agent prompts and calls DeepSeek with prompt variable injection."""
from pathlib import Path
from deepseek_client import call
from config import AGENTS_DIR, MODEL_CONFIG, PROMPT_VARS


def inject_vars(text):
    """Replace {VARIABLE_NAME} placeholders with values from PROMPT_VARS.
    Uses simple replacement (not .format()) so JSON braces in prompts are safe."""
    for key, val in PROMPT_VARS.items():
        text = text.replace("{" + key + "}", val)
    return text


def load_agent_prompt(agent_name):
    path = AGENTS_DIR / (agent_name + ".md")
    if not path.exists():
        raise FileNotFoundError("Agent not found: " + str(path))
    return path.read_text()


def run_agent(agent_name, user_content, extra_instructions=""):
    system = load_agent_prompt(agent_name)
    # Inject prompt variables
    system = inject_vars(system)
    if extra_instructions:
        system = system + "\n\n## Additional instructions\n" + extra_instructions
    cfg = MODEL_CONFIG.get(agent_name, MODEL_CONFIG.get("seo-optimizer", {}))
    return call(
        system_prompt=system,
        user_prompt=user_content,
        model=cfg.get("model", "deepseek-v4-pro"),
        temperature=cfg.get("temp", 0.3),
        max_tokens=cfg.get("max_tokens", 16384),
    )


def run_all_agents(topic, source_content, target_keywords="", internal_links=""):
    results = {}

    print("  [1/6] Editor -- writing article...", flush=True)
    editor_input = (
        "Topic: " + topic + "\n"
        "Source content: " + source_content + "\n"
        "Target keywords: " + target_keywords + "\n\n"
        "Write a comprehensive, actionable article (1500-2500 words) "
        "for QA engineers and API testers.\n"
        "SEO requirements (apply during writing):\n"
        "- Primary keyword density: ~0.5-1% (appear every 100-200 words)\n"
        "- Every H2 heading MUST contain the primary keyword or a close variant\n"
        "- Primary keyword must appear in the first 100 words\n"
        "- Add hyperlinks to authoritative sources (RFCs, official docs) "
        "when technologies are mentioned\n"
        "- Naturally reference {SITE_NAME} and {PRODUCT_NAME} ({PRODUCT_DESC}) "
        "where contextually relevant\n"
        "- Include CTA linking to {PRODUCT_URL}"
    )
    results["article"] = run_agent("editor", editor_input)
    article = results["article"]

    print("  [2/6] SEO Optimizer -- optimizing...", flush=True)
    results["seo_report"] = run_agent("seo-optimizer", article)

    print("  [3/6] Editor -- revision based on SEO report...", flush=True)
    revision_input = (
        "You wrote this article:\n\n" + article + "\n\n"
        "Your SEO Optimizer produced this report. Address ALL issues:\n\n"
        + results["seo_report"] + "\n\n"
        "Requirements:\n"
        "- Increase primary keyword density to ~0.5-1%\n"
        "- Include primary keyword in ALL H2 headings\n"
        "- Add external links to authoritative sources where technologies are mentioned\n"
        "- Keep all practical examples, curl commands, and CTA for {PRODUCT_NAME}\n"
        "- Preserve the same overall structure and word count (~1500-2500 words)\n"
        "- Do NOT cut substance when fixing"
    )
    results["article"] = run_agent("editor", revision_input)
    article = results["article"]

    print("  [4/6] Meta Creator -- generating meta tags...", flush=True)
    results["meta"] = run_agent("meta-creator",
        "Article:\n" + article + "\n\nTarget keywords: " + target_keywords)

    print("  [5/6] Internal Linker -- building links...", flush=True)
    results["links"] = run_agent("internal-linker",
        "Article:\n" + article + "\n\nInternal links: " + internal_links)

    print("  [6/6] Keyword Mapper -- final keyword check...", flush=True)
    results["keywords"] = run_agent("keyword-mapper",
        "Article:\n" + article + "\n\nTarget keywords: " + target_keywords)

    return results
