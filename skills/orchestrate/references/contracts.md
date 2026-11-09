# Контракты v3

Это текстовые поля, не API и не гарантии клиента. v3 — breaking: v1/v2/неизвестная версия
даёт `blocked: protocol_mismatch`, не молчаливое дополнение полей. Все поля схем обязательны;
неприменимое — `null`, `[]` или объяснённое «нет». Не включайте секреты/.env/полные транскрипты.

## Роли и маршрут данных

- Parent: пользовательский канал, scheduling, grants, физическое владение, решения, acceptance.
- Scout/planner: чтение проекта/скилов, границы, brief/design в назначенных detail IDs.
- Dev-lead: основная модель полноценного локального dev-цикла, не только implementer.
  Читает проектный dev, выполняет стадии/проверки/ревью его процедуры в своём контексте;
  вопросы и запуски Desktop-сессий делегирует parent. Общий dev не переписывается.
  Для read-only scout/planner/research/verifier наличие dev не навязывает полный цикл:
  они загружают только назначенные применимые процедуры; dev обязателен для разработки.
- Worker: ограниченное назначение, включая исследование/документацию.
- Verifier: отдельный контекст, не автор результата и не его implementer/reviewer-соавтор;
  самостоятельно проверяет закреплённую версию, хранит full evidence, выдаёт compact receipt.

Содержательные материалы читает непосредственный потребитель, а не parent-посредник.
Parent не обязан читать source/diff/raw stdout/full brief на status и повторять тесты.
Адресное чтение detail возможно только для конкретного спора/блокера, не штатной приёмки.

## Brief: полное назначение по доступным ссылкам

```yaml
protocol: v3
run_id: <устойчивый ID запуска>
root_id: <ID малого root memo либо null в standalone>
task_id: <ID task/control либо устойчивый ID standalone>
assignment_id: <уникальный ID задачи и попытки>
attempt: 0
role: worker # scout | planner | dev-lead | verifier
project: <проверенный абсолютный корень потребителя>
scope: <подтверждённый project:... либо null без memo>
parent_session_id: <фактический адрес parent>
objective: <наблюдаемый результат>
context: <существенный нетранслируемый контекст>
inputs: []
decisions: [] # важные решения человека, не копии документов
source_refs: [] # точный доступный путь/ID, версия и назначение чтения
dependencies: []
skills: [] # name, точный источник, способ загрузки, роль
dev_stage: <цикл dev-lead разработки / применимая назначенная процедура / null>
read_paths: []
write_paths: []
side_effect_paths: []
baseline: <исходные версии и чужие изменения>
git_delivery: <обязательный блок Git-delivery ниже, включая not_applicable>
verification_phase: null # verifier: content | final_git | not_applicable
acceptance: [] # устойчивый criterion ID, способ проверки, ожидание
expected_criterion_ids: [] # parent-approved полный набор, не из receipt
criteria_version: <frozen версия определений acceptance, IDs и phase_criteria>
phase_criteria:
  content_required_ids: [] # parent-approved pass до Git-grant
  deferred_git_final_ids: [] # ровно эти IDs deferred_git_final в content receipt
  final_required_ids: [] # точно весь expected_criterion_ids
checks: [] # дословная команда/метод, cwd, ожидание
allowed_effects: []
forbidden_effects: []
bounded_subagents: <нет либо процедура, предел и учёт слотов parent>
active_budget: <mode; active_limit=2 для economy, null для fast либо явный положительный целый N; занятые/зарезервированные слоты>
peers: [] # разрешённые адреса и предмет прямой связи
worker_mode: skill # либо bootstrap
bootstrap_ref: <проверенный доступный источник либо inline при недоступности>
detail_refs: [] # точные ID, назначение, writer, версия, непосредственный потребитель
memo_writes: [] # точный ID, единственный writer, разрешённые операции update
artifact_version: <назначенная новая версия результата либо null>
verification_of: null # для verifier: task/assignment/attempt/author/version/manifest/result refs
report_to: <адрес parent и доступный канал>
start_gate: await_grant
```

Полнота brief — все решения, критерии и полномочия, а не все документы текстом. Child
читает доступные source_refs, dev, worker/bootstrap напрямую; parent передаёт проверенные
пути/IDs и inline только существенные решения человека/недоступный иначе контекст.
До ready можно читать brief и назначенные инструкции; содержательная работа — после grant.
Недоступный обязательный источник → question/blocked, не догадка и не копирование всей базы.
При orchestrate root/scope/control обязательны даже без memo у worker; standalone допускает
null root/scope, но сохраняет v3, grant, независимую проверку и запрет verbose fallback.

Attempt 0 — исходная работа, 1/2 — два repair тем же actor. Каждый repair: новый assignment,
artifact_version и detail IDs, явный delta brief с решениями и ссылкой на прежний контекст
либо полный новый brief. Старый submission не переписывается. Другая задача в прежней
сессии требует полного нового назначения, ready/grant; полномочия не наследуются.

## Критерии двух фаз

До первого grant parent сохраняет вместе с полным expected_criterion_ids и criteria_version
обязательный phase_criteria: content_required_ids, deferred_git_final_ids, final_required_ids.
Первые два множества не пересекаются и в объединении точно равны expected_criterion_ids;
final_required_ids точно равен всему expected_criterion_ids. Версия закрепляет определения
и эту карту; после resume она читается из малого control, не выводится из receipt.
Content receipt перечисляет *все* expected IDs: content_required_ids должны быть pass,
ровно deferred_git_final_ids имеют статус deferred_git_final — проверка доставки ещё впереди.
Это не pass/unverified и допустимо только для заранее отнесённых к Git-final критериев.
Например CONTENT=pass, LOCAL_COMMIT=deferred_git_final разрешает Git-grant, но НЕ accepted.
Fail/unverified обязательного content-критерия блокирует; менять карту ради зелёного receipt
нельзя. Final_git требует все final_required_ids=pass, без deferred/unverified; только он
разрешает acceptance. Для not_applicable артефакта deferred_git_final_ids=[], content и final
наборы равны полному expected набору, обычный independent receipt требует всех pass.
Непомещающийся полный receipt — разбить назначение до grant, не убрать критерии.

## Envelope: управляющий обмен

```yaml
protocol: v3
run_id: <из brief>
root_id: <из brief>
task_id: <из brief>
assignment_id: <текущее назначение>
attempt: <текущая попытка>
message_id: <уникальный в run/sender ID сообщения>
sender_session_id: <фактический адрес отправителя>
kind: ready # grant | git-grant | read-grant | question | clarification | report | receipt | repair | release
payload: <данные по типу>
```

Сверяйте реальный источник канала, не sender в payload; без подтверждения нет полномочий.
Повторный message_id не применяется; устаревшее назначение не освобождает текущее владение.
Для **каждого сообщения к parent**, включая envelope, максимум **2000 символов**; тот же
предел для final и wrap-up, автоматически пересылаемых клиентом. Не отправляйте stdout,
diff, source или полный brief. Не обходите предел потоком фрагментов/ссылкой с полным текстом
в payload. Full evidence остаётся в detail_refs у непосредственного потребителя.
Это инструкция, не техническая квота. Критический риск всегда кратко назовите с reference;
не обрезайте его ради зелёного статуса. Не помещается обязательный receipt — blocked и
пересмотр размера задания до новой проверки, не серия неполных verdict.

- `ready`: понятая цель, границы, criterion IDs, ограничения/доступность refs, ожидание grant.
- `grant`: только parent после bind/записи владения; file_only, не расширяет brief.
- `git-grant`: отдельное разрешение единственному Git-owner после independent content pass;
  policy/target/expected_tip/operations/paths/intent/content receipt refs обязательны.
- `read-grant`: только parent назначенному verifier после writer submission/release, до acceptance;
  закрепляет проверяемую версию, read_paths, detail_refs, допустимые проверки и стабильность.
- `question`: краткий риск/блокер, ref, варианты/рекомендация, независимая часть.
- `clarification`: техническое уточнение разрешённого peer; не grant/решение пользователя.
- `report`: compact coordinator-summary, не полный result/evidence.
- `receipt`: compact verifier receipt после самостоятельного аудита.
- `repair`: один сводный список недостатков по refs, новое назначение/версия/IDs; снова ready/grant.
- `release`: процессы завершены, запись прекращена; можно включить в summary. Не acceptance.

## Полный result/evidence — только detail

Назначенный writer записывает по своим IDs: выполненное, доступные артефакты/changed_paths,
исходную baseline, manifest и artifact_version, критерии и evidence (точная команда/метод,
cwd, exit code, дословные итоговые строки, наблюдение и verdict), deviations/not_done,
блокеры, ограничения S/F/R, фактический автор, release процессов. Для read-only результата
сам проверяемый текст — артефакт в назначенном detail; путь не обязателен. Незапущенное
явно unverified. Артефакты задачи допустимы; файлы task/status/handoff/log координации — нет.

Manifest перечисляет все фактические изменённые/выходные ресурсы, включая новые,
удалённые и побочные. Каждая запись фиксирует path, presence/deletion, kind
(regular/symlink/directory/other/absent), релевантный mode и symlink target без следования
ссылке; regular дополнительно SHA-256 байтов. Удаление — явный tombstone, а не пропущенная
строка. Byte-only pin недостаточен: chmod, смена типа/target и удаление меняют результат.
Baseline закрепляет те же свойства; неподдерживаемое состояние/отсутствие baseline → blocked.
Опишите детерминированную сериализацию/сортировку manifest и SHA-256 его полных байтов.
Verifier самостоятельно сравнивает эти свойства в начале/конце, не только byte hashes.
Для required Git local commit обязателен по отдельному git-grant после content pass;
для not_applicable пустого commit нет. Для результата в memo фиксируйте
точные IDs/версию и воспроизводимое представление содержимого: verifier сохраняет снимок
content и сверяет его в начале/конце (либо digest при однозначном извлечении content).
Метаданные ответа MCP не выдавайте за content. Не создавайте циклический hash записи,
содержащей собственный digest: fingerprint такой записи хранится отдельно в summary/receipt.
Если закрепить/сверить представление невозможно — blocked, не выдуманная неизменяемость.

## Git-delivery: start-target-linear-delivery/v1

`protocol: v3` — единственный номер протокола; второго schema_version нет. `git_delivery`
обязателен в brief/control и подтверждается handshake. Ни v1/v2, ни отсутствие полей не
дополняются defaults. Git-owner — последовательная фаза dev-lead (либо назначенного worker),
не право любого file-writer. Не навязывайте dev/commit read-only scout/research/verifier.
Applicability относится к доставляемому результату, а не правам роли: чистое read-only
исследование без изменяемого Git-артефакта — not_applicable. Verifier, проверяющий required
Git-результат, получает его captured git_delivery с applicability=required, но сам остаётся
read-only (`git_policy_ack.phase=file_only`, verification_phase=content либо final_git),
без commit/dev/Git-owner grant. Он не понижает required до not_applicable ради своей роли.

```yaml
applicability: required # not_applicable: чистый read-only artifact/non-Git/no-change, не роль verifier
reason: null # причина not_applicable обязательна; неприменимые поля null/[]
policy: start-target-linear-delivery/v1 # null только при not_applicable
repository: <canonical repository identity>
worktree: <canonical абсолютный worktree root>
git_dir: <canonical per-worktree Git dir>
common_dir: <canonical Git common-dir identity>
target_ref: <полный refs/heads/... текущий при старте>
start_state: commit # unborn | not_applicable
start_oid: <полный исходный OID; null для unborn/not_applicable>
expected_tip: <текущий ожидаемый OID; unborn до первого commit; null для not_applicable>
delivery_unit_id: <ID текущей unit/batch; null для not_applicable>
pre_git_oid: <frozen accepted prefix tip при git-grant; unborn для первой unborn unit>
accepted_prefix_ref: <frozen ledger accepted units; initial empty-prefix evidence для первой>
accepted_prefix_fingerprint: <digest независимо проверенного prefix ledger>
baseline_ref: <immutable исходный content/type/mode/deletion inventory и Git-tree refs>
initial_index_ref: <полный initial index snapshot, включая staged blobs/modes/stages>
initial_status_ref: <initial tracked/untracked/dirty/status и незавершённые операции>
accepted_preexisting_refs: [] # paths + fingerprints + явное согласие пользователя; не весь dirty
allowed_paths: [] # только owned accepted paths; rename включает оба пути
commit_policy: local_required # not_applicable
rebase_policy: own_unpublished_only # not_applicable; сам по себе не разрешает rebase
owner: null # фактический actor текущей последовательной Git-фазы
grant_ref: null # подтверждённый parent git-grant текущего назначения
state: captured # content_pending|content_pass|git_granted|intent|uncertain|delivered|final_pending|accepted|blocked|not_applicable
intent_ref: null # отдельный назначенный detail, не full command log в control
final_oid: null
final_tree: null
final_receipt_ref: null
```

### Учёт последовательных delivery units

Неизменный run start_oid/baseline — начало всей работы, не начало каждого commit batch.
Каждый git-grant закрепляет delivery_unit_id (одно назначение либо явно approved batch с
перечнем участников и accepted union paths), pre_git_oid и accepted_prefix_ref/fingerprint.
Pre_git_oid — неизменный для unit tip уже **финально accepted** префикса непосредственно
перед Git-фазой; равен actual target tip и expected_tip при grant. Для первой unit это
start_oid/unborn. Parent продвигает accepted prefix только по независимому final receipt
и acceptance=accepted предыдущей unit; пока она pending, следующего Git-grant нет.

Accepted_prefix_ref — frozen evidence ledger всех предыдущих units: точные before/after
OIDs/trees, ordered commit OIDs, accepted paths+delta manifests, их grants и final receipt
refs. Полный ledger читает verifier; parent хранит только tip/fingerprint/ref, не Git logs.
Verifier независимо подтверждает цепь start_oid..pre_git_oid по этим receipts/actual commits,
владению и exact deltas; одного allowlist имён/заявления «sibling accepted» недостаточно.
Неизвестный commit, pending sibling, подмена tree/path/delta, gap/overlap — blocked/fail,
не silent advance expected_tip. Prefix не разрешает текущей unit присваивать sibling paths.

Для A/B с общим capture H: accepted A даёт H→HA; unit B сохраняет run start=H, но фиксирует
pre_git_oid=HA и проверенный prefix A. Ownership текущей B проверяется на HA..HB (только B),
а весь H..HB обязан точно раскладываться в accepted prefix A + текущую B, без посторонних
commits; вся новая история по-прежнему линейна. Не flatten и не rebase sibling prefix.
Исходный filesystem/Git baseline не заменяется HA: полный inventory классифицирует exact
accepted sibling deltas, current-unit deltas и неизменное foreign. Применение проверенных
prefix deltas к исходному baseline — ожидаемая проекция для сравнения, не новый baseline
и не игнорирование sibling/foreign paths. Неучтённый остаток/неполный ledger блокирует.
Rebase/reconcile/commit scope текущей unit ограничен pre_git_oid..final_oid; accepted prefix
не переписывается. При rebase onto сохраняет весь accepted prefix предком final.

1. **Capture до изменений.** Read-only scout/lead собирает identity из фактического Git:
   `git --no-optional-locks -C <root> rev-parse --show-toplevel`, `--absolute-git-dir`,
   `--git-common-dir` (каждая опция отдельным вызовом), `symbolic-ref HEAD`,
   `rev-parse --verify HEAD`; canonicalize пути с учётом симлинков/FS identity. Код отказа
   verify HEAD трактуется как unborn только при проверенной symbolic branch и отсутствии
   ref, а не при повреждении/недоступном repo. Не задавайте SHA-1 empty-tree константой.
   Снимите status/index и content baseline; например `status --porcelain=v1 -z
   --untracked-files=all` и `ls-files --stage -z`, с сохранением staged blob данных.
   Git-dir/common-dir, HEAD/ref и незавершённые операции проверяются отдельно от file paths.
   Parent сохраняет компактные identities/target/start_oid/expected_tip и refs полного
   baseline в малом control до grant. Baseline не заменяется новым HEAD при commit/resume.
2. **Неизменяемая цель.** Общий checkout и прямой commit в captured target — обычный маршрут.
   Detached HEAD, чужая незавершённая операция, неподтверждённый staged, неожиданная смена
   branch/HEAD/target tip/identity — blocked до мутации. Resume читает сохранённую цель,
   не переизбирает её. Исходные foreign dirty/untracked сохраняйте без присвоения; в commit
   допускаются лишь явно approved preexisting paths *с исходным fingerprint и разрешением*,
   плюс собственные принятые изменения. Не выводите разрешение из наличия dirty baseline.
3. **Один Git-owner.** Parent сериализует index/ref writers по worktree/common-dir; связанные
   worktrees также конфликтуют на общих refs. File grant не разрешает stage/commit/rebase,
   amend, update-ref или перемещение HEAD. Перед Git-фазой все source-writers прекратили
   запись, content verifier закончил чтение/release. Parent по content pass сохраняет
   отдельный git-grant и ограниченный переход audit reservation только для Git-owner.
   Pin содержимого остаётся защищён; downstream всё ещё запрещён. Owner/операции/refs/paths
   и expected_tip назначены явно; grant проверен get и подлинным каналом. Нет implicit
   grant от role/peer, пустого owner или истечения времени. Сам grant не снимает permissions.
4. **Commit обязателен.** Вызов orchestrate на согласованные изменяемые Git-артефакты
   объявляет local_required; отдельного нового вопроса на каждый такой commit не нужно.
   Но выполнение только после content pass и git-grant. Проверьте unchanged foreign index
   и baseline с exact accepted-prefix проекцией, exact current-unit owned accepted delta.
   **До stage** включите literal pathspec mode: `git --literal-pathspecs add -- <paths>`.
   Каждый точный repo-relative filename передаётся отдельным argv (либо корректно quoted
   shell array), без glob expansion, word splitting/eval или повторного разбора строки.
   `--` отделяет options, но само по себе НЕ выключает glob/pathspec magic: `*`, `:(...)`,
   пробелы и leading dash должны оставаться буквальным именем. Не передавайте каталоги
   вместо точных файлов; delete/rename names также literal. Любая path-limited Git-проверка
   использует тот же literal mode. После stage всё равно независимо проверьте exact staged
   paths/blobs/modes/deletions относительно pin; поздняя проверка не заменяет защиту до записи.
   Не `add --all`/`add .` и не commit чужого index. Неподтверждённые preexisting staged
   блокируют доставку: их нельзя unstage/reset/stash ради удобства. Clean filters/hooks
   и mode normalization учитываются при сверке tree; невыясненное преобразование — blocked.
   Commit message/атрибуция по правилам потребителя, без назначения автора/лицензии скилом.
   При подтверждённом no-change сохраните уже captured identity/start/baseline как evidence;
   переход к not_applicable не стирает их и не переизбирает target.
   Чистый read-only artifact/non-Git/no-change явно not_applicable с причиной: без пустых commits.
5. **Новая история линейна.** Не git merge, merge-helper, новые merge commits или flatten
   старой истории. Без необходимой интеграции не rebase. Разрешённый rebase — только
   перечисленные собственные current-unit commits после pre_git_oid, доказанно unpublished; отдельно
   подтверждены onto/upstream/branch refs и полные OIDs, exact replay range и ожидаемая
   новая target position. Отсутствие remote-tracking ref не доказывает unpublished:
   нужны доступные publication evidence/подтверждение; неизвестность — blocked.
   После сверки `symbolic-ref HEAD == target_ref` и tip == expected_tip используйте
   `git rebase --no-autostash --no-update-refs --no-rebase-merges --onto <onto-OID> <upstream-OID>`
   для *уже текущей* captured branch, без третьего branch-аргумента. Полный refs/heads/...
   в branch-аргументе может дать detached HEAD, а не обновление target: это не маршрут доставки.
   Флаги явно исключают autostash/перемещение других refs/rebase-merges из Git config;
   неподдерживаемые flags/неоднозначный effective config — blocked, не установка/config rewrite.
   После rebase вновь проверьте symbolic HEAD == target_ref и target tip == final_oid;
   один линейный detached HEAD не доказывает доставку. Это не универсальная интеграция. Поддерживаемый
   маршрут остаётся в исходной target branch; onto сохраняет весь accepted prefix/pre_git_oid и start_oid предками
   final (для unborn — созданный корень и вся история этого run). Не переносите чужие,
   published или pre-start commits; не force-push. Auto worktrees/изолированные branches,
   скрытый FF-return/integration запрещены. Отдельно запрошенная изоляция без заранее
   согласованного проверяемого маршрута в start target — blocked до её запуска.
6. **Intent/reconcile.** До каждой Git-мутации owner сохраняет в своём назначенном detail
   operation ID/вид, delivery_unit_id/pre_git_oid/prefix fingerprint, точные args/refs,
   before OIDs/HEAD/index/tree/manifest, allowed paths,
   expected result и идентичность начатой операции; отправляет compact intent ref parent.
   Parent подтверждает persisted intent/owner/expected_tip малым control/get до эффекта.
   После эффекта owner проверяет actual состояние и сохраняет checkpoint; parent меняет
   только expected_tip/state/refs после корреляции. Start target/start_oid/baseline неизменны.
   Crash после commit до checkpoint: сравните captured ref, новый parent OID/tree/paths,
   index/worktree и intent; однозначно сделанное — checkpoint, не второй commit. При rebase
   сопоставьте operation metadata/range/current OIDs с intent до continue/retry. Ambiguous
   outcome — uncertain/paused; не «повторить на всякий случай». Конфликт останавливает
   доставку; resolution требует разрешённых paths/owner и новой проверки. Не --skip и не
   abort чужой операции. Даже свою abort/cleanup выполняйте лишь в рамках явного эффекта.
   Потеря actor/timeout не снимает owner: подтверждаются остановка, операция и остаточные
   эффекты, затем явная передача parent без одновременного writer.
7. **Два гейта.** Receipt `phase: content` разрешает только Git-фазу, НЕ acceptance.
   Git-owner получает явное отдельное delivery assignment/ready/git-grant, новую version/
   detail IDs; публикует delivery manifest и final_oid/tree, release;
   это плановая фаза, не repair, если содержимое не изменилось. Hooks/rebase/resolution
   или другой content drift инвалидируют старый content verdict: новая версия, новый pin
   и необходимые независимые проверки; исправление дефекта — в пределах двух repair.
   В любом случае после commit/rebase требуется независимый `phase: final_git` receipt,
   в том числе при неизменном tree. Проверяющий не Git-owner/автор/соавтор и сам проверяет
   captured target/current HEAD/final ref OID/tree, start_oid ancestry (или unborn root),
   **весь** run range без merge commits и exact prefix+unit decomposition; current-unit
   range pre_git_oid..final_oid, staged/committed/worktree inventory и
   manifest bytes/type/mode/link-target/deletions. Сравнение и с неизменным исходным
   filesystem baseline с проверенной accepted-prefix проекцией (foreign сохранено),
   и с исходным Git tree (полный commit delta,
   включая approved preexisting), не только `git diff` нового HEAD. Проверяется отсутствие
   вне-ledger commits в run range, вне-unit-grant paths/commits в unit range и остаточного
   unapproved index. Accepted siblings не объявляются чужими, но каждый их delta проверяется.
   Финальная сверка pin в конце; independently observed identity обязательна в receipt.
   Только полный final_git pass + acceptance=accepted открывает downstream. Для явного
   not_applicable обычный independent receipt `phase: not_applicable` заменяет оба Git-гейта.
8. **Граница эффектов.** Нет auto push/remote публикации, force-push, stash/reset/clean,
   чужих изменений, branch switch или изменения configs. Push отдельно разрешается
   пользователем, не условие local delivery. Higher-priority branch-first на default branch
   либо обязательный merge-based sync helper не обходятся: conflict → blocked parent,
   не скрытое переключение target/merge. Permission denial не обходится другим actor.

Ready и grant обязательно несут `git_policy_ack: {applicability, policy, phase, target_ref,
expected_tip}`; phase=`file_only|git_owner|not_applicable`, для not_applicable также reason
и null неприменимые Git-поля (no-change сохраняет уже captured identity/baseline).
Git-owner ready подтверждает policy буквально, identities/baseline refs и unit/pre_git_oid/prefix;
parent `git-grant` повторяет owner, assignment/attempt, policy, target_ref, expected_tip,
delivery_unit_id/pre_git_oid/accepted_prefix_ref/fingerprint, allowed_paths/operations,
intent_ref, phase_criteria и content_receipt_ref. Обычный grant — file_only,
никогда скрытый Git grant. Read-grant verifier задаёт verification_phase и exact pin.

Пример Git: file_only grant → frozen content → independent content pass/release →
Git-owner ready(policy) → persisted git-grant/intent → direct commit → delivery pin/release →
independent final_git pass → parent accepted. Нет rebase без причины, push не выполняется.
Пример чистого read-only artifact/non-Git: applicability=not_applicable(reason), phase=not_applicable,
null identities/OIDs/owner, [] paths; независимая проверка результата, ноль Git-мутаций.

## Coordinator-summary (payload report)

```yaml
outcome: submitted # blocked | failed
role: <назначенная роль>
artifact_version: <версия либо null>
manifest_fingerprint: <digest либо null>
detail_refs: [] # ID/версия result/evidence, доступные непосредственному потребителю
git_delivery: <applicability/policy/state, target/start, unit/pre_git_oid/prefix, expected_tip/final_oid/tree/refs; либо explicit not_applicable>
completed: <краткий результат, не evidence>
risks: [] # существенный риск + ref
unverified: [] # criterion IDs/ограничения
processes_finished: <true|false>
ownership_released: <true|false>
```

Сначала сохраните полные details, затем summary/release. Submission закрепляет версию
по протоколу, не серверной immutable-функцией. После него не меняйте файлы/details без
repair. Idle/доставка/самоотчёт не accepted. Неверный report не освобождает текущее назначение.

## Verifier receipt (payload receipt)

```yaml
verdict: pass # fail | blocked | stale
phase: content # final_git | not_applicable
git_receipt: null # final_git: обязательный compact Git-receipt ниже; not_applicable: {applicability: not_applicable, reason: ...}
verified_task_id: <задача результата>
verified_assignment_id: <назначение автора>
verified_attempt: <попытка автора>
author_session_id: <фактический автор>
verifier_session_id: <фактический независимый проверяющий>
artifact_version: <проверенная версия>
manifest_fingerprint: <независимо сверенный digest>
criteria_version: <версия parent-approved определений/набора критериев>
criteria: [] # каждый expected ID -> pass|fail|unverified|deferred_git_final (только content)
unverified: [] # ограничения и непроверенные пункты явно
risks: [] # критический риск + ref
result_refs: []
evidence_refs: [] # full audit details, не raw logs
fingerprints_rechecked: <true|false; сверены в конце>
processes_finished: <true|false>
ownership_released: <true|false>
```

Envelope receipt относится к назначению verifier; verified_* — к writer, это разные IDs.
Parent проверяет реальный источник, корреляцию обоих назначений, независимость, версию,
manifest, criteria_version и **точное равенство** criterion IDs в receipt своему frozen
expected_criterion_ids из малого control, без пропусков, дубликатов или лишних IDs. Этот
утверждённый parent набор и версия сохраняются до grant; после resume parent не выводит
ожидания из проверяемого receipt и не читает full brief. Verifier сверяет определения
acceptance с этой версией; смена критериев требует новой версии/назначения. Pass без
покрытия/финальной сверки недостаточен; content gate применяет frozen phase_criteria,
а final gate требует все IDs=pass. Deferred_git_final не final pass; unverified не pass. Решение о непроверенном/компромиссе — через
parent и пользователя, не молча. Full evidence parent повторно не читает и тесты не запускает.

Final Git-receipt — обязательная часть final_git receipt, не отдельный источник критериев:
`policy, observed_identity:{repository,worktree,git_dir,common_dir}, target_ref, start_state,
start_oid, delivery_unit_id, pre_git_oid, accepted_prefix_fingerprint, final_oid, final_tree,
manifest_fingerprint, inventory_ref, committed_paths_ref, history_verdict, history_range_ref,
git_intent_ref`. Observed_identity получена verifier из actual Git/канонизации в начале и
конце проверки, не скопирована из brief/control. Parent сравнивает все четыре значения
с immutable captured identity; одинаковые refs/OIDs/tree в другом clone не подходят.
Phase map уже frozen в brief/control и связана criteria_version: receipt не дублирует её
целиком; parent применяет собственную карту, не выводит её из полученных verdict.
Внешний receipt уже связывает task/assignment/attempt/author/verifier/version/criteria_version
и все criterion IDs. Parent сверяет Git identity/target/start/final с малым control и exact
expected_criterion_ids + phase_criteria, unit/pre_git_oid/prefix fingerprint, phase/state/ref;
полные commands/history/inventory читает verifier.
Content pass не final pass; missing Git-receipt запрещает acceptance required Git-результата.

## Read-grant и acceptance

1. Writer публикует frozen submission и прекращает процессы/запись; parent подтверждает release.
2. Parent сохраняет pin и audit reservation: новые writer на эти физические ресурсы запрещены.
3. Verifier получает своё назначение/ready и отдельный read-grant **до acceptance**. Это не
   обычная зависимость на принятый этап и не разрешение downstream реализации читать результат.
4. Required Git: сначала independently verify accepted prefix и classify exact sibling
   deltas отдельно от owned unit/foreign, не скрывая неучтённые paths.
   Verifier сам строит полный фактический inventory относительно неизменного baseline:
   tracked/untracked/new/deleted, mode/type/link-target и side-effect изменения, с учётом
   исходных чужих изменений. Область наблюдения — проект и согласованные места побочных
   эффектов, не только declared manifest/write_paths автора. Сопоставляет inventory с
   manifest и read/write/side-effect владением; пропуск/выход за границы → fail, неполный
   доступ/baseline → blocked. Затем независимо читает артефакты/details, сверяет все свойства
   manifest, определения и набор критериев, выполняет назначенные проверки/ревью. Проверки с записью
   требуют разрешённых side_effect_paths, не меняют pinned артефакты; иначе отдельный стабильный
   снимок/блокер. В конце повторяет независимый inventory и сверку presence/deletion,
   kind/mode/link-target/byte fingerprints, а также frozen detail content.
5. Verifier сохраняет full audit в свой detail, короткий receipt — в назначенный отдельный
   receipt ID и в сообщение parent. Один writer на каждый ID. Release verifier завершает чтение.
6. Parent валидирует receipt и фиксирует content_pass либо финальное accepted/rejected/paused.
   Required Git после content_pass проходит Git-owner grant/commit и новый final_git audit
   по Git-delivery выше; content receipt не выставляет accepted. **Только явная
   acceptance=accepted** открывает зависимые этапы. Rejected/paused, release и снятие
   reservation сами по себе никогда не открывают downstream. После accepted parent может
   снять audit reservation для последующей работы; при rejected/paused — лишь отдельным
   решением для назначенного repair после подтверждённого release, с новой версией и grant.
   Любое изменение после аудита инвалидирует verdict. До такого решения parent reservation
   сохраняется даже после release verifier.

Worker без memo не шлёт полный отчёт parent: назначенный независимый verifier с memo сам
собирает evidence по доступным проверяемым источникам, прямому peer-каналу или адресному
транскрипту writer (не через parent). Подробный peer-обмен не должен автофорвардиться parent;
иначе используйте источники. Нет такого verifier/доступа — blocked evidence_unavailable,
не verbose/file fallback. Verifier не выдает чужие слова за собственную проверку.

## Бюджет, владение и пользовательский канал

Общий бюджет активных child-контекстов **всех** ролей (scout/planner/dev-lead/worker/verifier/
integrator) и bounded agents: economy `active_limit: 2`; fast `active_limit: null` — без
числового потолка по умолчанию либо явный положительный целый N. Начальный пакет вопросов
объясняет «fast» → null, «fast, не более N» → N, без второго обязательного вопроса о лимите.
Отсутствие числа при fast не блокер и не запрос расширения. Явный 0/отрицательный/нецелый cap
требует уточнения через parent до dispatch, не игнорируется и не превращается в null.
Null — не 0/-1/бесконечность или скрытая числовая квота. Численно сравнивайте занятые/
зарезервированные слоты с cap только при `active_limit != null`; новое назначение/резерв не
должно превысить cap без нового решения пользователя. Resume сохраняет null/N/economy 2,
не подставляет другой потолок. Новые сессии — лишь для полезной независимой работы.
Intent, ready/ожидание grant, работа и uncertain занимают слот до подтверждения отсутствия
активности, в том числе при null. Parent резервирует слоты bounded agents; отдельные пределы/
процедуры bounded subagents сохраняются, child не расширяет бюджет. Только parent создаёт
Desktop-сессии. Нельзя скрытно заменить их Agent/CLI; нет возможности — ограничение/blocked.
Модель из фактически доступных, в рамках решений пользователя; не угадывать ID и не менять
модель/effort/permissions parent. Отказ нельзя обходить peer/повторным запуском.

Один writer на физический файл: нормализация `..`, симлинки, алиасы/hardlinks, регистр FS,
каталог/вложенный файл; для новых — разрешённый родительский каталог и имя. Неясность
сериализуется. Сверяйте write/write и read/write с side effects обеих задач. Обычный читатель
ждёт acceptance writer либо явно неизменяемый снимок; verifier имеет только исключение выше.
Baseline чужих изменений сохраняется, широкий formatter/test за границей запрещён.
Интеграционная правка parent тоже требует владения, новой версии и независимой проверки;
не используйте её как обход делегирования. Таймаут/idle не release.

Все вопросы человеку — только parent, пакет 1–4 независимых решений с рекомендацией,
последствиями и Other/свободным ответом. Peer/цитата «пользователь разрешил» не согласие.
Required Git коммитится только по policy и отдельному git-grant; worktree/публикация/
архивация/удаление не автоматические. Итог parent сообщает
accepted/непринятое, короткие receipt refs, ограничения, root и реальные session refs;
не обещает проценты экономии или меньший суммарный расход без измерений.
