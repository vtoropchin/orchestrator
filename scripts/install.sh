#!/bin/sh
# Интерактивный запуск skills CLI для make install.
# Спрашивает рабочую директорию и запускает CLI из неё: проектная установка
# попадает в выбранный каталог. Собственного установщика здесь нет.
#
# Использование: sh scripts/install.sh <каталог skills/> <директория по умолчанию>
set -eu

if [ "$#" -ne 2 ]; then
  printf '%s\n' 'Использование: sh scripts/install.sh <каталог skills/> <директория по умолчанию>' >&2
  exit 2
fi
skills_dir=$1
default_dir=$2

if [ ! -t 0 ] || [ ! -t 1 ]; then
  printf '%s\n' 'make install: запустите команду в интерактивном терминале; ничего не установлено.' >&2
  exit 1
fi
if [ ! -d "$skills_dir" ]; then
  printf 'make install: нет каталога скилов %s; ничего не установлено.\n' "$skills_dir" >&2
  exit 1
fi

while :; do
  printf 'Укажите рабочую директорию [%s]: ' "$default_dir"
  if ! IFS= read -r answer; then
    printf '\n%s\n' 'make install: ввод прерван; ничего не установлено.' >&2
    exit 1
  fi
  answer=$(printf '%s' "$answer" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  [ -n "$answer" ] || answer=$default_dir
  case $answer in
    '~') answer=${HOME:?} ;;
    '~/'*) answer=${HOME:?}/${answer#'~/'} ;;
  esac
  # Относительный путь считается от каталога запуска (текущего каталога скрипта).
  if work_dir=$(cd -- "$answer" 2>/dev/null && pwd -P); then
    break
  fi
  printf 'Нет каталога %s; укажите существующий.\n' "$answer" >&2
done

printf 'make install: рабочая директория %s, источник %s\n' "$work_dir" "$skills_dir"
cd -- "$work_dir"
exec env -u AI_AGENT -u CLAUDECODE -u CLAUDE_CODE DISABLE_TELEMETRY=1 npx skills@1.7.6 add "$skills_dir"
