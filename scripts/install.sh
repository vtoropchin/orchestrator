#!/bin/sh
# Интерактивный запуск skills CLI для make install.
# Спрашивает рабочую директорию и запускает CLI из неё: проектная установка
# попадает в выбранный каталог. После установки сообщает, что получил
# DeepSeek Harness (dsh) и, если поставлен orchestrate, предлагает настроить Jev
# (scripts/configure-jev.sh). Собственного установщика здесь нет.
#
# Использование: sh scripts/install.sh <каталог skills/> <директория по умолчанию>
set -eu
script_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)

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
# Абсолютный путь: после cd в проект относительный указывал бы на код проекта.
skills_dir=$(cd -- "$skills_dir" && pwd -P)

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
# DeepSeek Harness (dsh) нет в зашитом списке агентов skills CLI, но он читает
# .agents/skills проекта — это секция Universal, которую CLI ставит всегда.
printf '%s\n' \
  'make install: DeepSeek Harness (dsh) в списке CLI отдельно не показан: он читает' \
  '  .agents/skills — секция «Universal (.agents/skills)», она устанавливается всегда.' \
  '  Для dsh выберите проектную область (Project), а не глобальную.' \
  'make install: dev и orchestrate по умолчанию включают стиль i-have-adhd для сообщений' \
  '  пользователю. Отметьте i-have-adhd вместе с ними; без него — обычный стиль.'
cd -- "$work_dir"
status=0
env -u AI_AGENT -u CLAUDECODE -u CLAUDE_CODE DISABLE_TELEMETRY=1 npx skills@1.7.6 add "$skills_dir" || status=$?
[ "$status" -eq 0 ] || exit "$status"

# Итог для dsh: какие скилы источника лежат в .agents/skills выбранного проекта.
found=0
total=0
for skill in "$skills_dir"/*/; do
  [ -f "${skill}SKILL.md" ] || continue
  total=$((total + 1))
  name=$(basename -- "$skill")
  [ -f "$work_dir/.agents/skills/$name/SKILL.md" ] && found=$((found + 1))
done
if [ "$found" -gt 0 ]; then
  printf 'make install: DeepSeek Harness (dsh): %s из %s скилов источника в %s/.agents/skills\n' \
    "$found" "$total" "$work_dir"
  if [ -f "$work_dir/.agents/skills/orchestrate/SKILL.md" ]; then
    printf '%s\n' \
      'make install: чтобы orchestrate в dsh запускал субагентов на более дешёвых моделях, включите' \
      '  в dsh: Settings → Subagent → Model selection → «Allow agents to choose models for' \
      '  Subagents» и отметьте дешёвую и сильную модели. Действует только для новых сессий.'
  fi
else
  printf 'make install: DeepSeek Harness (dsh): в %s/.agents/skills нет скилов источника;\n  %s\n' \
    "$work_dir" 'dsh их не увидит (установка отменена или выбрана глобальная область).'
fi

# Оркестраторы включают i-have-adhd по умолчанию; напомнить, если его не поставили рядом.
skills_root=$work_dir/.agents/skills
if [ -f "$skills_dir/i-have-adhd/SKILL.md" ] && [ ! -f "$skills_root/i-have-adhd/SKILL.md" ] &&
  { [ -f "$skills_root/dev/SKILL.md" ] || [ -f "$skills_root/orchestrate/SKILL.md" ]; }; then
  printf 'make install: в %s нет i-have-adhd: dev/orchestrate будут писать в обычном стиле.\n  %s\n' \
    "$skills_root" 'Чтобы включить его, повторите make install и отметьте i-have-adhd.'
fi

# orchestrate может брать суждения у Jev: ключ и адрес нужны в .env проекта.
if [ -f "$skills_root/orchestrate/SKILL.md" ] || [ -f "$work_dir/.claude/skills/orchestrate/SKILL.md" ]; then
  sh "$script_dir/configure-jev.sh" "$work_dir" "$skills_dir/orchestrate/scripts/jev.py"
elif [ -f "$skills_dir/orchestrate/SKILL.md" ]; then
  printf 'make install: orchestrate не найден в проекте. Если он установлен глобально, настроить\n  %s\n' \
    "Jev для проекта можно так: sh $script_dir/configure-jev.sh $work_dir"
fi
