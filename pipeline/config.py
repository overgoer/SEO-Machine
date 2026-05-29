import os
from pathlib import Path

BASE_DIR = Path("/root/SEO-Machine")
AGENTS_DIR = BASE_DIR / ".claude" / "agents"
MODULES_DIR = BASE_DIR / "data_sources" / "modules"
OUTPUT_DIR = BASE_DIR / "drafts"

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.environ.get(
    "DEEPSEEK_API_KEY",
    "sk-ec80e4519216494fa74911e5f365e8ff"
)

# Prompt variables — injected into all agent prompts via {variable_name}.
# Change values here to update site name, URLs, and product info everywhere.
PROMPT_VARS = {
    "SITE_NAME": "eddytester.com",
    "SITE_URL": "https://eddytester.com",
    "PRODUCT_NAME": "API Practicum",
    "PRODUCT_URL": "https://eddytester.com/refactor.html",
    "PRODUCT_DESC": "практикум по тестированию API с реальными багами",
    "AUDIENCE": "QA-инженеров, тестировщиков API и автоматизаторов",
}

MODEL_CONFIG = {
    "editor": {"model": "deepseek-v4-pro", "temp": 0.7, "max_tokens": 16384},
    "seo-optimizer": {"model": "deepseek-v4-pro", "temp": 0.3, "max_tokens": 16384},
    "meta-creator": {"model": "deepseek-v4-pro", "temp": 0.5, "max_tokens": 16384},
    "internal-linker": {"model": "deepseek-v4-pro", "temp": 0.3, "max_tokens": 16384},
    "keyword-mapper": {"model": "deepseek-v4-pro", "temp": 0.3, "max_tokens": 16384},
    "content-analyzer": {"model": "deepseek-v4-pro", "temp": 0.3, "max_tokens": 16384},
}

OUTPUT_DIR.mkdir(exist_ok=True)
