# Адаптация v3 к Claude Code Desktop

Названия ниже соответствуют Desktop-инструментам, а не универсальному стандарту Agent
Skills. Перед вызовом читайте их фактические схемы и ограничения. Если требуемых
возможностей нет, остановите оркестрацию; не имитируйте вызов текстом.

## Требуемые возможности

| Действие | Обычно доступный инструмент | Что проверить |
|---|---|---|
| Узнать собственный ID/проект | `mcp__ccd_session_mgmt__get_session` с self | originCwd/cwd, реальный local_... ID |
| Создать настоящую дочернюю сессию | `mcp__ccd_session__start_session` | допустимый initiation, fresh prompt/background, общий checkout |
| Адресовать сообщение | `SendMessage` либо `mcp__ccd_session_mgmt__send_message` | адрес local_... и факт доставки/очереди, не только имя в тексте |
| Сверить созданные сессии | `mcp__ccd_session_mgmt__list_sessions` с linked:true | фактические ID/состояния, не произвольные чужие сессии |
| Разобрать сомнительный запуск | get_session / list_events доступной сессии | token, задача, источник и актуальное назначение |

Нужны запуск, адресуемая двусторонняя связь и возможность сверки. Наличие только Agent
или Workflow не удовлетворяет контракту реальных сессий. Не стартуйте CLI/tmux/SDK,
новый MCP или скрытый заменитель. Ограничения системы и пользователя выше этого скила.

## Запуск

Вызов пользователем orchestrate с явной задачей для дочерних сессий разрешает запуски
только в согласованных границах; он не расширяет permissions и не разрешает публикацию.
Если клиент требует более явного запроса или отказывает запуску части одной задачи,
сообщите ограничение пользователю. Не меняйте формулировку/инициатор ради обхода отказа.

Для поддерживаемого клиентом запуска используйте:

- `context: fresh` — новый контекст вместо всей беседы родителя;
- `prompt` — полное назначение v3: решения/критерии/полномочия, доступные точные refs
  brief/design/dev/worker/bootstrap и launch token. Не копия всех документов;
  inline только важные решения человека/нетранслируемый контекст. Parent проверяет доступность
  источников, child читает их напрямую; bootstrap inline целиком лишь при недоступности пути;
- `background` — самостоятельный контекст минимум 80 символов, не ссылка «см. разговор»;
- `initiation: user_asked` — только при действительном запросе пользователя на работу
  в сессиях и если tool разрешает такую задачу; не выдавайте предложение за запрос;
- `use_worktree: false` — только если клиент разрешает общий checkout. Если нет — спросите
  о другом режиме; не создавайте worktree автоматически;
- короткие `name`/`title` и модель из реально доступного набора клиента. Сохраните
  намеченный handle/token в memo до вызова, возвращённый ID — после.

Не передавайте `cwd`, host, preset или другой проект без соответствующего решения
пользователя и проверки разрешённого назначения. Не включайте cloud или offer там,
где они запрещены. Не переключайте родительскую модель, effort, permissions, настройки
или browser/MCP для получения недоступной возможности.

Актуальные доступные модели выясняйте из среды/инструментов клиента. Не конструируйте
версионные ID по памяти. Разрешённый дешёвый профиль полезен для извлечения фактов;
сложные задачи назначайте сильной модели. При отказе настройки не запускайте повторные
сессии вслепую: сначала установите, создана ли первая, и согласуйте недоступный режим.

## Доставка и ожидание

Храните **фактические local_... ID**. Короткий name может служить только адресом, который
вернул/разрешил клиент; не угадывайте его. Сообщение должно содержать envelope текущего
назначения. Готовность/результат проверяются по фактическому источнику канала.

`delivered` означает доставку, `queued` — ожидание обработки, не выполнение. Ошибка или
таймаут доставки не разрешают новую сессию. Учитывайте, что между сессиями с разными
permissions сообщения могут ожидать пользовательского подтверждения и не доходить сразу.
Если подтвердить источник/доставку нельзя, ветка остаётся заблокированной.

Используйте push-уведомления/события завершения, которые действительно предоставляет
клиент. Не опрашивайте ListAgents/list_sessions в цикле, не отправляйте «готово?» и не
создавайте Cron/loop/Monitor для проверки сессий. Пока worker ждёт grant, его ready можно
обработать адресно; пока parent ждёт report — завершить ход с сохранённым root ID.
В новой реплике читайте малый root/current_frontier/control, не full brief/evidence/history
и не начинайте разбиение заново. Parent не читает source/diff/raw logs и не повторяет тесты.
Адресный list_events для содержательного evidence выполняет назначенный verifier, не parent;
parent использует его лишь для конкретной сверки источника/token/управляющего блокера.

Автоматическое событие или отчёт другой сессии не является пользовательским согласием.
Если в ходе, начатом событием, клиент запрещает новые запуски, продолжайте только
разрешённую обработку результатов; недоступный dispatch сообщите как ограничение.
Не требуйте, чтобы дочерняя сессия отвечала за гарантию автоматического пробуждения parent.

## Git runtime: policy не отменяет ограничения клиента

`git_delivery` обязателен в v3 brief/control; ready/grant подтверждают policy
`start-target-linear-delivery/v1` и captured target/expected_tip либо явный not_applicable
с причиной. Git CLI объявляется внешней зависимостью только изменяемого Git-результата;
чистое read-only исследование/non-Git не требует commit/dev. Его установку/доступ скил не выполняет.
Один назначенный последовательный Git-owner после content pass получает отдельный git-grant,
не обычный file grant. Общий checkout не означает независимые index/refs; сериализация
по canonical worktree/git-dir/common-dir. Full baseline/commands/history/reconcile остаются
в назначенных child details; parent получает refs/OIDs/короткие receipts.

До start mutation сохраняются immutable canonical identity/start target/start_oid(unborn),
initial index/status/baseline и expected_tip. Resume/client worktree metadata не переизбирают
цель. Default direct local commit only owned accepted paths; rebase лишь нужный разрешённый
own unpublished range по explicit refs/OIDs. Нет auto worktree/branches/скрытого FF-return,
merge/merge-helper/новых merge commits, flatten old history, force-push, auto stash/reset/
clean/add-all. Push — отдельное согласие, не условие local delivery.

Если higher-priority клиент требует branch-first на default branch, а captured target
default, сообщите conflict/blocked *до* переключения; не заменяйте start target временной
веткой. Если sync tool обязателен и делает merge (например, sync_with_base_branch), не
вызывайте его и не обходите обязательность ручной командой: blocked parent. Реальные
permission prompts обязательны; grant не позволяет менять permissions или идти через peer.

Intent parent persist/get до Git mutation; owner full intent/checkpoint/reconcile в своих
IDs. Timeout не retry/release. Crash после commit сверяется, не создаёт повторный commit;
конфликт без --skip/foreign abort. После delivery release нужен новый независимый final_git
receipt target/start/final OID/tree/inventory/manifest/history/criteria; content pass не
accepted. Hook/rebase/content drift инвалидирует старый audit. Только final accepted
открывает downstream, включая случай unchanged tree. Полные схемы — Contracts.

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

## Навигация и жизненный цикл

При упоминании реальной сессии давайте ссылку формата `[Название](#local_<реальный-id>)`:
используйте целиком ID, который вернул инструмент, не добавляйте local_ второй раз.
Это ссылка внутри Desktop, не ссылка для внешней публикации. При поддержке клиента можно
показать созданную сессию рядом с родителем, но это не требуется для исполнения.

После release сохраняйте адрес для возможного repair. Не архивируйте/удаляйте сессии
автоматически: это отдельное решение пользователя. Worker не обещает невидимость;
системные progress, финальные сообщения и permission prompts могут отображаться.
Каждый envelope/summary к parent ≤2000 символов, final и wrap-up также ≤2000 каждый.
Не передавайте source/diff/stdout/full reports, не дробите их потоком; full evidence в
назначенных detail IDs у непосредственного потребителя, критический риск — кратко+ref.
Учитывайте автоматически пересылаемые final/wrap-up; подробная peer-связь не должна
неявно попасть parent. Нет безопасного прямого канала — verifier читает проверяемые источники.
Не просите peer выполнить действие, которое запрещено вашей сессии или уже отклонено.

## Роли, слоты и audit

Scout/planner/dev-lead/worker/verifier используют тот же handshake v3 и общий предел
**economy ≤2 / fast ≤4**, включая bounded agents. Intent, ready/ожидание grant, работа,
uncertain занимают слот до подтверждения завершения активности. Только parent создаёт
Desktop-сессии; child запрашивает нужный запуск у него. Bounded agent не заменяет требуемую
Desktop-сессию; слоты и процедура назначены заранее. Dev-lead сам ведёт полноценный локальный
проектный dev-цикл разработки; parent не становится повторным implementer/test runner.
Read-only scout/planner/research/verifier загружают только назначенные применимые процедуры,
не полный dev-цикл только из-за наличия dev.

После writer submission/release parent закрепляет версию/manifest/details и запрещает новых
writer. Независимому verifier (не автору/соавтору) даётся отдельное назначение/ready/read-grant
**до acceptance writer**, без deadlock обычной зависимости. Downstream реализация ждёт acceptance.
Verifier независимо перечисляет все фактические tracked/untracked/new/deleted, mode/type/
link-target и side-effect изменения против baseline, включая не названные автором; сверяет
полный inventory с manifest/ownership. Нет полного baseline/inventory — blocked. Manifest
закрепляет presence/deletion, kind, релевантный mode, symlink target и SHA-256 regular bytes.
Verifier читает actual artifacts/full details, проверяет критерии/команды; в конце повторяет
inventory/все свойства pin и frozen content, пишет full audit и отдельный compact receipt.
Required Git проходит отдельную последовательную Git-фазу после content pass; затем
final_git verifier проверяет конечные target/start/final OID/tree/manifest/inventory/history
против неизменного исходного baseline, не чистого diff нового HEAD. Content receipt не final.
Parent сверяет реальный источник, корреляцию, независимость, версию и точное равенство
receipt criterion IDs своему frozen expected_criterion_ids с совпадающим criteria_version;
оба поля утверждены и хранятся в малом control до grant. Любое изменение после audit делает
verdict stale. Только явная acceptance=accepted открывает downstream. Rejected/paused,
release и отдельное снятие reservation parent для назначенного repair после release
не открывают downstream; новая версия требует новой проверки.

Worker без memo не возвращает полный report parent. Назначенный verifier с memo сам собирает
evidence по доступным проверяемым источникам/прямому каналу/адресному транскрипту. Нет доступа
или такого verifier — blocked evidence_unavailable, не verbose/file fallback. После submission
ни автор, ни verifier не меняют свои frozen details; repair получает новые IDs/версию.
v1/v2/неизвестная версия — protocol_mismatch, никакого silent mix установленного старого worker.
