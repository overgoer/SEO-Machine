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
    print("  [1/5] Editor -- writing article...", flush=True)
    editor_input = (
        "Topic: " + topic + "\n"
        "Source content: " + source_content + "\n"
        "Target keywords: " + target_keywords + "\n\n"
        "Write a comprehensive, actionable article (1500-2500 words) "
        "for QA engineers and API testers."
    )
    results["article"] = run_agent("editor", editor_input)
    article = results["article"]

    print("  [2/5] SEO Optimizer -- optimizing...", flush=True)
    results["seo_report"] = run_agent("seo-optimizer", article)

    print("  [3/5] Meta Creator -- generating meta tags...", flush=True)
    results["meta"] = run_agent("meta-creator",
        "Article:\n" + article + "\n\nTarget keywords: " + target_keywords)

    print("  [4/5] Internal Linker -- building links...", flush=True)
    results["links"] = run_agent("internal-linker",
        "Article:\n" + article + "\n\nInternal links: " + internal_links)

    print("  [5/5] Keyword Mapper -- final keyword check...", flush=True)
    results["keywords"] = run_agent("keyword-mapper",
        "Article:\n" + article + "\n\nTarget keywords: " + target_keywords)

    return results
