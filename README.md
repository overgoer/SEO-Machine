# SEO Machine

Полноценный AI-пайплайн для генерации SEO-оптимизированных статей. Форк [TheCraigHewitt/seomachine](https://github.com/TheCraigHewitt/seomachine), переработан под сайт **eddytester.com** (ниша QA/API тестирования).

## Что делает

```
Тема + описание → 6 AI-агентов → SEO-статья → HTML → rsync на сервер
```

Каждая статья проходит полный цикл: написание → SEO-аудит → ревизия по замечаниям → мета-теги → внутренние ссылки → проверка ключей → публикация.

## Быстрый старт

```bash
python3 pipeline/pipeline.py \
  --topic "Тестирование idempotency API" \
  --source "Описание темы для seed-контента..." \
  --keywords "ключ1, ключ2" \
  --publish
```

### Доступные флаги

| Флаг | Описание |
|------|----------|
| `--topic` | Тема статьи |
| `--source` | Seed-контент (описание, контекст) |
| `--source-file` | Seed-контент из файла |
| `--keywords` | Целевые ключевые слова через запятую |
| `--publish` | Сгенерировать HTML + rsync на eddytester.com |
| `--html-only` | Только HTML из существующего .md (без перезапуска агентов) |
| `--list-drafts` | Список всех черновиков |
| `--file` | Готовая статья из файла (пропускает написание) |

## Архитектура

```
config.py — PROMPT_VARS, MODEL_CONFIG
  ↓
agent_runner.py — 6 агентов последовательно
  ↓
pipeline.py — CLI + Markdown→HTML + rsync
  ↓
drafts/ — *.md (полные) + *.html (для публикации)
  ↓
rsync → timeweb:/var/www/eddytester.com/
```

### 6 шагов пайплайна

| Шаг | Агент | Что делает |
|-----|-------|------------|
| 1/6 | Editor | Пишет черновик (1500-2500 слов) |
| 2/6 | SEO Optimizer | Анализирует: ключи, структура, ссылки, мета |
| 3/6 | Editor Revision | Исправляет черновик по отчёту SEO |
| 4/6 | Meta Creator | Генерирует title/description/keywords |
| 5/6 | Internal Linker | Подбирает внутренние ссылки |
| 6/6 | Keyword Mapper | Финальная проверка плотности ключей |

### Модели

Все агенты — **deepseek-v4-pro**, max_tokens=16384.

| Агент | Температура |
|-------|-------------|
| Editor | 0.7 |
| SEO Optimizer | 0.3 |
| Editor Revision | 0.7 |
| Meta Creator | 0.5 |
| Internal Linker | 0.3 |
| Keyword Mapper | 0.3 |

## Конфигурация

Всё управляется через `pipeline/config.py`. Основные переменные (PROMPT_VARS):

| Переменная | Значение |
|------------|----------|
| SITE_NAME | eddytester.com |
| SITE_URL | https://eddytester.com |
| PRODUCT_NAME | API Practicum |
| PRODUCT_URL | https://eddytester.com/refactor.html |
| PRODUCT_DESC | практикум по тестированию API с реальными багами |
| AUDIENCE | QA-инженеров, тестировщиков API и автоматизаторов |

Замена значений в PROMPT_VARS автоматически применяется во всех промтах агентов.

## Структура репозитория

```
pipeline/
  config.py           # Конфиг: переменные, модели
  agent_runner.py     # Запуск агентов, inject_vars
  pipeline.py         # CLI + HTML-генерация + деплой
  deepseek_client.py  # Клиент DeepSeek API
  content_scorer.py   # Оценка качества контента

.claude/agents/
  editor.md           # Редактор: стиль, тон, структура, SEO
  seo-optimizer.md    # SEO-оптимизатор
  meta-creator.md     # Генератор мета-тегов
  internal-linker.md  # Внутренняя перелинковка
  keyword-mapper.md   # Карта ключевых слов

drafts/               # Готовые статьи (.md + .html)
```

## Деплой

Статьи публикуются в корень eddytester.com рядом с существующими HTML-страницами (Tilda CMS). Достаточно одного флага `--publish`:

```bash
python3 pipeline/pipeline.py --topic "..." --source "..." --publish
# → https://eddytester.com/statja-YYYY-MM-DD.html
```

Для rsync используется SSH-хост `timeweb` (85.193.81.51:2222, `/var/www/eddytester.com/`).

## Требования

- Python 3.10+
- `pip install markdown`

DeepSeek API ключ — в `DEEPSEEK_API_KEY` (переменная окружения или в config.py).
