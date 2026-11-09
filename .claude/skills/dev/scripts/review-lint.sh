#!/bin/sh
# review-lint — проверка формы и гигиены REVIEW.md (скил dev, фаза 6; скил adapt).
# POSIX sh, нужны только git и стандартные утилиты. Код возврата: 0 — нарушений нет,
# 1 — есть нарушения (список в stdout), 2 — ошибка запуска.

set -f
LC_ALL=C
export LC_ALL

usage() {
	cat <<'EOF'
Использование: review-lint.sh [--today ГГГГ-ММ-ДД] [путь/к/REVIEW.md]

Проверяет REVIEW.md репозитория по контракту «код-ревью по риску»:
  - на месте все 7 разделов с точными заголовками, без повторов;
  - каждый glob в разделах «Высокий риск», «Безопасность», «Низкий риск» совпадает
    хотя бы с одним файлом (git ls-files ':(glob)…', учитываются и неотслеживаемые);
  - в «Высокий риск» есть сам REVIEW.md, .gitattributes и .claude/skills/dev/**
    (фазы ревью и сам review-lint);
  - в «Низкий риск» и «Не ревьюить» нет путей .claude/ и целей симлинков из .claude/ —
    ни glob, начинающегося с них, ни glob, который захватывает их файлы;
  - .gitattributes содержит строку «REVIEW.md merge=union»;
  - в «Повторяющиеся находки» не больше 15 правил, каждое в формате
    «- [<glob-якорь>] <правило> — <ГГГГ-ММ-ДД>, <откуда>», якорь совпадает хотя бы
    с одним файлом, срок «до: ГГГГ-ММ-ДД» не истёк;
  - в файле не больше 150 строк и нет дословно повторяющихся пунктов и правил.

Путь по умолчанию — REVIEW.md в корне текущего git-репозитория. Glob-пути считаются
от корня репозитория, в котором лежит файл. HTML-комментарии <!-- … --> не читаются.
--today задаёт «сегодня» для проверки сроков (по умолчанию — системная дата).

Код возврата: 0 — нарушений нет; 1 — нарушения (по одному на строку); 2 — ошибка запуска.
EOF
}

today=$(date +%Y-%m-%d)
file=""
while [ $# -gt 0 ]; do
	case "$1" in
	-h | --help) usage; exit 0 ;;
	--today)
		[ $# -ge 2 ] || { echo "review-lint: --today без даты" >&2; exit 2; }
		today=$2; shift 2 ;;
	-*) echo "review-lint: неизвестный ключ $1 (см. --help)" >&2; exit 2 ;;
	*) file=$1; shift ;;
	esac
done

if [ -z "$file" ]; then
	root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "review-lint: не git-репозиторий" >&2; exit 2; }
	file=$root/REVIEW.md
fi
[ -f "$file" ] || { echo "review-lint: нет файла $file" >&2; exit 2; }
dir=$(cd "$(dirname "$file")" && pwd) || exit 2
root=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || { echo "review-lint: $file не в git-репозитории" >&2; exit 2; }

tmp=$(mktemp -d "${TMPDIR:-/tmp}/review-lint.XXXXXX") || exit 2
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
: >"$tmp/out"

fail() { printf '%s\n' "$1" >>"$tmp/out"; }

# Совпадает ли glob хотя бы с одним файлом репозитория (отслеживаемым или новым).
matches() {
	[ -n "$(git -C "$root" ls-files --cached --others --exclude-standard -- ":(glob)$1" 2>/dev/null | head -n 1)" ]
}

# Разбор: H<TAB>раздел — заголовок; G<TAB>раздел<TAB>glob — путь раздела риска;
# N<TAB>Не ревьюить<TAB>glob; R<TAB>пункт — правило; L<TAB>пункт — любой пункт
# списка (для поиска дублей).
# Пункт списка — строка «- …» вместе со строками-продолжениями с отступом: они
# склеиваются до следующего «- », заголовка или строки без отступа.
awk '
function flush(   rest, i, j) {
	if (item == "") return
	print "L\t" item
	if (sec == "Высокий риск" || sec == "Безопасность" || sec == "Низкий риск") {
		rest = item
		while ((i = index(rest, "`")) > 0) {
			rest = substr(rest, i + 1); j = index(rest, "`")
			if (j == 0) break
			print "G\t" sec "\t" substr(rest, 1, j - 1); rest = substr(rest, j + 1)
		}
	}
	if (sec == "Не ревьюить") {
		rest = item
		while ((i = index(rest, "`")) > 0) {
			rest = substr(rest, i + 1); j = index(rest, "`")
			if (j == 0) break
			print "N\t" sec "\t" substr(rest, 1, j - 1); rest = substr(rest, j + 1)
		}
	}
	if (sec == "Повторяющиеся находки") print "R\t" item
	item = ""
}
{
	line = $0; out = ""
	while (length(line) > 0) {
		if (inc) {
			i = index(line, "-->")
			if (i == 0) line = ""; else { line = substr(line, i + 3); inc = 0 }
		} else {
			i = index(line, "<!--")
			if (i == 0) { out = out line; line = "" }
			else { out = out substr(line, 1, i - 1); line = substr(line, i + 4); inc = 1 }
		}
	}
	sub(/[ \t]+$/, "", out)
	if (out ~ /^## /) { flush(); sec = substr(out, 4); print "H\t" sec; next }
	if (out ~ /^- /) { flush(); item = out; next }
	if (out == "") next
	if (item != "" && out ~ /^[ \t]/) { sub(/^[ \t]+/, "", out); item = item " " out; next }
	flush()
}
END { flush() }' "$file" >"$tmp/parsed"

# 1. Разделы.
for h in "Как здесь выглядит сбой" "Высокий риск" "Безопасность" "Низкий риск" \
	"Не ревьюить" "Правила замечаний" "Повторяющиеся находки"; do
	n=$(grep -c -x -F "H	$h" "$tmp/parsed")
	if [ "$n" -eq 0 ]; then fail "разделы: нет заголовка «## $h»"
	elif [ "$n" -gt 1 ]; then fail "разделы: заголовок «## $h» повторяется $n раз"
	fi
done

# 2. Пути разделов риска.
high_review=no
high_attr=no
high_dev=no
grep '^G	' "$tmp/parsed" | while IFS='	' read -r _ sec g; do
	matches "$g" || fail "$sec: путь \`$g\` не совпадает ни с одним файлом"
done
grep '^G	Высокий риск	' "$tmp/parsed" | cut -f3 >"$tmp/high"
while read -r g; do
	files=$(git -C "$root" ls-files --cached --others --exclude-standard -- ":(glob)$g" 2>/dev/null)
	printf '%s\n' "$files" | grep -q -x -F 'REVIEW.md' && high_review=yes
	printf '%s\n' "$files" | grep -q -x -F '.gitattributes' && high_attr=yes
	{ [ "$g" = '.claude/skills/dev/**' ] || printf '%s\n' "$files" | grep -q -x -F '.claude/skills/dev/SKILL.md'; } && high_dev=yes
done <"$tmp/high"
[ "$high_review" = yes ] || fail "Высокий риск: нет пути, покрывающего сам REVIEW.md"
[ "$high_attr" = yes ] || fail "Высокий риск: нет пути, покрывающего .gitattributes"
[ "$high_dev" = yes ] || fail "Высокий риск: нет пути \`.claude/skills/dev/**\` (фазы ревью и review-lint)"
# Инструменты агента (.claude/ и цели его симлинков внутри репозитория) не бывают
# ни низким риском, ни «Не ревьюить».
printf '.claude/\n' >"$tmp/protected"
rootp=$(cd "$root" && pwd -P)
if [ -d "$root/.claude" ]; then
	find "$root/.claude" -type l | while IFS= read -r l; do
		t=$(cd "$(dirname "$l")" 2>/dev/null && cd -P "$(readlink "$l")" 2>/dev/null && pwd -P) || continue
		case "$t" in "$rootp"/*) printf '%s/\n' "${t#"$rootp"/}" >>"$tmp/protected" ;; esac
	done
fi
under_protected() { awk 'NR == FNR { p[n++] = $0; next } { for (i = 0; i < n; i++) if (index($0, p[i]) == 1) { f = 1; exit } } END { exit !f }' "$tmp/protected" -; }
for sec in "Низкий риск" "Не ревьюить"; do
	grep "^[GN]	$sec	" "$tmp/parsed" | cut -f3 | while read -r g; do
		if printf '%s\n' "${g#./}" | under_protected; then
			fail "$sec: путь \`$g\` под .claude/ или целью его симлинка — инструменты агента сюда не относятся"
		elif git -C "$root" ls-files --cached --others --exclude-standard -- ":(glob)$g" 2>/dev/null | under_protected; then
			fail "$sec: путь \`$g\` захватывает файлы под .claude/ или целью его симлинка — сузить glob"
		fi
	done
done

# 3. Слияние union.
if ! grep -q -E '^[[:space:]]*REVIEW\.md[[:space:]].*merge=union' "$root/.gitattributes" 2>/dev/null; then
	fail ".gitattributes: нет строки «REVIEW.md merge=union»"
fi

# 4. Правила.
grep '^R	' "$tmp/parsed" | cut -f2- >"$tmp/rules"
count=$(grep -c '' "$tmp/rules")
[ "$count" -le 15 ] || fail "Повторяющиеся находки: правил $count, потолок 15 — слить похожие"
while IFS= read -r r; do
	anchor=$(printf '%s\n' "$r" | sed -n 's/^- \[\([^]]*\)\] .*/\1/p')
	if [ -z "$anchor" ]; then
		fail "Повторяющиеся находки: правило без якоря [glob]: $r"
		continue
	fi
	matches "$anchor" || fail "Повторяющиеся находки: якорь [$anchor] не совпадает ни с одним файлом: $r"
	printf '%s\n' "$r" | grep -q -E '^- \[[^]]+\] .+ — [0-9]{4}-[0-9]{2}-[0-9]{2}, .+' ||
		fail "Повторяющиеся находки: строка не по формату «- [якорь] правило — ГГГГ-ММ-ДД, откуда»: $r"
	until_date=$(printf '%s\n' "$r" | sed -n 's/.*до: *\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\).*/\1/p')
	if [ -n "$until_date" ] && [ "$(printf '%s\n%s\n' "$until_date" "$today" | sort | head -n 1)" = "$until_date" ] &&
		[ "$until_date" != "$today" ]; then
		fail "Повторяющиеся находки: срок до: $until_date истёк — снять правило в архив: $r"
	fi
done <"$tmp/rules"

# 5. Размер и дубли.
lines=$(grep -c '' "$file")
[ "$lines" -le 150 ] || fail "файл: $lines строк, предел 150"
grep '^L	' "$tmp/parsed" | cut -f2- | sort | uniq -d | while IFS= read -r d; do
	fail "дубль: пункт повторяется дословно: $d"
done
sed -n 's/^- \[[^]]*\] \(.*\) — [0-9]\{4\}-.*/\1/p' "$tmp/rules" | sort | uniq -d | while IFS= read -r d; do
	fail "Повторяющиеся находки: правило повторяется дословно: $d"
done

if [ -s "$tmp/out" ]; then
	sed 's/^/review-lint: /' "$tmp/out"
	exit 1
fi
echo "review-lint: нарушений нет ($file)"
exit 0
