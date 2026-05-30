# CLAUDE.md — SEO Machine / eddytester.com

## Проект

SEO Machine — AI-пайплайн генерации SEO-статей для eddytester.com (ниша QA/API тестирования).
Форк https://github.com/TheCraigHewitt/seomachine, переработан под продуктовый сайт с деплоем на Timeweb.

## Архитектура

```
config.py → agent_runner.py (6 агентов) → pipeline.py (CLI + HTML + rsync)
```

Ключевой файл: `pipeline/config.py` — содержит PROMPT_VARS (брендовые переменные) и MODEL_CONFIG.

### Агенты (порядок выполнения)

1. editor — пишет черновик
2. seo-optimizer — аудит статьи
3. editor — revision: исправляет по отчёту SEO
4. meta-creator — title/description/keywords
5. internal-linker — внутренние ссылки
6. keyword-mapper — финальная проверка

### Команды пайплайна

```bash
python3 pipeline/pipeline.py --topic "..." --source "..." --keywords "..." --publish
python3 pipeline/pipeline.py --topic "slug" --html-only              # только HTML
python3 pipeline/pipeline.py --topic "slug" --html-only --publish     # HTML + деплой
python3 pipeline/pipeline.py --list-drafts                           # список статей
```

## Конфигурация

PROMPT_VARS в config.py. Менять тут — применяется во всех промтах агентов.

Ключевые переменные: {SITE_NAME}, {PRODUCT_NAME}, {PRODUCT_URL}, {PRODUCT_DESC}, {AUDIENCE}.

Все агенты: deepseek-v4-pro, max_tokens=16384.

## Важные правила при работе с кодом

- inject_vars() использует str.replace(), не .format() — в промтах JSON-фигурные скобки
- Meta Creator должен выдавать "Meta Title:" / "Meta Description:" / "Primary Keyword:" в конце ответа — pipeline парсит эти строки
- HTML_TEMPLATE использует str.format() — CSS-скобки должны быть экранированы {{ }}
- extract_article_body() отрезает блоки YAML frontmatter и секции после "--- ## SEO Report"

## Деплой

Хост timeweb: 85.193.81.51:2222, /var/www/eddytester.com/
Pipeline → rsync HTML → eddytester.com/{slug}-{date}.html

## SSH

- amsterdam (77.73.135.110) — сервер с SEO Machine
- timeweb — хостинг eddytester.com (через amsterdam)
- ssh timeweb с amsterdam работает напрямую

## Полезное

- Serper API ключ: /root/.openclaw/.env
- Все изменения коммитить в git после каждой логической единицы работы
- BACKLOG.md — текущий статус задач
- Тестовый запуск: не меньше 20 минут на 6 шагов V4 Pro
