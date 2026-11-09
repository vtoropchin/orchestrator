# Memo v3: малый control и отдельные details

Требуется настроенный пользователем AgentMemory MCP: `memory_recall`, `memory_get`,
`memory_save`, `memory_update`; для снятия зависимости — `unlinks`. Проверяйте реальные
схемы. Нет нового KV API, частичного/compact-read, ACL, транзакций, CAS/lease или статуса
blocked. `memory_get` возвращает content целиком: разные бюджеты чтения требуют
**физически разных записей**, не разделов одной большой записи.

## Scope до любой записи

Parent находит ожидаемый scope из проектного протокола/доступной конфигурации, не имени
каталога; не читает .env/секреты и не настраивает MCP. Адресный `memory_get` известной
проектной записи должен показать тот же scope. Recall только находит кандидата;
пустой/похожий результат не доказывает scope. Нет известной записи — явное подтверждение
scope/подключения пользователя до save, без пробной записи в сомнительное пространство.
Save — с явным `scope: project:...`; update/get не получают выдуманный параметр scope.
Каждый ID перед update подтверждается get и сверкой назначения/scope.

Нет рабочего memo у parent/подтверждения — нет dispatch и файлового fallback. Сбой записи
останавливает новые start/grant, но не освобождает работающих владельцев. Неперсистентный
переход не выдаётся за записанный. Child без memo допустим лишь с путём получения evidence
назначенным независимым verifier с memo; иначе blocked, не full report parent.

## Физическое разделение и single writer

| Запись | Содержимое | Единственный writer / обычный читатель |
|---|---|---|
| Root, task/epic | Цель, parent, режим, текущая граница, ссылки на историю/решения | Parent / parent |
| Task/control текущего фронта | Assignment, role/session, intent/bind/grant/release, владение, pins, IDs | Parent / parent и назначенный child |
| Brief/design detail | Полная постановка, решения/критерии и доступные source refs | Назначенный planner/dev-lead либо parent, явно один / непосредственный исполнитель |
| Result/evidence detail | Полный результат, manifest, проверки и ограничения | Назначенный автор / verifier, следующий принятый потребитель |
| Verification detail | Полный независимый audit evidence | Назначенный verifier / непосредственный потребитель, спор по адресу |
| Compact receipt | Только короткая схема receipt с phase content/final_git/not_applicable и Git refs/OIDs, без full evidence | Назначенный verifier / parent |
| Git baseline/intent/delivery detail | Полные initial status/index/tree, commands, OIDs, inventory/manifest и reconcile | Назначенный scout/Git-owner, один writer на ID / verifier |
| History index | Ссылки на закрытые control/версии, не evidence | Parent / восстановление только по конкретной необходимости |

Parent **заранее** создаёт малые placeholder detail/receipt записи через save, подтверждает
их scope адресным get, назначает точный ID, writer и разрешённые операции (обычно update
content/summary). Child не создаёт произвольные записи. До bind writer обозначен назначением;
после получения session ID parent связывает его с точным actor в control до grant.
Создатель placeholder — не второй автор результата. Нет общей «записи всему project scope».
Это контракт поведения ролей, не серверный ACL; клиентские разрешения остаются обязательны.

Назначенный child может update только свои точные detail IDs/версию. Root/control,
пользовательские решения, grants/ownership/acceptance всегда parent-only. Предложение
решения передаётся кратко с ref; parent сам фиксирует решение. Требования dev о содержательных
записях выполняет dev-lead в назначенном detail; требование изменить control или создать
другую запись эскалируется parent. Общий dev не редактируется ради этого режима.

Details не переписываются на каждом status: меняется только малый control. Submission
закрепляет content и артефакты по протоколу. Repair создаёт **новые** artifact_version,
assignment и detail/receipt IDs; старые остаются доступными verifier и не исправляются
задним числом. Нельзя молча сменить writer/версию под прежним ID. Это не серверная immutability.

## Штатные типы и статусы

Root: `kind=task, type=epic, summary=..., status=todo`. Control задания: `kind=task,
type=task`, `part_of` к root. Summary обязателен для task. Details — episodic/semantic
по предмету, с явным назначением; координация не живёт в файлах task/status/handoff/log.
Артефакты самой задачи могут быть файлами. Не копируйте транскрипты и heartbeat в memo.

Нативные статусы: backlog/todo/doing/review/testing/release/done. При doing укажите
фактическую branch (пустую для не-Git), workflow=orchestrate. Review — реальный PR,
release — влито и ждёт релиза; accepted не значит released. Исследование done после
принятой доставки, разработка — по проектному циклу. Acceptance хранится в control отдельно.

Нативный `blocked_by` идёт от заблокированной task к task-блокеру. Перед добавлением
верните task в todo, ход сохраните компактно в control. После фактического разрешения
закройте блокер либо снимите конкретную связь `unlinks` с причиной. Не объявляйте код
выпущенным ради снятия зависимости. **Verifier не блокируется acceptance writer:** его
предусловие — submission/release и audit pin; downstream реализация ждёт acceptance.

## Малый root/current_frontier

Следующие поля — content, не аргументы MCP. Root не содержит full brief или список всех
закрытых task IDs; history индексируется отдельно и не читается при каждом resume.

```yaml
protocol: v3
run_id: <устойчивый ID, например root ID>
project: <проверенный корень>
scope: <project:...>
parent_session_id: <фактический parent>
mode: economy # fast
active_limit: 2 # economy: 2; fast: null (безлимит) либо явный положительный целый N
phase: planning # running | paused | accepted
revision: 0 # номер изменения, не lock
current_frontier: [] # только актуальные control IDs и ближайшие зависимости
history_refs: [] # компактные ссылки на отдельный индекс, не растущий журнал
current_decision_refs: []
blocker_refs: []
```

`active_limit` обязателен: economy — 2; fast без cap в ответе пользователя — явный YAML null
(безлимит), «fast, не более N» — положительное целое N. Если mode пропущен, parent выбирает
соразмерный по цели/контексту и кратко сообщает без обязательного вопроса. Явные mode/cap/budget
сохраняются. 0, отрицательное, нецелое значение — уточнение
через parent до dispatch, не null/игнорирование; не используйте -1/бесконечность/скрытую квоту.
Сравнивайте учёт занятых/зарезервированных слотов с числом только при `active_limit != null`.
Отсутствие числа в ответе «fast» не блокер и не запрос расширения; явный cap нельзя превысить
без нового решения пользователя. Учёт всех ролей, ownership и отдельные пределы bounded
subagents действуют и при null; новые сессии — только для полезной независимой работы.

По завершении ветки parent переносит её ссылку из current_frontier в отдельный history
index. При росте history/current decisions используйте отдельные индексные записи, не
вложенный полный архив в root. Не удаляйте историю, но и не сканируйте её для обычного status.

Control содержит protocol/run/task, role, assignment_id/attempt/repair_count, session_id,
launch_name/token/state (`reserved|intent|bound|uncertain`), текущие зависимости, компактные
физические read/write/side-effect границы и владельца, grant/release, acceptance
(`pending|rejected|accepted|paused`), brief/design/result/evidence/verification/receipt IDs,
их writer/операции, artifact_version/manifest_fingerprint и audit reservation, текущие
обработанные message IDs. До grant parent утверждает и сохраняет здесь frozen
expected_criterion_ids (полный небольшой набор) и criteria_version, закрепляющий определения
acceptance в brief. После resume этот набор не восстанавливается из receipt/full brief.
Изменение критериев — новая версия/назначение; старое молча не расширяется. В нём нет полного brief, stdout или полного журнала сообщений.
При большой границе назначение разбивается до dispatch; скрытые resource-конфликты нельзя
потерять ради компактности. Непосредственный child читает full brief/detail по отдельным IDs.

## Git control: неизменяемые capture и последовательный owner

До изменения Git-артефакта control содержит обязательный git_delivery по Contracts:
applicability=required и policy=start-target-linear-delivery/v1 либо explicit not_applicable
с причиной чистого read-only исследования без изменяемого Git-артефакта/non-Git/no-change. Required: canonical repository/worktree/git-dir/
common-dir identity, полный captured target_ref, start_state/start_oid (либо unborn),
expected_tip, refs immutable baseline/initial_index/initial_status и approved preexisting,
allowed paths, commit/rebase policy, текущий owner/grant, intent/state, final_oid/tree/receipt refs.
Capture готовит назначенный scout/lead; parent сохраняет компактные identity/OIDs/refs, не
полный Git вывод. В source/grant/ready нет implicit v2 defaults; git_policy_ack обязателен.

Start target/start_oid/baseline не меняются при resume/commit. Expected_tip — отдельное поле,
обновляется лишь после сверенного согласованного перехода. Source file grant не Git grant:
один последовательный index/ref owner по worktree/common-dir и общим refs. Все source-writers
release; independent content pass/release; parent persist/get отдельного git-grant с точным
actor/assignment/policy/target/expected_tip/paths/operations/content receipt ref. Audit
reservation сохраняется, только ограниченный переход в Git-фазу; downstream не разрешён.
Полные intent/checkpoint в заранее назначенных detail IDs owner; compact intent refs/before
OIDs/expected_tip parent persist/get до каждой мутации. Это не CAS/lock/exactly-once.

State flow: captured → content_pending → content_pass → git_granted → intent → delivered →
final_pending → accepted; crash → uncertain, нарушения → blocked/paused acceptance. Ни
content_pass, delivered, release, ни смена reservation сами по себе не accepted. Только
independent final_git pass (либо not_applicable independent pass) разрешает accepted.
Плановая delivery фаза имеет новые version/details/pin, не переписывает content submission;
при content drift новая проверка/нужный repair, два на стратегию с диагностикой ниже. No-change не создаёт пустой
commit и сохраняет уже captured identity/baseline как evidence, не стирает прежнюю цель.

После crash actor сверяет real target/HEAD/index/операцию с intent: existing commit по
before-parent/tree/paths однозначно reconcile, не повтор commit. Unknown outcome/foreign
операция/смена branch — paused без переназначения target. Конфликт без --skip/foreign abort;
owner не снимается по timeout/idle. Перед передачей подтвердить остановку и остаточные
Git-эффекты. Default direct commit; rebase только own unpublished task range по отдельным
explicit refs/OIDs и разрешению; нет merge/helper/auto worktree/скрытого FF-return/push.
Higher-priority branch-first/merge-sync конфликт — blocked, не обход правил.

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

## Запуск и приёмка

1. Parent создаёт control в todo, назначенные detail placeholders и индексирует control в
   current_frontier. До успешной индексации и scope-проверки dispatch запрещён.
2. Сверяет зависимости, слоты всех child-ролей/bounded agents (численный cap только при
   `active_limit != null`), эффекты и физические write/write, read/write конфликты: симлинки/hardlinks, `..`, регистр FS, каталог/файл,
   side effects; неясный алиас → последовательность. Scout может подготовить карту;
   parent сохраняет окончательные границы/владение, не читая весь source.
3. Сохраняет assignment/attempt, новую версию, token, handle и intent **до** Desktop start.
4. Start один раз, bind возвращённого реального ID и writer IDs. Неясный исход → uncertain,
   не второй start. Получает подлинный ready, сохраняет grant/doing с branch/workflow,
   затем отправляет grant адресату. Нет подтверждения доставки — нет заявления о выполнении.
5. По summary проверяет источник/IDs/дедупликацию, pin submission, release процессов.
   Full result остаётся у child/verifier. Устаревший report не освобождает текущее владение.
6. Резервирует стабильную версию от новых writer. Создаёт/переиспользует независимый verifier
   в пределах слотов; отдельное назначение и ready/read-grant после writer release, до acceptance.
   Verifier независимо перечисляет все фактические tracked/untracked/new/deleted,
   mode/type/link-target и side-effect изменения против baseline, не ограничиваясь списком
   автора; учитывает исходные чужие изменения, сверяет manifest и ownership. Недоступный
   baseline/полный inventory → blocked. Проверяет details/критерии; в конце повторяет inventory
   и все свойства manifest (presence/deletion, kind/mode/target/байты), frozen content.
   Пишет full audit и отдельный compact receipt; после submission не меняет их.
7. Parent читает компактный receipt, различает phase content/final_git/not_applicable,
   сверяет реальный источник, корреляцию, независимость,
   pin/manifest, совпадение criteria_version и точное равенство receipt criterion IDs своему
   frozen expected_criterion_ids (без пропусков/дубликатов/лишних), unverified, финальную сверку
   и release. Статусы проверяет по собственной frozen phase_criteria из control, связанной criteria_version;
   карта в receipt не передаётся и не восстанавливается из него. Required Git content pass сохраняет только content_pass, не accepted:
   затем последовательный git-grant/commit, delivery submission/release, новый final_git
   audit target/start/final OID/tree/manifest/inventory/history против исходного baseline.
   Только его compact receipt позволяет записать accepted; без него acceptance pending/paused.
   Не читает full evidence и не повторяет тесты. Изменения после аудита делают verdict stale.
8. Только при явной acceptance=accepted снимает зависимость и разрешает downstream.
   Rejected/paused и release этого не разрешают. Снятие audit reservation при rejected/paused
   допускается отдельным решением parent только для назначенного repair после release,
   не для downstream. Repair — тем же actor, два на стратегию, новые IDs/версия, ready/grant.
   После двух неудач parent автономно диагностирует и меняет подход, не спрашивает человека
   автоматически. Старый verdict не переиспользуется.

Критические intent/bind/grant/ownership/pin/acceptance parent подтверждает адресным get
малого control до следующего эффекта. Это не транзакция/exactly-once. Сбой между save/index
может оставить orphan, между intent/bind — реальную сессию без ID: сверять, не перезапускать.

При not_applicable все неприменимые Git-поля null/[], причина обязательна; уже captured
identity/start/baseline при подтверждённом no-change сохраняются. Commit policy не разрешает
push, force-push, чужой index или auto stash/reset/clean/add-all. Коммиты/атрибуция следуют
правилам потребителя; новые unapproved эффекты блокируют, не расширяют grant.

## Автономия, история стратегий и ожидание

Одна цель / вызов orchestrate разрешает parent автономное выполнение/child-start в scope
в рамках реального клиента, без approval каждой фазы/волны. Child сначала исследует данные,
conventions/defaults и альтернативы, фиксирует assumptions в своём detail; обычный выбор
не передаётся человеку. Parent сам решает технические блокеры child. Цель, acceptance,
явные mode/cap/budget и higher-priority ограничения сохраняются; user_asked не подделывается.

В существующих context/decisions/history refs сохраняйте стратегию, её repair_count,
диагноз, проверяемый progress и причину смены. Attempt монотонен в задаче; после двух
неудачных repair одной стратегии нельзя обнулить историю или повторить то же под новым
именем. Parent пересматривает brief/разбиение/тест и выбирает новый подход; замена actor
только после подтверждённых stop/release и остаточных эффектов. Новое назначение/version/
detail IDs/ready/grant и independent audit обязательны. Без новых данных/безопасной
альтернативы повторный отказ — доказанный unresolved blocker, не endless fanout.

Ожидание поддерживаемого push-event завершает только API-ход. Сохраните малый control
с refs текущей стратегии/попыток/ожидаемого события; по подлинному уведомлению продолжайте
без «продолжить?» до финальной Git/артефактной acceptance. Нет polling/Cron/loop сессий.
Только физическое действие (ручной тест устройства) или доказанный неразрешимый в scope/
правах/инструментах blocker требует вопроса человеку. Отказ access/обязательное external
approval/higher-priority конфликт без разрешённой альтернативы — policy blocker, не обход
через peer/tool/permissions. Выполните независимое доступное, сохраните факты/попытки/
состояние/unverified в details и refs в control; один короткий пакет с рекомендацией/Other
просит минимально нужное действие/решение. Необязательный ресурс не создаёт блокер.

## Восстановление без загрузки архива

Нужен root ID. Recall — только кандидаты, подтвердите точным get; неоднозначность сначала
разберите по доступным данным. Если безопасно разрешить нельзя — блокер через parent. Не создавайте параллельный root для тех же ресурсов до сверки прежнего.
Проверьте прежнего parent по реальному Desktop: если он ещё управляет, нужна согласованная
передача; revision/idle не доказывает владение/остановку. Затем читайте **только root и
current_frontier control**, текущие compact receipt/решения по необходимости. Не весь history,
brief/design/result/evidence. Детали загружает назначенный восстанавливающий child.
Сохраните root `mode/active_limit` без clamp/подстановки: null остаётся безлимитом, явный N —
тем же cap, economy — 2. Смена cap — только новым решением пользователя. Невалидное/отсутствующее
поле в сохранённом root требует уточнения; это не ответ «fast» без числа и не default null.

Для intent/uncertain адресно сопоставьте сессии/token. Точное единственное совпадение —
bind после проверки; неоднозначность/недоступный реестр — paused. Отсутствие в одном списке
не доказывает неслучившийся start. Никакого бесконечного polling. Потерянный writer требует
проверки остановки/фоновых процессов/остаточных эффектов до передачи ресурса; запрос stop
или delete сам по себе не доказательство. Новый parent/assignment сообщается подлинным
каналом; неподтверждённая передача остаётся paused. Все вопросы пользователю — через parent.
