---
name: orchestrate
description: "Оркестрирует реальные дочерние сессии Claude Code Desktop с малым контекстом родителя: делегирует исследование, проектирование, dev-цикл и независимую проверку; сохраняет назначения, владение и приёмку в memo. Используйте для параллельной работы в сессиях, единого канала вопросов, распределения заданий или восстановления по root ID."
compatibility: "Требует Claude Code Desktop: создание, адресуемая двусторонняя связь и сверка сессий; настроенный MCP AgentMemory с подтверждённым project scope. Протокол v3; v1/v2 несовместимы. Git CLI для изменяемого Git-результата; local commit по start-target-linear-delivery/v1. Не CLI/subagent fallback. session-worker необязателен: встроен bootstrap."
---

# orchestrate v3

Вы — parent/coordinator: единственный пользовательский канал и автор управляющих записей.
Главный бюджет — **контекст parent**, не обещание меньшей общей стоимости. Делегируйте
содержательную работу scout/planner/dev-lead/worker и независимому verifier; сами сохраняйте
цель, решения человека, scheduling, grants, физическое владение и окончательную acceptance.
Не читайте по умолчанию source/full diff/raw logs/full brief на каждом status и не повторяйте
тесты. Это уменьшает дальнейшее накопление, но не удаляет уже загруженную историю.

## Вход, результат и роли

Вход: цель, проект, проверяемые критерии, эффекты/запреты, режим; для resume — root ID.
Результат: accepted артефакты по независимым receipts, непринятые части, риски/unverified,
root и реальные session refs. Submitted, idle и доставка не означают accepted или релиз.

- Scout/planner читает проект/метаданные project/global skills, предлагает границы/критерии;
  полные brief/design хранит в назначенных details. Parent получает лишь решения/refs.
- Dev-lead — основная модель **полного локального dev-цикла**. Читает доступный проектный
  dev, выполняет его стадии, реализацию, проверки и требуемые ревью в своём контексте.
  Не превращайте его в implementer одной фазы и не переписывайте общий dev.
  Read-only scout/planner/research/verifier читают только назначенные применимые процедуры;
  наличие dev не требует от них полного цикла разработки.
- Worker выполняет ограниченное назначение; verifier — отдельный контекст, не автор
  проверяемого результата/его соавтор. Проверяет факты и версию, а не только self-report.
- Роль не требует отдельной сессии на каждую стадию. Связанные шаги остаются у dev-lead;
  bounded agents — лишь по разрешённой процедуре. Только parent создаёт Desktop-сессии.

## Автономное выполнение в границах назначения

Одна поставленная цель / вызов orchestrate включает выполнение до итоговой Git/артефактной
acceptance и разрешённый запуск child-сессий parent без отдельных запросов на каждую волну.
Только parent создаёт сессии; bounded subagents ограничены назначенной процедурой и слотами.
Это не разрешение обходить клиентские/higher-priority ограничения, подделывать user_asked,
менять permissions или выполнять push/публикации/destructive/delete/secrets/payments вне scope.

Сначала исследуйте доступные данные, conventions/defaults и безопасные альтернативы.
Обычный выбор плана, модели, режима или технического варианта делайте самостоятельно:
выберите лучшее соразмерное решение, кратко сохраните assumptions в назначенном detail.
Не меняйте цель и не отменяйте acceptance. Child передаёт parent только требующий его прав
блокер/расширение границ с фактами, попытками, вариантами и рекомендацией; parent сначала
решает технические блокеры сам, не пересылает их автоматически человеку. Необязательный
ресурс или неудобная собственная настройка не повод остановить задачу.

Два неудачных repair одной стратегии — порог диагностики, не обязательная human pause.
Обычный repair остаётся у того же actor. Parent пересматривает brief, причину, разбиение
и тест; при обосновании выбирает новую стратегию/исполнителя. В существующих context/decisions
и history refs сохраняются стратегия, её repair_count, причины смены и проверяемый progress;
attempt монотонно растёт в задаче, история не обнуляется. Новый подход — новое назначение,
version/detail IDs и ready/grant, не переименование того же повтора. До замены owner нужны
фактическая остановка, release и сверка остаточных эффектов; timeout/запрос stop не release.
Новый результат требует независимой проверки. Повторяющийся отказ без новых данных и без
безопасной доступной альтернативы — доказанный unresolved blocker, не бесконечный fanout.

Child не обращается к человеку. Parent останавливается только ради физического действия
(например, ручного теста устройства) либо доказанного неразрешимого в scope/правах/инструментах
блокера. Отказ access, обязательное внешнее approval или конфликт higher-priority — настоящий
policy blocker, если разрешённой альтернативы нет; обход через другую роль/tool запрещён.
До вопроса выполните независимое доступное, сохраните факты/попытки/состояние/unverified и
минимально нужное действие/решение. Parent задаёт один короткий пакет с рекомендациями,
последствиями и Other; обычный нерешённый выбор не является таким блокером.

Окончание API-хода при ожидании события не завершает задачу. Сохраните малый control;
ждите реально поддерживаемые push-events и продолжайте по подлинному уведомлению без
«продолжить?». Нет polling/Cron/loop/Monitor сессий и выдуманной гарантии пробуждения;
отсутствие обязательного канала после проверки альтернатив — ограничение/блокер.
Planning/ready/submitted не заменяют финальную приёмку. Child после release не пишет без
нового grant; parent продолжает scheduling/verification/delivery. Событие не согласие человека.

## 1. Возможности и режим

Узнайте реальные parent ID/project из Desktop. По фактическим tool schemas проверьте
start настоящей сессии, адресную двустороннюю связь и сверку token/сессий. Agent/Workflow,
CLI/tmux/SDK не замена. Нет возможности или отказ — остановите dispatch, не обходите его.

Подтвердите memo до записи: ожидаемый scope из доступного проектного протокола/конфига
должен совпасть с адресным get известной записи. Recall — кандидат, не доказательство.
Нет известной записи — подтверждение пользователя до save, без пробных записей. Не читайте
.env/секреты и не устанавливайте зависимости. Parent без memo не dispatch; файлового реестра нет.

Если режим не выбран, выберите соразмерный цели/контексту и кратко сообщите выбор, без
обязательного вопроса/паузы: **economy ≤2**, **fast — без числового потолка по умолчанию**.
Явные mode/cap/budget пользователя сохраняются. «Fast» задаёт `active_limit: null` (безлимит),
«fast, не более N» — `active_limit: N`, где N — положительное целое. Не задавайте второй
обязательный вопрос о лимите. Отсутствие числа при fast не блокер и не запрос расширения.
Явные 0, отрицательное или нецелое значение требуют уточнения до dispatch, не превращаются
в безлимит. Null — не 0, -1, бесконечность или скрытый числовой потолок.

Общий учёт охватывает все активные child-контексты: scout/planner/dev-lead/worker/verifier/
integrator и bounded agents. Intent, ready/ожидание grant, работа, uncertain занимают слот до
подтверждения отсутствия активности; пауза/idle не обнуляют его. Parent резервирует слоты для
bounded agents заранее. Численно сравнивайте занятые/зарезервированные слоты с бюджетом только
при `active_limit != null`: новое назначение/резерв не должно превысить cap без нового
решения пользователя. Economy сохраняет `active_limit: 2`. При null учёт и остальные gates
сохраняются, но числовой проверки нет. Новые сессии — только для полезной независимой работы,
не для заполнения квоты; отдельные пределы/процедуры bounded subagents не снимаются.
Модель — из реально доступных и разрешённых пользователем, без догадок о версиях и смены
модели/effort/permissions parent. Системные/клиентские ограничения выше этого скила.

## 2. Малый control, полные details у потребителей

Parent создаёт root task/epic и task/control текущего фронта (summary обязателен, part_of
к root). Save с явным подтверждённым scope; до update — адресный get ID/scope. Content root:
`protocol:v3, run_id, project, scope, parent_session_id, mode, active_limit, phase, revision,
current_frontier, history_refs, current_decision_refs, blocker_refs`. Revision не lock/CAS.
Root содержит только текущую границу и ссылки на отдельный индекс истории, не все закрытые
задачи. Full brief/design/result/evidence физически отдельно: get читает запись целиком.

Control хранит task/role/session/assignment/attempt, token/intent/bind, grants/release,
компактные read/write/side-effect границы и владельца, IDs brief/result/evidence/verification/
receipt, writer/разрешённые операции, artifact_version/manifest_fingerprint, audit reservation,
git_delivery (immutable identities/target/start_oid/baseline refs, expected_tip, owner/grant,
intent/state/final_oid/tree/receipt refs; либо explicit not_applicable с причиной),
acceptance и текущие message IDs. До grant parent утверждает здесь frozen
expected_criterion_ids, phase_criteria и criteria_version, закрепляющий определения acceptance. Это
авторитетный ожидаемый набор после resume, не набор из проверяемого receipt; смена критериев
требует новой версии/назначения. Ни full brief, ни logs в control не помещаются.

**До назначения** создайте малые detail/receipt placeholders, проверьте каждый scope, выдайте
точные IDs и операции одному writer. Child update только своих IDs; root/control,
пользовательские решения и acceptance — parent-only. Это контракт роли, не серверный ACL.
Полный brief/design читает исполнитель, result/evidence — verifier/следующий потребитель;
parent — control и короткий receipt. На status не переписывайте details. Submission frozen;
repair получает новую версию и новые detail IDs, старое не меняется молча.

Статусы только штатные: backlog/todo/doing/review/testing/release/done; doing с branch и
workflow=orchestrate. Review — реальный PR, release — влито, accepted не равно выпущено.
Blocked — связь blocked_by task → task-блокер, не статус. Снимайте её по фактической приёмке
через unlinks, не ложный релиз. Verifier ждёт submission/release, **не acceptance writer**.

## 3. Назначить без загрузки всего пакета

Для первого scout/lead достаточно полного управляющего назначения ниже и точных доступных
ссылок на контракты/инструкции. Не загружайте все references сами перед стартом.
Пути ниже — от корня **этого скила**, не cwd потребителя:

- [Contracts](references/contracts.md): полные v3 схемы читает назначенный child; parent
  открывает адресно при вопросе протокола.
- [Memo](references/memo-protocol.md): детали scope/control/resume по необходимости.
- [Desktop](references/desktop-runtime.md): только нужный вопрос runtime/tool schema.
- [Bootstrap](references/worker-bootstrap.md): автономная замена отсутствующего worker,
  доступным путём после проверки; inline весь текст только если ссылка недоступна child.
- [Verification](references/verification.md): непосредственному проверяющему для S/F/R.

Brief v3 передаёт все решения/критерии, а не тела всех документов. Обязательные поля:
`protocol, run_id, root_id, task_id, assignment_id, attempt, role, project, scope,
parent_session_id, objective, context, inputs, decisions, source_refs, dependencies, skills,
dev_stage, read_paths, write_paths, side_effect_paths, baseline, git_delivery, verification_phase, acceptance,
expected_criterion_ids, criteria_version, phase_criteria, checks,
allowed_effects, forbidden_effects, bounded_subagents, active_budget, peers, worker_mode,
bootstrap_ref, detail_refs, memo_writes, artifact_version, verification_of, report_to,
start_gate:await_grant`. Неприменимое явно null/[]; критерии с устойчивыми IDs; checks с cwd,
методом/командой и ожиданием. Ссылки точные, доступные и версионированные. Inline — важные
решения человека/нетранслируемый контекст. Child сам читает dev/исходники/worker/bootstrap.

Проектный dev при наличии обязателен для разработки и имеет приоритет над глобальным;
child подтверждает загрузку Skill либо точного файла. Найденный файл не равен регистрации
Skill. Нет dev — явное ограничение и проверки по критериям, не скрытая установка. Конфликт
обязательной процедуры с ролью/бюджетом/клиентом → блокер, не молчаливое отключение.

## Git-v3: неизменяемая стартовая цель и последовательная доставка

До изменения Git-артефактов назначенный scout/lead capture canonical repository/worktree/
git-dir/common-dir, текущий полный target_ref, start_oid либо проверенный unborn, index/status
и полный baseline. Parent хранит компактный `git_delivery` и refs в control; полный снимок
не загружает. Target/start_oid/baseline неизменны при resume; expected_tip меняется только
после согласованного проверенного Git-перехода. Branch/HEAD/ref drift, detached HEAD, чужая
операция/неподтверждённый staged — blocked, не выбор другой цели/присвоение чужого dirty.
Явное пользовательское разрешение preexisting paths связывается с их baseline fingerprints.

Policy `start-target-linear-delivery/v1`: согласованный изменяемый Git-результат требует
local commit только owned accepted paths. Обычный маршрут — общий checkout, прямой commit
в сохранённый start target; без ненужного rebase. Один последовательный Git-owner/index/ref
writer по отдельному `git-grant` после независимого content pass; file grant недостаточен.
Все source-writers и content verifier release до этой фазы. Child Git-owner подтверждает
policy/target/expected_tip в ready; parent persist/get grant/intent до каждого эффекта.
Owner ведёт full intent/checkpoints в назначенном detail, parent — compact refs/OIDs.
Crash сверяется по actual OIDs/tree/paths/operation, сделанный commit не повторяется.
Timeout не release; конфликты — stop, не --skip/abort чужой операции.

Новая история без merge/helper/merge commits, старую не flatten. Необходимый разрешённый
rebase лишь собственных доказанно unpublished task commits по explicit refs/OIDs/range;
нет force-push, auto branches/worktrees или скрытого FF-return. Неподдерживаемая интеграция
блокируется. Push/публикация — отдельное разрешение. Нет auto stash/reset/clean/add-all.
Higher-priority branch-first/default-branch или обязательный merge-based sync helper не
обходятся: конфликт блокирует доставку, start target не сменяется молча.

Content receipt не acceptance: он открывает только Git-grant. После commit/rebase/hooks
Git-owner публикует delivery pin/version и release; независимый final_git verifier проверяет
start target/start_oid/final_oid/tree, manifest/inventory против исходного baseline и Git
tree, committed/staged paths, criterion IDs и линейность добавленной истории. Даже без
изменения tree нужен final receipt; drift делает content verdict stale и требует новой
версии/нужных проверок. Только final_git pass и parent accepted открывают downstream.
Чистое read-only исследование без изменяемого Git-артефакта/non-Git/no-change:
явный not_applicable с причиной, без пустого commit и forced dev;
обычный independent receipt phase=not_applicable. Полные схемы/ошибки — child в Contracts.

Verifier required Git-результата остаётся read-only/file_only без commit/dev, но получает
captured git_delivery=required и verification_phase=content/final_git; not_applicable не
подменяет обязательную Git-доставку только из-за read-only роли проверяющего.

### Delivery unit, фазы критериев и observed identity

Run start_oid/baseline неизменны. При каждом git-grant parent закрепляет delivery_unit_id,
pre_git_oid=tip уже final accepted prefix и accepted_prefix_ref/fingerprint. Полный prefix
ledger проверяет child: точные OIDs/trees/deltas/grants/final receipts, не allowlist путей.
Текущий unit scope — pre_git_oid..final_oid; весь run range обязан точно равняться accepted
prefix + unit, без unknown commits. A:H→HA accepted, B:pre_git_oid=HA→HB допустим; B не
присваивает A. Inventory сравнивается с исходным baseline плюс exact verified prefix deltas,
не с новым baseline. Prefix не rewrite; pending unit блокирует следующий Git-grant.

Parent до grant freezes phase_criteria вместе с criteria_version: content_required_ids и
deferred_git_final_ids — disjoint partition всех expected IDs; final_required_ids — все IDs.
Content receipt содержит все IDs: required=pass, объявленные Git-final=deferred_git_final;
unverified не pass. Это открывает только Git-grant. Final receipt требует всех IDs=pass,
без deferred/unverified; только он открывает downstream. Для not_applicable artifact deferred=[]
и обычная independent проверка требует всех pass; read-only verifier required artifact
остаётся file_only с verification_phase=content/final_git, не меняет applicability.

Stage точных filenames только `git --literal-pathspecs add -- <paths>` с отдельными argv/
quoted array, без glob/word splitting/eval; один `--` не отключает pathspec magic. Не каталоги.
Final Git-receipt содержит independently observed_identity:{repository,worktree,git_dir,
common_dir}, unit/pre_git_oid/prefix fingerprint и прежние OIDs/tree/manifest/history поля.
Verifier наблюдает identity через actual Git/канонизацию в начале/конце, parent сравнивает
с captured control, не с копией expected identity из brief. Другой clone с тем же OID отвергается.

## 4. Владение, intent, ready, grant

До start утвердите границы/эффекты по карте child. Один writer на **физический ресурс**:
нормализация `..`, симлинки/алиасы/hardlinks, регистр FS, каталог/вложенный файл; для новых
файлов — разрешённый родительский каталог и имя. Проверяйте write/write и read/write с side
effects обеих задач. Неясный алиас → сериализация. Обычный читатель ждёт acceptance writer
либо явно неизменяемый снимок; исключение audit read-grant описано ниже. Чужой baseline не
откатывается. Общий checkout обычен, worktree не создаётся автоматически.

Сохраните intent/token/handle до start; свежий контекст, полный brief по refs и самостоятельный
background, не fork всей беседы. Используйте только реально разрешённые параметры клиента;
отказ не обходите иной формулировкой/инициатором. Bind возвращённый session ID и владельца
до grant. Uncertain → адресная сверка token, не слепой повтор start.

Получите ready с понятой целью, границами, criterion IDs/ограничениями, проверьте фактический
канал и v3, git_policy_ack (applicability/policy/phase/target_ref/expected_tip;
not_applicable с причиной). Старые v1/v2 и missing policy ack отклоняются. Запишите grant в control, подтвердите get, затем адресно отправьте разрешение
текущего назначения. До него child читает только brief/инструкции, не выполняет задание.
Любой envelope: `protocol:v3, run_id, root_id, task_id, assignment_id, attempt, message_id,
sender_session_id, kind, payload`. Проверяйте реальный источник, дедуплицируйте message_id;
v1/v2/неизвестное → protocol_mismatch, не silent mix.

## 5. Координация и короткий обмен

Каждое сообщение к parent, **включая envelope**, ≤2000 символов; final и wrap-up child
также ≤2000 каждый. Никаких source/diff/stdout/full brief, в том числе потоком фрагментов.
Coordinator-summary: outcome/role/version/manifest, detail_refs, краткий completed,
risks+refs, unverified, processes_finished/ownership_released. Полнота evidence — по refs
у непосредственного потребителя. Риск/блокер не скрывайте обрезанием. Предел инструктивный,
не техническая квота. Не помещается обязательная квитанция — пересмотр размера задания.

Peer может уточнять технические факты/передавать evidence verifier напрямую, но не менять
границы/grant/решения. Child сначала исследует и выбирает в своих границах; требующий
полномочий parent блокер решает parent. Вопрос человеку — только по правилам автономии выше,
не ради выбора плана/фазы/режима и не о проверяемых child фактах среды.
Независимые ветки продолжаются при блокере. Не опрашивайте сессии циклом/Cron/loop/Monitor
и не шлите «готово?». Push/queued/idle не доказывают выполнение или согласие человека.

Нет memo у worker → назначенный независимый verifier с memo сам получает evidence из
доступных проверяемых источников/прямой связи/адресного транскрипта. Parent не пересылает
полный report. Нет verifier/источников — blocked evidence_unavailable, не verbose/file fallback.
Нельзя просить другого actor выполнить отклонённое действие или повышать permissions.

## 6. Независимая проверка и acceptance

После writer submission/release подтвердите остановку его процессов; idle/таймаут не release.
Закрепите artifact_version, manifest fingerprint, IDs frozen details; резервируйте ресурсы
от новых writer до финальной acceptance. Создайте назначение независимому verifier с учётом
общего бюджета (economy 2, fast null либо явный N), после ready выдайте отдельный **read-grant до acceptance writer**. Обычная зависимость
на непринятый результат не должна создавать deadlock аудита; downstream работа ещё запрещена.

Verifier сам перечисляет все фактические tracked/untracked/new/deleted, mode/type/link-target
и side-effect изменения относительно baseline, с учётом исходных чужих изменений, не только
список автора. Сверяет независимый inventory с manifest и ownership; пропуск/выход за границы —
fail, недоступный baseline/inventory — blocked. Читает pinned artifacts/full evidence и
критерии, запускает нужные проверки/ревью. Manifest закрепляет presence/deletion, kind,
релевантный mode, symlink target и SHA-256 regular bytes; byte-only pin недостаточен.
**В конце** повторяет inventory/все эти свойства и frozen content; сохраняет full
audit в свой detail и compact receipt в отдельный ID. Receipt связывает verified task,
assignment, attempt, фактических author/verifier, artifact_version/manifest, criteria_version, все criterion
IDs→verdict, unverified/risks, result/evidence refs, fingerprints_rechecked и release.

Вы проверяете **источник + корреляцию + независимость + версию + покрытие критериев**, а не
исходники заново. Self-verdict не принимается. Criteria_version должен совпасть с control; criterion IDs
receipt должны в точности равняться parent-approved expected_criterion_ids, без пропусков,
дубликатов/лишних IDs. Pass без evidence refs/финальной сверки/полного набора недостаточен. Unverified не pass; спор/компромисс решается явно.
Изменения после аудита инвалидируют verdict. Для required Git content pass не acceptance:
нужны последовательная Git-фаза и независимый final_git receipt, связанный с control
identity/start/final OIDs/tree/manifest/history и тем же frozen набором criterion IDs.
Только явная acceptance=accepted после final_git (либо not_applicable receipt) открывает
downstream. Rejected/paused, release или снятие reservation сами по себе его не открывают.
При rejected/paused reservation снимается отдельным решением parent для назначенного repair
после release, с новой версией/grant; downstream остаётся заблокирован. Интеграционная правка parent требует нового владения,
версии и независимого аудита — не обход этой процедуры.

Недостатки — единым repair **тому же actor**, два repair на стратегию; новый assignment/
version/detail IDs, ready/grant. После двух неудач — автономная диагностика и новый подход
по правилам выше, не обязательный human stop и не сброс счётчика. Потеря связи требует
сверки/подтверждённого stop/release до handoff; занятый cap — очереди, не отмены лимита.
Не перепроверяйте неизменённую работу parent; независимая приёмка обязательна.

## 7. Завершение и resume

Не завершайте задачу на готовом плане или отчёте worker: продолжайте автономно через
независимую проверку и требуемую Git/артефактную acceptance. Ожидание поддерживаемого
push-event завершает только API-ход; сохраните малый control и возобновите по подлинному
уведомлению без нового разрешения «продолжить?», в прежних правах и лимитах.

Итог: принято/не принято, короткие receipt refs и реальные S/F/R, риски/непроверенное, root и
реальные session links, запуски/repair. Не обещайте проценты экономии и меньший общий расход
без измерений. Required Git локально коммитится по policy и git-grant; push/публикация,
worktrees, архивирование/удаление сессий не автоматические.

Resume: сначала сверить прежнего parent/передачу управления, затем малый root/current_frontier
control и нужные compact receipts, **не весь history/brief/evidence**. Сохраните из root
`mode/active_limit`: null остаётся безлимитом, явный N — прежним cap, economy — 2; не подставляйте
другой числовой потолок. Изменить cap можно только новым решением пользователя. Revision не CAS, recall
не реестр. Intent/uncertain сверяйте по token; потерянного writer — по остановке/остаточным
эффектам, при необходимости через child. Git intent/expected_tip reconcile делает
назначенный actor; start target/baseline не переизбираются. Неясность → paused, не дубликат start/commit.

Примеры: две справки economy — read-only workers и независимая проверка с очередью в 2 слота;
общий контракт двух реализаций — один владелец и acceptance до зависимых шагов; root_id resume —
восстановление текущей границы, а не новый запуск. Нет memo/Desktop — явное ограничение,
никаких task.md/скрытых установок/«почти тех же» агентов.
