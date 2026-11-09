# Skills

Репозиторий для создания переносимых скилов ИИ-агентов с помощью Claude Code.
Формат — [Agent Skills](https://agentskills.io/specification), установка — стандартный
[skills CLI](https://github.com/vercel-labs/skills), который используется на skills.sh.
Собственного установщика здесь нет.

## Публичные скилы

| Скил | Назначение | Внешние требования |
|---|---|---|
| [orchestrate](skills/orchestrate/SKILL.md) | Тонкий parent: реальные child-сессии, делегированный dev-цикл, независимая проверка и восстановление v3 | Claude Code Desktop: запуск, адресуемая связь и сверка сессий; настроенный MCP memo с подтверждённым project scope |
| [session-worker](skills/session-worker/SKILL.md) | Scout/planner/dev-lead/worker/verifier: полные details у потребителей, короткий результат parent | Desktop с межсессионной связью и полный brief v3; без memo нужен независимый verifier с memo и проверяемыми источниками evidence |

Универсальны по типу работы: разработка, исследование и документация. Формат переносимый,
но эта версия намеренно требует Desktop-возможностей: CLI, tmux и субагенты не являются
скрытой заменой настоящих сессий. Установка скилов не устанавливает MCP и не выдаёт доступы.
Шаблон в `templates/` не является готовым скилом и не появляется в списке установки.

## Структура

```text
skills/                         распространяемые скилы: по каталогу на скил
  orchestrate/                  координатор Desktop-сессий и memo-протокол
    SKILL.md                    метаданные и основной сценарий
    references/                 контракты, runtime, bootstrap и сценарии проверки
  session-worker/               самостоятельный исполнитель
    SKILL.md                    роль, ready/grant, выполнение, ограничения
    references/                 полный контракт назначения и отчёта
templates/skill/SKILL.md.template  шаблон для авторинга, не готовый скил
scripts/check-skills.sh          проверка метаданных публичного каталога
.claude/skills/                  служебные скилы разработки, включая /dev и /adapt
.claude/agents/                  служебные агенты разработки
CLAUDE.md                       стабильные правила этого проекта
REVIEW.md                       риск изменений и контракт ревью
agentmemory.toml                локальная настройка memo, scope project:Skills
```

`skills/` и `.claude/skills/` имеют разные роли. CLI обнаруживает оба каталога при установке
из корня репозитория. Чтобы получить только распространяемые скилы, передавайте CLI путь
именно к `skills/`. Это соглашение о пути установки, а не механизм скрытия служебных скилов.

## Работа через дочерние сессии

Пример запроса после проектной установки:

```text
/orchestrate economy
Выполни две независимые проверки документации через дочерние Desktop-сессии.
Не меняй файлы. Верни проверяемые источники и противоречия.
```

Главная цель v3 — меньше **контекста родителя**. Scout/planner исследуют проект и скилы,
пишут brief/design; dev-lead ведёт полноценный локальный dev-цикл; независимый verifier читает
артефакты и доказательства. Parent сохраняет scheduling, grants, физическое владение,
решения человека и итоговую acceptance. Он не читает по умолчанию исходники/full diff/raw logs,
не загружает все references перед стартом и не повторяет тесты. Уже накопленная история не
удаляется. Дополнительный audit может увеличить общую стоимость/время; проценты без замеров
не обещаются.

Одна цель / вызов orchestrate включает автономную работу и разрешённые child-запуски parent
до итоговой Git/артефактной acceptance, без approval каждого плана/этапа/волны. Если режим
не указан, parent выбирает соразмерный цели/контексту и кратко сообщает без обязательного
вопроса: **economy — до 2**, **fast — без числового потолка по умолчанию**. Явные mode/cap/budget
пользователя сохраняются. «Fast» означает `active_limit: null` (безлимит), «fast, не более N» —
положительный целый cap N без второго обязательного вопроса о лимите. Нет числа при fast —
не блокер/запрос расширения; 0, отрицательный или нецелый cap требует уточнения, не игнорируется.
Cap общий для всех ролей, включая integrator и bounded agents; intent/ready/uncertain тоже
занимают слот. Численная проверка занятых/зарезервированных слотов нужна только при ненулевом
cap; превысить его можно лишь по новому решению пользователя. Resume сохраняет null/N/economy 2,
без скрытого потолка. Новые сессии — лишь для полезной независимой работы; отдельные пределы
bounded subagents и критерии качества сохраняются. Только parent
создаёт Desktop-сессии, child не запускает скрытое дерево. Модель/effort/permissions parent
не меняются. Доступный проектный `dev` обязателен у dev-lead разработки; read-only scout/
research/verifier используют только назначенные применимые процедуры, не полный dev-цикл.
Отсутствие/конфликт сообщается, общий dev не переписывается и зависимости скрытно не устанавливаются.

Координация — **только memo**, без task/status/handoff/log-файлов. Малые parent-owned
root/current_frontier/control физически отделены от full brief/design/result/evidence.
Parent заранее создаёт detail IDs, подтверждает scope и назначает одному writer точные IDs/
операции; это контракт ролей, не серверный ACL. Непосредственный исполнитель/verifier читает
полные details. Status/resume не перечитывает полный brief/evidence/историю закрытых задач.
Полное ТЗ передаёт все решения и критерии, но доступные документы/dev/worker/bootstrap
читаются child по точным ссылкам; inline — важные решения человека/нетранслируемый контекст.

Предпочтителен `session-worker`; автономный bootstrap уже входит в orchestrate. Проверенный
доступный файл читается напрямую, целиком inline передаётся лишь при недоступности пути.
Регистрация Skill и доступность файла различаются. **v3 несовместим с v1/v2**: обновите установленные
копии обоих используемых пакетов согласованно; старые brief/worker не принимаются молча.

Исполнитель проходит intent/bind/`ready`/`grant`. Один writer на физический ресурс, включая
симлинки/hardlinks/алиасы и побочные записи; read/write конфликты тоже исключаются. Общий
checkout обычен; worktree и внешние эффекты требуют отдельного решения. Submission
закрепляет версию/manifest/details, release подтверждает остановку процессов. Независимый
verifier (не автор результата) получает отдельный **read-grant после release, до acceptance**,
сам строит полный inventory изменений против baseline (tracked/untracked/new/deleted,
mode/type/link-target/side effects), не доверяет перечню автора; сверяет ownership и manifest.
Pin различает presence/deletion, kind, релевантный mode, symlink target и SHA-256 regular bytes;
verifier повторяет inventory/все свойства в конце. Нет полного baseline/inventory — blocked.
До решения parent новые writer запрещены. Только явная acceptance=accepted открывает downstream;
rejected/paused/release и снятие reservation для repair не открывают его. Изменения после аудита
инвалидируют verdict. Parent проверяет источник/корреляцию/независимость/версию и точное
равенство criterion IDs compact receipt своему frozen expected_criterion_ids, с совпадающим
criteria_version. Этот авторитетный набор/версия сохранён в малом control до grant и доступен
после resume без full brief. Parent не повторяет содержательную проверку. Repair остаётся
у того же actor, два на стратегию с новыми версиями/detail IDs. После двух неудач parent
автономно исследует причину/brief/разбиение/тест и меняет подход; attempt и история
не обнуляются, нужен проверяемый progress, не бесконечный повтор или fanout. Обоснованная
замена actor только после фактических stop/release/сверки остаточных эффектов прежнего owner,
с новым назначением/grants/version/detail IDs и независимой проверкой. Timeout не handoff.

Для изменяемых Git-артефактов v3 требует `git_delivery` и policy
`start-target-linear-delivery/v1`: до работ capture canonical repository/worktree/git-dir/
common-dir, полный текущий target_ref/start_oid (либо unborn), initial index/status/baseline
и отдельный expected_tip. Стартовая цель и baseline неизменны при resume/switch; drift,
detached, чужая операция или неподтверждённый staged блокируют, не выбирают другую цель.
Local commit обязателен для owned accepted paths, approved preexisting — только по явному
разрешению с fingerprints; чужие dirty/staged/untracked не присваиваются. Чистое read-only
исследование без изменяемого Git-артефакта/non-Git/
подтверждённый no-change явно not_applicable с причиной, без пустых commits/forced dev.

File grant не даёт Git-полномочий: один последовательный Git-owner/index/ref writer по
отдельному `git-grant` после independent content pass и release writers/verifier. Policy
ack обязателен в ready/grant; нет silent v2 defaults/второго schema_version. Default —
прямой commit в start target, без ненужного rebase. Нужный разрешённый rebase переносит
только own proven unpublished task commits по explicit refs/OIDs/range. Новая история
без merge/helper/merge commits, старая не flatten. Нет auto worktree/branches/скрытого
FF-return, force-push, auto stash/reset/clean/add-all. Push отдельно разрешает пользователь.
Higher-priority branch-first/default-branch или обязательный merge-sync конфликт — blocked,
не обход правил и не молчаливая смена target. Attribution — по правилам потребителя.

Перед Git-мутацией persisted intent/expected OIDs; после crash — reconcile actual state,
не дублирование commit. Конфликт без --skip/foreign abort; timeout не освобождает owner.
Content pass — не acceptance. После commit/rebase/hooks новый delivery pin/release и
независимый final_git receipt: target/start/final OID/tree, manifest/inventory, criterion IDs,
линейность добавленной истории относительно неизменного baseline/Git tree. Drift делает
старый verdict stale; даже unchanged tree требует final Git-receipt. Только final accepted
открывает downstream. Full Git evidence читает child verifier, не parent.

Verifier required Git-результата остаётся read-only/file_only без commit/dev, но получает
captured git_delivery=required и verification_phase=content/final_git; not_applicable не
подменяет обязательную Git-доставку только из-за read-only роли проверяющего.

Delivery сериализуется по units: immutable run start/baseline сохраняются; каждый Git-grant
закрепляет pre_git_oid и exact already-accepted sibling prefix (OIDs/trees/deltas/receipts).
Current unit проверяется на pre_git_oid..final_oid, весь run range = verified prefix + unit;
неизвестные commits не разрешаются allowlist имён. Stage exact argv только с
`git --literal-pathspecs add -- <paths>`: один `--` не отключает patterns/magic.
Parent-approved phase_criteria отделяет content-required pass от заранее deferred_git_final
критериев доставки; полный final набор всё равно требует всех pass. Content pass не downstream.
Final receipt включает independently observed repository/worktree/git-dir/common-dir для
сравнения с captured identity, а не только одинаковые OID/tree в другом clone. Чистый
read-only artifact — not_applicable; read-only verifier required artifact остаётся file_only,
но проверяет required delivery и не понижает applicability из-за своей роли.

Каждое сообщение к parent вместе с envelope — **до 2000 символов**; final и wrap-up — тот же
предел каждый. Нет stdout/diff/source и обхода потоком фрагментов. Full evidence остаётся по
refs у потребителей; критические риски кратко называются с ref. Worker без memo не шлёт
полный отчёт parent: назначенный verifier с memo сам получает evidence из проверяемых
источников/прямой связи/адресного транскрипта. Нет такого пути — blocked, не verbose/file
fallback. Без parent memo/Desktop новых назначений нет; MCP настраивается пользователем.

Parent и children сначала исследуют доступные данные, conventions/defaults и альтернативы,
выбирают лучшие соразмерные решения и кратко фиксируют assumptions, не меняя цель/acceptance.
Технический blocker child сначала решает parent, не пересылает автоматически человеку.
Остановка ради человека — только необходимое физическое действие (например, ручной тест
устройства) или доказанный неразрешимый в scope/правах/инструментах blocker. Отказ access,
обязательное внешнее approval или конфликт higher-priority без разрешённой альтернативы —
policy blocker; обычный выбор или необязательная зависимость — нет. Сначала независимая
доступная работа, затем факты/попытки/состояние/unverified и один короткий пакет parent
с рекомендацией/Other о минимальном действии/решении. Peer не расширяет полномочия;
отказ не обходится ролью/tool/сменой permissions или выдуманным user_asked. Системные
permission prompts/видимость сессий сохраняются. Required Git commit — по policy/git-grant;
автоматических worktree/archive/delete/push нет; destructive/secrets/payments вне scope
не разрешаются автономией.

Окончание API-хода в ожидании child не завершает задачу: малый control сохранён, реально
поддерживаемое подлинное push-event возобновляет работу без «продолжить?». Polling/Cron/loop/
Monitor сессий запрещены; готовый план или worker report не заменяют final acceptance.
Если клиент не допускает обязательный запуск/канал, это честный blocker после проверки
разрешённых альтернатив, не обещание автопробуждения.
При resume передайте root ID: recall — не реестр, нужен малый current frontier и сверка
реальных сессий/старого parent до новых запусков. Контракты и матрица — в
[пакете orchestrate](skills/orchestrate/SKILL.md).

## Создать скил

Из корня этого репозитория:

```bash
mkdir -p skills/my-skill
```

```bash
cp templates/skill/SKILL.md.template skills/my-skill/SKILL.md
```

Замените `my-skill` на имя задачи в названии каталога и в `name`. Заполните инструкции,
удалите заметки автору и добавьте только необходимые ресурсы. Альтернативный способ начать —
официальный `npx skills init my-skill` из каталога `skills/`.

Минимальный frontmatter:

```yaml
---
name: my-skill
description: "Конкретная задача скила и ситуации, в которых агенту следует его применять."
---
```

Обязательные правила:

- `name`: 1–64 символа; для совместимости используйте `a-z`, `0-9` и `-`, без дефисов
  по краям и `--`. Имя совпадает с названием каталога и уникально в публичном каталоге.
- `description`: непустая строка до 1024 символов, содержащая назначение и триггеры применения.
  Обязательны только `name` и `description`; дополнительные поля — по спецификации.
- Инструкции описывают входы, ожидаемый результат, конкретную процедуру, примеры и обработку
  ошибок. Не заменяйте процедуру обещанием «сделать хорошо».
- Ресурсы входят в пакет. Пути разрешаются относительно корня скила, а не текущего каталога
  пользователя. Не используйте обязательные ссылки за пределы пакета или симлинки наружу.
- Публичный скил не зависит от среды авторинга: её `.claude/`, `CLAUDE.md`, настройки memo,
  соседних скилов или абсолютных путей автора. Внешние инструменты, MCP и ограничения
  клиента объявляются явно; отдельно настроенный пользователем memo допустим как явная
  зависимость конкретного пакета. Они не устанавливаются автоматически вместе со скилом.
- Не встраивайте секреты и не требуйте загрузить проектную `.env`. Побочные эффекты
  вроде публикации, удаления, перезаписи и глобальной установки требуют разрешения.

Спецификация рекомендует держать `SKILL.md` короче 500 строк и выносить подробности в
`references/`; это рекомендация, а не ограничение формата. Лицензия не выбрана автоматически:
согласуйте права на распространение перед публикацией.

## Проверки

Потребуются `sh` и [uv](https://docs.astral.sh/uv/) с `uvx`. Для установки через CLI нужны
Node.js 22.20+ и npm. Оба инструмента могут загружать пакеты в свои кэши; это не глобальная
установка команд, но записи вне репозитория будут.

Проверить все публичные скилы в плоском каталоге `skills/`:

```bash
sh scripts/check-skills.sh
```

Проверить другой каталог с пакетами, например временные фикстуры:

```bash
sh scripts/check-skills.sh /path/to/skill-catalog
```

Скрипт вызывает официальный `skills-ref validate` через `uvx --no-env-file` и фиксирует
исходник валидатора на коммите `83021e2be457a9b6679148719c1f6074f0ad975e`.
Глобальная установка Python-пакета и собственный YAML-парсер не нужны. Проверка запускается
из каталога нашего скрипта, а не из проверяемого пакета. При ошибке возвращается ненулевой
статус; пустой каталог явно сообщает `0 public skills; nothing to validate`.

`skills-ref` — демонстрационная reference library. Она проверяет метаданные, но не доказывает
безопасность, корректность ссылок, качество инструкций или поведение агента. Дополнительно
нужны установка из локального пути в отдельный тестовый проект, проверка наличия ресурсов и
сценарии выполнения: нормальный запрос, пограничный случай, отсутствие зависимости.
Установка для одного агента не подтверждает совместимость со всеми остальными.

Для v3 отдельно сверяются схемы обоих пакетов/bootstrap, локальные ссылки/автономность,
установка закреплённым `skills@1.7.6 --copy` в три временных consumer-проекта: каждый пакет
отдельно и оба вместе, без `-g`. Матрица включает независимый verdict, stale version,
защиту control/detail writer, worker без memo, бюджет всех ролей economy 2 / fast null либо N, запрет downstream после
rejected/paused, полноту parent-owned criterion IDs, независимый inventory всех изменений,
применимость dev к роли, mode/type/deletion/link-target pin и три условия малого
контекста parent: нет source/diff/stdout/повторных тестов; evidence ×10 не увеличивает чтение
parent пропорционально; resume читает current frontier, не архив.
Различайте **S** (статически), **F** (явная фикстура), **R** (реальные Desktop-сессии).
Git-fixtures в новых temporary repo проверяют start target, dirty/staged, sequential owner
model, branch drift, own rebase/no merge, conflict/publication guards, mode/type/delete/hooks
and crash reconcile; F/GitCLI не Desktop R/не исполнение скила. Живой v3 smoke lead+independent
verifier — только по отдельному разрешению; старые v1/v2 smoke,
копирование файлов и фикстуры не доказывают R или измеренную экономию. Полные результаты
проверок и manifest сохраняет child в назначенном detail, parent получает compact receipt.

Отдельная проверка контракта ревью:

```bash
sh .claude/skills/dev/scripts/review-lint.sh
```

Она требует Git-репозиторий и учитывает новые неигнорируемые файлы без коммита. Это проверка
гигиены `REVIEW.md`, а не валидатор скилов или линтер зависимостей приложения.

## Интерактивная установка через Make

Из корня этого репозитория:

```bash
make install
```

Запустится обычный диалог закреплённого `skills@1.7.6`: выберите нужный скил или несколько,
агента, проектную/глобальную область и способ установки, затем подтвердите итог.
Выбор в списке — пробел, переход дальше — Enter; отмена — Ctrl+C.
Источник — только публичный каталог `skills/`, без служебных скилов `.claude/skills/`.
Если выбрать проектную установку, проектом-потребителем будет текущий репозиторий;
для установки в другой проект используйте команды следующего раздела из его каталога.

Команда требует интерактивный терминал и не передаёт флаги автоматического выбора или
подтверждения. Маркеры `AI_AGENT`, `CLAUDECODE` и `CLAUDE_CODE` удаляются только из окружения
дочернего CLI, чтобы он не включил автоматические подтверждения из-за окружения Claude.
Без терминала команда прекращает работу до вызова CLI. Node.js/npm и Make нужны отдельно;
Makefile не содержит собственного установщика.

## Установка из локального проекта

Команды выполняются **из корня проекта-потребителя**, не из этого репозитория.
Для воспроизводимости примеры закреплены на `skills@1.7.6`.

Оба готовых пакета для Claude Code, проектная независимая копия:

```bash
DISABLE_TELEMETRY=1 npx --yes skills@1.7.6 add /Users/vladimir/Programming/Skills/skills --skill orchestrate session-worker -a claude-code --copy -y
```

Только оркестратор (bootstrap уже внутри):

```bash
DISABLE_TELEMETRY=1 npx --yes skills@1.7.6 add /Users/vladimir/Programming/Skills/skills --skill orchestrate -a claude-code --copy -y
```

Только исполнитель:

```bash
DISABLE_TELEMETRY=1 npx --yes skills@1.7.6 add /Users/vladimir/Programming/Skills/skills --skill session-worker -a claude-code --copy -y
```

Ниже — общие примеры для авторов: скил `my-skill` должен уже существовать.

Посмотреть список без установки:

```bash
DISABLE_TELEMETRY=1 npx skills@1.7.6 add /Users/vladimir/Programming/Skills/skills --list
```

Установить один скил для Claude Code:

```bash
DISABLE_TELEMETRY=1 npx skills@1.7.6 add /Users/vladimir/Programming/Skills/skills --skill my-skill -a claude-code
```

Укажите свой путь к клону вместо показанного абсолютного пути. Можно передать относительный
путь, например `../Skills/skills`, или путь прямо к `skills/my-skill`. Для другого клиента
используйте `-a codex`, `-a cursor` либо выбор агентов в интерактивном CLI.

По умолчанию установка проектная. `-g` делает её глобальной — не добавляйте его без намерения.
CLI предлагает симлинки либо копирование; `--copy` создаёт независимую копию. После правки
локального исходника не предполагается автоматическое обновление установленной копии:
повторите `skills add` и отдельно проверьте поведение своего клиента.

## Установка из GitHub

Remote ещё не настроен, репозиторий не опубликован. Следующая команда — **форма будущей
установки**, а не действующая ссылка: замените `OWNER`, `REPO` и `main` фактическими значениями.

```bash
DISABLE_TELEMETRY=1 npx skills@1.7.6 add https://github.com/OWNER/REPO/tree/main/skills --skill my-skill -a claude-code
```

Перед публикацией проверьте её из отдельного проекта-потребителя. Наличие совместимого
формата не означает автоматическое включение репозитория в каталог skills.sh.

## Среда авторинга Claude Code

Откройте новую сессию непосредственно в этом каталоге: она загрузит проектные скилы, агентов,
хуки и `.mcp.json`. MCP-сервер может потребовать отдельного подтверждения доверия.

- `/dev` — разработка скила по конкретной задаче; уровень строгости зависит от размера и риска.
- `/memo` — решения и контекст проекта `Skills`; `/memo-bootstrap` — первичная инициализация
  памяти, запускается отдельно, не выполнялась автоматически при переносе.
- `/adapt update /путь/к/исходному/набору` — обновление набора из целевого проекта; конфиги
  сохраняются, проектные дополнения сливаются. Не переписывайте общие скилы под конкретный стек.

memo использует бинарь `/Users/vladimir/.local/bin/memo` и общую БД с изоляцией по scope.
Этот путь относится только к среде авторинга и не должен попадать в распространяемые скилы.
На другой машине нужно настроить свой путь к memo. Reasoner использует локальный
CLIProxyAPI по адресу `http://127.0.0.1:8317/v1`; модель задаётся в `agentmemory.toml`.
Передайте один из ключей `api-keys` конфига CLIProxyAPI через переменную окружения
`CLIPROXY_API_KEY` или локальную `.env` (она исключена из Git). Не записывайте ключ
в TOML или README. При пустом ключе или недоступном прокси память работает без reasoner;
без доступного Ollama предусмотрен FTS5. Доступность сервисов нужно проверять отдельно.
Эта настройка относится к среде авторинга. Публичному `orchestrate` нужен свой настроенный
пользователем MCP memo с подтверждённым scope; авторские пути, CLIProxyAPI и его конфигурация
ему не требуются. `session-worker` без собственного memo требует назначенного независимого
verifier с memo и проверяемым путём получения evidence; иначе v3 блокирует submission.

## Источники

- [Agent Skills Specification](https://agentskills.io/specification)
- [Создание и обнаружение скилов](https://github.com/vercel-labs/skills/blob/main/docs/creating-skills.md)
- [Команды skills CLI](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)
- [skills-ref на закреплённом коммите](https://github.com/agentskills/agentskills/tree/83021e2be457a9b6679148719c1f6074f0ad975e/skills-ref)
