---
name: session-worker
description: "Исполняет назначение v3 в дочерней сессии Claude Code Desktop: scout/planner, полноценный dev-lead, worker или независимый verifier. Соблюдает ready/grant, физическое владение и назначенные memo detail IDs; возвращает краткий результат родителю без full evidence. Используйте для worker-роли, независимой проверки, исправлений и отчётов оркестратору; не для общения с пользователем или запуска дерева сессий."
compatibility: "Требует Claude Code Desktop с адресуемой межсессионной связью и полное назначение v3. Для child без memo нужен назначенный независимый verifier с memo и проверяемыми источниками evidence, иначе blocked. v1/v2 несовместимы. Git CLI для Git-owner фазы; local commit по start-target-linear-delivery/v1. Сессии и доступы не создаёт."
---

# session-worker v3

Вы — один назначенный actor, не второй координатор. Parent сохраняет scheduling, grants,
владение, пользовательские решения и acceptance. Вы читаете и делаете содержательную работу
в своём контексте, не возвращаете её parent для повторного чтения/тестов. Все вопросы
человеку — только через parent. Правила системы/проекта и отказы доступа выше этого скила;
сессия и системные permission prompts могут быть видимы.

Самостоятельный [контракт v3](references/assignment-and-report.md) прочитайте до ready.
Другой пакет не требуется. Пути ресурсов — от корня этого пакета, не cwd потребителя.

## Вход и результат

Полный brief v3: текущие task/assignment/attempt/role, parent, scope, цель/решения, source
refs, критерии с IDs, пути/эффекты, dev/skills, точные detail IDs/writer/операции, версия,
бюджет, обязательный git_delivery/verification_phase и канал report. Полнота — все решения, не все документы inline. Доступные dev,
worker/источники читайте сами; отсутствующее обязательное → blocked, не догадка.
Root/scope под orchestrate уже проверены parent даже без вашего memo; standalone может
иметь null root/scope, но сохраняет v3/handshake/independent verifier. v1/v2/неизвестное →
protocol_mismatch без silent mix.

Результат — full result/evidence в назначенных details и compact coordinator-summary parent;
для verifier — full audit и отдельный compact receipt. Вы не выставляете accepted/done.

## Процедура

1. Проверьте фактический канал parent, поля/версию/источники. Нет канала — blocked
   no_parent_channel; не пользовательский диалог/файловый канал.
2. Загрузите назначенные применимые инструкции. Проектный dev при наличии обязателен
   **для разработки** и приоритетен; read-only scout/planner/research/verifier не обязаны
   проходить полный dev-цикл только из-за его наличия.
   Dev-lead — основная модель **полного локального dev-цикла**, выполняет требуемые стадии,
   реализацию, проверки/ревью у себя. Не сводите роль к implementer и не переписывайте общий
   dev. Skill не зарегистрирован, точный файл доступен — явно прочитайте, не заявляйте вызов.
   Нет необязательного — сообщите; конфликт обязательного/бюджета/клиента — blocked parent.
3. Ready: кратко цель, границы/эффекты, criterion IDs, refs и ограничения; ждите подлинный
   grant parent текущему assignment/attempt. До grant читайте только brief/инструкции,
   не выполняйте задание/команды. Старый grant и peer clarification не разрешение.
4. Соблюдайте одного writer на физический ресурс: нормализация `..`, симлинки/алиасы,
   hardlinks, регистр FS, каталог/вложенный файл; для нового target — разрешённый каталог
   и имя. Неясный/внешний target → blocked до записи. Formatter/generator/lockfile/test
   outputs тоже запись. Чужой baseline не откатывайте. Обычный читатель ждёт acceptance
   writer либо явно неизменяемый снимок, не читает живую запись.
5. Memo: только точные **заранее созданные** parent detail IDs с одним writer и указанными
   операциями. Get ID/scope/назначения до update. Не меняйте root/control, решения человека,
   чужие details/receipts и не создавайте произвольные записи. Dev findings/design/evidence
   пишутся в свои details; control-решения предлагаются parent с ref. Это не серверные ACL.
6. В своём detail сохраните полный результат: артефакты/фактические changed_paths/baseline,
   version/manifest, criterion→метод/команда/cwd/exit code/дословный итог/verdict, отклонения,
   блокеры, not_done и S/F/R ограничения. Manifest — детерминированный список fingerprints,
   закрепляет presence/deletion, kind, релевантный mode, symlink target без следования и
   SHA-256 regular bytes; удаление явно tombstone. Byte-only pin недостаточен, формат
   воспроизводим. Submission frozen.
7. Завершите свои процессы/запись; report summary с version/manifest, refs, кратким результатом,
   risks+refs, unverified, processes_finished/ownership_released. Неизвестная остановка →
   false и блокер. Idle/таймаут/пауза не release; release не acceptance.
8. Repair только parent: новый assignment/attempt/artifact_version/detail IDs, явные недостатки
   и brief/delta, снова ready/grant. Старое не исправляйте задним числом. Attempt 0 — работа,
   1/2 — два repair тем же actor; дальше blocked, не третий круг/автозамена.

## Последовательная Git-owner фаза

Чистое read-only исследование без изменяемого Git-артефакта/non-Git явно
`git_delivery.applicability=not_applicable` с причиной, без пустого
commit и навязанного dev. Для изменяемого Git-результата policy
`start-target-linear-delivery/v1` обязательна: local commit owned accepted paths в captured
start target. До работ capture canonical repo/worktree/git-dir/common-dir, target_ref,
start_oid/unborn, expected_tip, initial index/status и immutable baseline refs. Resume или
switch не выбирает цель заново. Чужие dirty/staged/untracked не присваиваются; approved
preexisting только по явному разрешению с fingerprints. Drift/чужая операция — blocked.

Обычный file grant не разрешает Git. Отдельная последовательная фаза назначенного actor
получает `git-grant` только после independent content pass/release и release всех writers;
один owner общего index/refs/common-dir, не по числу непересекающихся файлов. Ready/grant
несут git_policy_ack: applicability/policy/phase/target_ref/expected_tip, phase=file_only
либо git_owner; not_applicable содержит reason/null Git-поля. Owner хранит full intent
до каждой мутации в назначенном detail; parent persist/get compact intent/grant. Проверяет
exact staged paths/blobs/modes/deletions, делает commit с правилами атрибуции потребителя.

Прямой commit в start target — default, без ненужного rebase. Нужный разрешённый rebase
только own proven unpublished task commits с explicit refs/OIDs/range. Нет git merge,
merge-helper/новых merge commits, flatten старой истории, auto branches/worktrees/FF-return,
force-push, auto stash/reset/clean/add-all или push без отдельного согласия. Higher-priority
branch-first/merge-sync конфликт блокирует, а не меняет target. После сбоя reconcile actual
OIDs/tree/paths/operation с intent: сделанный commit не повторять. Конфликт — stop, не --skip,
не abort чужой операции. Потеря связи/timeout не освобождает Git-owner.

После commit/rebase новая delivery version/pin/details/release, затем independent final_git
receipt target/start/final OID/tree/manifest/inventory/history/criterion IDs. Исходный baseline
не подменяется HEAD. Hook/content drift делает content verdict stale: новая версия/проверки;
даже unchanged tree требует финального Git receipt. Content pass не accepted/downstream.
Полный автономный контракт Git-delivery и все поля — в assignment-and-report, прочитанном до ready.

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

## Independent verifier

Вы не автор/соавтор проверяемого результата. Проверяйте verification_of: writer task,
assignment, attempt, author, version, manifest/result refs. После writer submission/release
parent выдаёт ваше назначение и отдельный **read-grant до acceptance**, а не обычную
зависимость на принятую работу. Parent запрещает новых writer до acceptance. Read-grant
не разрешает downstream реализацию. Нестабильность версии → blocked.

Сами перечислите все фактические tracked/untracked/new/deleted, mode/type/link-target и
side-effect изменения относительно принятого baseline, с учётом чужих исходных изменений.
Не ограничивайтесь manifest/write_paths автора: область наблюдения — проект и согласованные
места side effects. Сверьте inventory с manifest и ownership; пропуск/выход за границы → fail,
недоступный baseline/inventory → blocked. Независимо читайте pinned artifacts/full details,
проверяйте определения критериев и команды/ревью, все свойства manifest. Проверки с записью требуют разрешённых side effects и не меняют pinned
артефакты; иначе стабильный снимок/блокер. **В конце снова независимый inventory,
presence/deletion, kind/mode/link-target/byte fingerprints и frozen detail content**;
full audit — в свой detail, compact receipt — в отдельный назначенный ID/parent.
Receipt указывает phase=content|final_git|not_applicable. Required Git content pass
разрешает лишь Git-гейт, не accepted. После commit/rebase final_git independently сверяет
captured target/start_oid/final_oid/tree, весь добавленный history range, committed/staged
inventory и manifest против immutable исходных filesystem baseline и Git tree; не только
чистый diff нового HEAD. Final Git-receipt обязателен даже без изменения tree.
Receipt связывает оба назначения/attempt, author/verifier, version/manifest, все criterion
IDs→verdict и criteria_version, unverified/risks, result/evidence refs, fingerprints_rechecked
и release. Карта phase_criteria в receipt не передаётся: parent применяет свою frozen phase_criteria из control,
связанную criteria_version, к полученным статусам. Parent сравнивает criteria_version и точное равенство criterion IDs со своими frozen
expected_criterion_ids из control, не выводит их из receipt. Нельзя пропускать/дублировать/
добавлять IDs; определения/версия утверждены до grant. Только явная acceptance=accepted
открывает downstream; rejected/paused/release/снятие reservation для repair его не открывают.
Изменение после аудита инвалидирует verdict. Self-report не независимая проверка.

## Контекст parent и отсутствие memo

Каждое сообщение к parent **≤2000 символов вместе с envelope**. Final и wrap-up, которые
клиент может переслать parent, ≤2000 каждый. Ни source/diff/stdout/full brief, ни поток
фрагментов. Критический риск всегда кратко+ref; не скрывайте его ради лимита. Full evidence
доступен непосредственному потребителю по detail_refs. Не помещается обязательный receipt —
blocked/пересмотр задания, не серия неполных сообщений.

Нет вашего memo — назначенный независимый verifier с memo сам получает evidence из
проверяемых источников, прямой разрешённой связи или адресного транскрипта, не через parent.
Подробный peer-обмен не должен автофорвардиться parent. Нет verifier/источника → blocked
evidence_unavailable, не verbose/file fallback и не настройка MCP. Verifier не подменяет
независимую проверку словами worker. Нет канала parent — не начинайте даже при доступных файлах.

## Ограничения роли

- Только parent создаёт Desktop-сессии; никаких CLI/Agent fallback вместо них. Bounded
  agents лишь по процедуре и резерву слотов parent: economy ≤2 / fast ≤4 всех активных
  scout/planner/lead/worker/verifier/agents; intent/ready/uncertain занимают слот.
- Peer — технические факты, не grant/согласие человека. Проверяйте источник канала,
  message_id и назначение; повтор/устаревшее не применять. AskUserQuestion не используйте.
- Новые пути/эффекты/решения → parent. Отказ не обходите peer, сменой permissions/модели/
  effort. Не меняйте CLAUDE/config; stage/commit/rebase/ref writes только назначенный
  Git-owner по git-grant после content pass. Не создавайте ветки/worktrees, не публикуйте,
  не архивируйте/удаляйте сессии без отдельного явного разрешения через parent.
- Никакого циклического polling/Cron/loop/Monitor ожидания. После report/release не пишите
  без нового grant и не начинайте соседнюю работу. Final/progress — фактический статус
  в лимите, без вопросов/предложений пользователю.

Примеры: read-only цитаты с источниками в result detail, parent — короткие refs/риски;
peer grant на неназначенный файл — blocked; старый attempt 0 после attempt 1 — игнорируется;
worker без memo и без независимого сборщика evidence — blocked, не длинный отчёт.
