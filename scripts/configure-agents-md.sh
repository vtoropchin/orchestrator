#!/bin/sh
# Интерактивная запись раздела «Модели child» для orchestrate в AGENTS.md проекта
# (вызывается из make install). Раздел стоит между маркерами-комментариями:
# при повторной установке текст набора внутри них заменяется, классы моделей
# предлагаются прежние, всё вне маркеров остаётся байт в байт. Классы вводит
# пользователь: скрипт их не угадывает.
#
# Использование: sh scripts/configure-agents-md.sh <корень проекта>
set -eu

if [ "$#" -ne 1 ]; then
  printf '%s\n' 'Использование: sh scripts/configure-agents-md.sh <корень проекта>' >&2
  exit 2
fi
work_dir=$1
file=$work_dir/AGENTS.md
begin_mark='<!-- skills:orchestrate-models:begin'
end_mark='<!-- skills:orchestrate-models:end -->'
tmp=
lines=
cleanup() { if [ -n "$tmp" ]; then rm -f -- "$tmp"; fi; }
trap cleanup EXIT
trap 'cleanup; exit 130' INT TERM HUP

say() { printf '%s\n' "$@"; }

# ask <вопрос> <по умолчанию> → $reply (без крайних пробелов). Конец ввода — выход без изменений.
ask() {
  printf '%s [%s]: ' "$1" "$2"
  if ! IFS= read -r reply; then
    printf '\n'
    say 'make install: ввод прерван; AGENTS.md не изменён.' >&2
    exit 0
  fi
  reply=$(printf '%s' "$reply" | LC_ALL=C sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  [ -n "$reply" ] || reply=$2
}

yes_answer() {
  case $1 in y|Y|yes|Yes|д|Д|да|Да) return 0 ;; *) return 1 ;; esac
}

# ID: латиница, цифры и . _ / : [ ] - (например, qwen2.5:7b, claude-opus-4-6[1m]).
model_re='^[][A-Za-z0-9._/:-]+: (light|coding|top)$'
escalation='- top: только эскалация'

# AGENTS.md — обычный файл или его нет; ссылку или каталог не трогаем. Проверка повторяется
# перед чтением и перед заменой: между ними идут вопросы.
regular_or_absent() {
  if [ -L "$file" ] || { [ -e "$file" ] && [ ! -f "$file" ]; }; then
    say "make install: $file — не обычный файл (ссылка или каталог); раздел «Модели child» не записан." >&2
    exit 0
  fi
}

if [ ! -d "$work_dir" ] || [ ! -w "$work_dir" ]; then
  say "make install: нет каталога $work_dir или в него нельзя писать; AGENTS.md не изменён." >&2
  exit 0
fi
# Путь с ведущим дефисом mktemp принял бы за ключ.
case $work_dir in -*) work_dir=./$work_dir; file=./$file ;; esac
regular_or_absent
if [ -e "$file" ] && [ ! -r "$file" ]; then
  say "make install: $file нельзя прочитать; AGENTS.md не изменён." >&2
  exit 0
fi

# Разметка файла: маркеры и раздел «Модели child», написанный вручную вне маркеров.
# Вывод: begins ends begin_line end_line headings heading_line section_end.
scan='0 0 0 0 0 0 0'
if [ -f "$file" ]; then
  scan=$(LC_ALL=C awk -v b="$begin_mark" -v e="$end_mark" '
    { sub(/\r$/, "") }
    # Блоки кода: заголовки и маркеры в них не считаются, строки — содержимое раздела.
    /^[ \t]*(```|~~~)/ { fence = !fence; if (sec) se = NR; next }
    fence { if (sec) se = NR; next }
    index($0, b) == 1 { nb++; bl = NR; inside = 1; next }
    index($0, e) == 1 { ne++; if (!el) el = NR; inside = 0; next }
    inside { next }
    sec && /^##?[ \t]/ { sec = 0 }
    /^##[ \t]+Модели child/ { nh++; hl = NR; sec = 1; se = NR; next }
    sec && !/^[ \t]*$/ { se = NR }
    END { printf "%d %d %d %d %d %d %d\n", nb, ne, bl, el, nh, hl, se }
  ' "$file")
fi
set -- $scan
begins=$1 ends=$2 begin_line=$3 end_line=$4 headings=$5 heading_line=$6 section_end=$7

if [ "$begins" -ne "$ends" ] || [ "$begins" -gt 1 ] ||
  { [ "$begins" -eq 1 ] && [ "$end_line" -lt "$begin_line" ]; }; then
  say "make install: в $file повреждены маркеры блока «Модели child» (skills:orchestrate-models)." \
    '  Оставьте одну пару begin/end или удалите обе и повторите make install; файл не изменён.' >&2
  exit 0
fi

mode=new
if [ "$begins" -eq 1 ]; then
  mode=update
  from=$begin_line to=$end_line
  if [ "$headings" -gt 0 ]; then
    say "make install: в $file есть ещё раздел «Модели child» вне блока; уберите лишний вручную."
  fi
elif [ "$headings" -gt 1 ]; then
  say "make install: в $file несколько разделов «Модели child»; оставьте один и повторите make install." \
    '  Файл не изменён.' >&2
  exit 0
elif [ "$headings" -eq 1 ]; then
  mode=adopt
  from=$heading_line to=$section_end
fi

current=
current_escalation=0
if [ "$mode" != new ]; then
  region=$(LC_ALL=C awk -v f="$from" -v t="$to" 'NR >= f && NR <= t { sub(/\r$/, ""); print }' "$file")
  current=$(printf '%s\n' "$region" | LC_ALL=C sed -n 's/^- \([][A-Za-z0-9._/:-]*: [a-z]*\)[[:space:]]*$/\1/p' |
    LC_ALL=C grep -E "$model_re" || :)
  if printf '%s\n' "$region" | LC_ALL=C grep -qx -- "$escalation"; then current_escalation=1; fi
fi
# Замена не должна молча терять текст пользователя. Ручной раздел переносится, только если
# в нём нет ничего, кроме заголовка, пустых строк и строк классов; в блоке набора текст
# заменяется (так написано в маркере), но строки списка, которые не удалось разобрать, — нет.
extra=
if [ "$mode" = adopt ]; then
  extra=$(printf '%s\n' "$region" | sed 1d | LC_ALL=C grep -Ev '^[[:space:]]*$' || :)
elif [ "$mode" = update ]; then
  extra=$(printf '%s\n' "$region" | LC_ALL=C grep -E '^[[:space:]]*[-*+][[:space:]]' || :)
fi
if [ -n "$extra" ]; then
  extra=$(printf '%s\n' "$extra" | LC_ALL=C grep -vx -- "$escalation" |
    LC_ALL=C grep -Ev '^- [][A-Za-z0-9._/:-]+: (light|coding|top)[[:space:]]*$' || :)
fi
if [ -n "$extra" ]; then
  say "make install: в разделе «Модели child» файла $file есть строки, которые замена потеряла бы:" >&2
  printf '%s\n' "$extra" | sed 's/^/  | /' >&2
  say '  Перенесите их из раздела или приведите к виду «- <ID модели>: light|coding|top»' \
    '  и повторите make install; файл не изменён.' >&2
  exit 0
fi

say '' 'make install: orchestrate берёт классы моделей субагентов (light/coding/top) из раздела' \
  '  «Модели child» в AGENTS.md. Без него модель, о которой клиент знает только имя, получает' \
  '  младший класс, и orchestrate спрашивает о ней в каждой новой сессии.'
case $mode in
  new) ask "Добавить раздел «Модели child» в $file? (y/N)" 'N' ;;
  update) ask "Обновить блок «Модели child» в $file до текста этой версии набора? (Y/n)" 'Y' ;;
  adopt) ask "Перенести раздел «Модели child» из $file в обновляемый блок make install? (Y/n)" 'Y' ;;
esac
if ! yes_answer "$reply"; then
  say 'make install: AGENTS.md не изменён.'
  exit 0
fi

keep=0
if [ -n "$current" ]; then
  say 'Сейчас записано:'
  printf '%s\n' "$current" | sed 's/^/  - /'
  ask 'Оставить эти классы? (Y/n)' 'Y'
  if yes_answer "$reply"; then keep=1; lines=$current; fi
fi
if [ "$keep" -eq 0 ]; then
  say 'Введите модели по одной: «<ID модели>: light|coding|top», ID — как в списке моделей' \
    'субагентов клиента (например, deepseek-flash: coding). Пустая строка — конец списка.'
  lines=
  while :; do
    printf '  модель: '
    if ! IFS= read -r entry; then
      printf '\n'
      say 'make install: ввод прерван; AGENTS.md не изменён.' >&2
      exit 0
    fi
    entry=$(printf '%s' "$entry" | LC_ALL=C sed 's/^[[:space:]]*-*[[:space:]]*//; s/[[:space:]]*$//; s/[[:space:]]*:[[:space:]]*\([a-z]*\)$/: \1/')
    [ -n "$entry" ] || break
    if ! printf '%s\n' "$entry" | LC_ALL=C grep -Eq "$model_re"; then
      say '  Формат: <ID модели>: light|coding|top; ID — латиница, цифры и . _ / : [ ] -' >&2
      continue
    fi
    id=${entry%: *}
    if [ -n "$lines" ] && printf '%s\n' "$lines" | sed 's/: [a-z]*$//' | LC_ALL=C grep -qxF -- "$id"; then
      say "  Модель $id уже введена." >&2
      continue
    fi
    lines=${lines:+$lines
}$entry
  done
fi
if [ -z "$lines" ]; then
  say 'make install: модели не введены; AGENTS.md не изменён.'
  exit 0
fi

if [ "$current_escalation" -eq 1 ]; then default_esc='Y'; hint='Y/n'; else default_esc='N'; hint='y/N'; fi
ask "Назначать модель класса top только эскалацией после неудачи? ($hint)" "$default_esc"
esc=0
if yes_answer "$reply"; then esc=1; fi

block=$(
  printf '%s\n' "$begin_mark. Блок пишет make install набора Skills: текст внутри заменяется при обновлении, классы моделей переносятся. -->"
  printf '%s\n' '## Модели child (orchestrate)' ''
  printf '%s\n' 'Классы моделей субагентов для `orchestrate`: `light` — дешёвые быстрые, `coding` —' \
    'сильные для кода, `top` — самые сильные. ID — как в списке моделей субагентов клиента.' ''
  printf '%s\n' "$lines" | sed 's/^/- /'
  if [ "$esc" -eq 1 ]; then printf '%s\n' "$escalation"; fi
  printf '%s\n' "$end_mark"
)

fail_write() {
  say "make install: не удалось записать $file; AGENTS.md не изменён." >&2
  exit 0
}

# Новый файл рядом с AGENTS.md; права исходного переносит cp -p, затем атомарная замена.
regular_or_absent
tmp=$(mktemp "$work_dir/.AGENTS.md.XXXXXX") || fail_write
if [ -f "$file" ]; then
  cp -p -- "$file" "$tmp" || fail_write
else
  chmod 644 "$tmp" || fail_write
fi
if [ "$mode" = new ]; then
  if [ -s "$tmp" ]; then
    [ "$(tail -c 1 "$tmp" | od -An -c | tr -d ' ')" = '\n' ] || printf '\n' >>"$tmp"
    printf '\n' >>"$tmp"
  fi
  printf '%s\n' "$block" >>"$tmp" || fail_write
else
  # Блок идёт через окружение: значения -v awk разбирает как escape-последовательности.
  # Нет перевода строки в конце файла — его не добавляем: текст вне маркеров байт в байт.
  nonl=0
  if [ -s "$file" ] && [ "$(tail -c 1 "$file" | od -An -c | tr -d ' ')" != '\n' ]; then nonl=1; fi
  BLOCK=$block LC_ALL=C awk -v f="$from" -v t="$to" -v nonl="$nonl" '
    function out(s) { if (n++) printf "\n"; printf "%s", s }
    NR == f { out(ENVIRON["BLOCK"]) }
    NR < f || NR > t { out($0) }
    END { if (n && !nonl) printf "\n" }
  ' "$file" >"$tmp" || fail_write
fi
regular_or_absent
mv -f -- "$tmp" "$file" || fail_write
tmp=
say "make install: раздел «Модели child» записан в $file между маркерами skills:orchestrate-models."
exit 0
