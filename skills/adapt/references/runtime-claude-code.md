# Адаптер: Claude Code

Читайте, только если среди клиентов проекта есть Claude Code. Общие правила — `wiring.md`.

## Скилы и агенты

- Скилы Claude Code ищет в `.claude/skills/` проекта (установщик кладёт их туда напрямую или
  симлинками) и в `~/.claude/skills/`.
- Именованные агенты — файлы `.claude/agents/<роль>.md` проекта. Для каждой роли из
  `references/agents/` скила `dev` создать файл: frontmatter `name`, `description` — из файла
  роли; `tools`, `model`, `effort` — из таблицы в `references/runtime-claude-code.md` скила
  `dev`; тело — тело файла роли без изменений. Без `memo` убрать инструменты `mcp__memo__*`,
  без `context7` — `mcp__context7__*`. Есть ли `context7`: сервер в `.mcp.json` проекта, в
  `~/.claude.json` или инструменты `mcp__context7__*` в текущей сессии; не найден нигде —
  убрать и назвать в отчёте (пользователь может вернуть после подключения).
- Агенты читаются при старте сессии: после создания — назвать перезапуск ручным шагом.

## Файл правил

`CLAUDE.md`. Если правила пишутся в `AGENTS.md` (есть и другие клиенты), в `CLAUDE.md` нужна
строка `@AGENTS.md` — Claude Code подставит файл целиком.

## Память `memo`

Шаблоны — `assets/claude-code/`:

- `mcp.json` → слить в `.mcp.json` проекта: ключ `mcpServers.memo`, другие серверы не трогать;
  `env.DEEPSEEK_API_KEY` оставить в форме `${DEEPSEEK_API_KEY:-}` — значение memo берёт из
  `.env` рядом с `agentmemory.toml`.
- `settings.json` → слить хуки в `.claude/settings.json`: для событий `SessionStart` и
  `UserPromptSubmit` добавить хук `memo` в массив `hooks[<событие>]`, не заменяя существующие;
  хук с подстрокой `memo` и тем же `-event` уже есть — пропустить.
- `<путь-к-memo>` заменить фактическим путём из `command -v memo`.
- `${CLAUDE_PROJECT_DIR:-.}` оставить как есть: Claude Code раскрывает его в корень проекта.
