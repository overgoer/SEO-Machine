# BACKLOG — SEO Machine

> Репозиторий: https://github.com/overgoer/SEO-Machine
> Сервер: Amsterdam (77.73.135.110)
> Сайт: eddytester.com
> Деплой: Timeweb (85.193.81.51:2222)

---

## Текущие задачи

### [DONE] Пайплайн генерации статей (6 шагов)
- [x] Editor — первая версия статьи
- [x] SEO Optimizer — аудит
- [x] Editor Revision — исправление по отчёту SEO
- [x] Meta Creator — title/description/keywords
- [x] Internal Linker — внутренние ссылки
- [x] Keyword Mapper — финальная проверка ключей
- [x] HTML-генерация из Markdown
- [x] Deploy на Timeweb через rsync

### [DONE] Ребрендинг Castos → eddytester.com
- [x] PROMPT_VARS в config.py (SITE_NAME, PRODUCT_NAME, PRODUCT_URL и т.д.)
- [x] Editor, SEO Optimizer, Meta Creator, Linker, Mapper — промты переписаны под QA/API
- [x] Meta Creator — формат вывода (Meta Title: / Meta Description: / Primary Keyword:)

### [IN PROGRESS] Качество контента
- [ ] Структура вступления — максимум 5 предложений, TL;DR/bullets, сразу мясо
- [ ] Запрет на выдуманные изображения и несуществующие ссылки (блог)
- [ ] First-person voice (AI impersonation) — решить, допустимо или нет
- [ ] Проверить плотность ключей после ревизии
- [ ] Внешние ссылки на авторитетные источники (RFC, документация) — добавить

### [TODO] Ключевые слова и спрос
- [ ] Serper API — сбор ключей по нише API testing/QA
- [ ] Yandex Wordstat — интеграция через MCP сервер или Python
- [ ] Фильтрация: search volume + конкуренция
- [ ] Сформировать очередь из 10-20 тем с данными о спросе

### [TODO] Инфраструктура
- [ ] Исправить ContentScorer (numpy/scipy compatibility)
- [ ] Чистые URL без даты (slug вместо slug-YYYY-MM-DD)
- [ ] Sitemap для статей
- [ ] Robots.txt — убрать запрет на индексацию, если есть
- [ ] Schema.org/Article разметка в HTML

### [TODO] Метрики и аналитика
- [ ] Google Search Console — подключить
- [ ] Яндекс.Вебмастер — подключить
- [ ] Отслеживание позиций по ключам
- [ ] A/B тесты заголовков

---

## Текущая архитектура

```
config.py (PROMPT_VARS, MODEL_CONFIG)
      ↓
agent_runner.py (inject_vars → run_agent → run_all_agents)
      ↓
pipeline.py (CLI: --topic --source --keywords --publish --html-only)
      ↓
drafts/ (article-YYYY-MM-DD.md + article-YYYY-MM-DD.html)
      ↓
rsync → timeweb:/var/www/eddytester.com/
```

## Модель

Все агенты: deepseek-v4-pro, max_tokens=16384

| Агент | temp |
|-------|------|
| Editor | 0.7 |
| SEO Optimizer | 0.3 |
| Editor Revision | 0.7 |
| Meta Creator | 0.5 |
| Internal Linker | 0.3 |
| Keyword Mapper | 0.3 |

## PROMPT_VARS (config.py)

| Переменная | Значение |
|------------|----------|
| SITE_NAME | eddytester.com |
| SITE_URL | https://eddytester.com |
| PRODUCT_NAME | API Practicum |
| PRODUCT_URL | https://eddytester.com/refactor.html |
| PRODUCT_DESC | практикум по тестированию API с реальными багами |
| AUDIENCE | QA-инженеров, тестировщиков API и автоматизаторов |

## Команды

```bash
# Полный цикл: статья → SEO → реалия → мета → ссылки → ключи → HTML → деплой
python3 pipeline/pipeline.py --topic "Тема" --source "Описание" --keywords "ключ1, ключ2" --publish

# Только HTML из существующего .md
python3 pipeline/pipeline.py --topic "slug-temy" --html-only

# Только HTML + деплой
python3 pipeline/pipeline.py --topic "slug-temy" --html-only --publish

# Список черновиков
python3 pipeline/pipeline.py --list-drafts
```

## SSH

| Хост | Адрес | Назначение |
|------|-------|------------|
| amsterdam | 77.73.135.110 | Сервер с SEO Machine |
| timeweb | 85.193.81.51:2222 | Хостинг eddytester.com |
