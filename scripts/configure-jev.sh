#!/bin/sh
# Интерактивная настройка Jev для orchestrate (вызывается из make install).
# Спрашивает адрес API, модель и ключ и записывает JEV_AI_* в .env проекта
# (права 0600, остальные строки файла сохраняются). Ключ не печатается и не
# передаётся аргументами команд. Затем по согласию — проверка подключения
# через GET /v1/models: инференса нет, баланс не расходуется.
#
# Использование: sh scripts/configure-jev.sh <корень проекта> [путь к jev.py]
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  printf '%s\n' 'Использование: sh scripts/configure-jev.sh <корень проекта> [путь к jev.py]' >&2
  exit 2
fi
work_dir=$1
jev_py=${2:-}
env_file=$work_dir/.env
default_base=https://jev-ai.pro/api
default_model=jev-latest
tmp=
echo_off=0

cleanup() {
  if [ "$echo_off" -eq 1 ]; then stty echo 2>/dev/null || :; fi
  if [ -n "$tmp" ]; then rm -f -- "$tmp"; fi
}
trap cleanup EXIT
trap 'cleanup; exit 130' INT TERM HUP

say() { printf '%s\n' "$@"; }

# ask <вопрос> <по умолчанию> → $reply (без крайних пробелов).
ask() {
  printf '%s [%s]: ' "$1" "$2"
  if ! IFS= read -r reply; then
    printf '\n'
    say 'make install: ввод прерван; настройка Jev пропущена, .env не изменён.' >&2
    exit 0
  fi
  reply=$(printf '%s' "$reply" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  [ -n "$reply" ] || reply=$2
}

# Файл не должен кончаться без перевода строки: иначе дописанная строка склеится.
end_with_newline() {
  if [ -s "$1" ] && [ "$(tail -c 1 "$1" | od -An -c | tr -d ' ')" != '\n' ]; then
    printf '\n' >>"$1"
  fi
}

yes_answer() {
  case $1 in y|Y|yes|Yes|д|Д|да|Да) return 0 ;; *) return 1 ;; esac
}

say '' 'make install: orchestrate умеет брать дешёвые суждения у модели Jev (Jev AI/TypeSafe),' \
  '  чтобы не тратить лимиты сильных моделей на калибровку назначений.' \
  '  Без ключа orchestrate работает как раньше. Подробно: skills/orchestrate/references/jev.md'
ask 'Настроить Jev для этого проекта? (y/N)' 'N'
if ! yes_answer "$reply"; then
  say 'make install: Jev не настроен. Позже: повторите make install или запустите' \
    "  sh scripts/configure-jev.sh $work_dir"
  exit 0
fi

if [ -L "$env_file" ]; then
  say "make install: $env_file — символическая ссылка; запишите ключ в исходный файл сами." >&2
  exit 0
fi
in_git=0
if git -C "$work_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  in_git=1
  if git -C "$work_dir" ls-files --error-unmatch -- .env >/dev/null 2>&1; then
    say "make install: .env уже отслеживается git в $work_dir — ключ попал бы в коммит." \
      '  Ничего не записано. Уберите файл из индекса (git rm --cached .env), добавьте .env' \
      '  в .gitignore и повторите настройку.' >&2
    exit 0
  fi
fi

key_re='^[[:space:]]*(export[[:space:]]+)?JEV_AI_API_KEY[[:space:]]*='
if [ -f "$env_file" ] && grep -Eq "${key_re}[[:space:]]*[^[:space:]]" "$env_file"; then
  ask "В $env_file уже есть JEV_AI_API_KEY. Заменить ключ, адрес и модель? (y/N)" 'N'
  if ! yes_answer "$reply"; then
    say 'make install: прежние настройки Jev сохранены.'
    skip_write=1
  fi
fi

if [ "${skip_write:-0}" -eq 0 ]; then
  while :; do
    ask 'Адрес API Jev' "$default_base"
    base=${reply%/}
    if printf '%s\n' "$base" | grep -Eq '^https://[A-Za-z0-9.-]+(:[0-9]+)?(/[A-Za-z0-9._~/%-]*)?$' ||
      printf '%s\n' "$base" | grep -Eq '^http://(127\.0\.0\.1|localhost)(:[0-9]+)?(/[A-Za-z0-9._~/%-]*)?$'; then
      break
    fi
    say 'Нужен адрес https://… (http:// — только для localhost).' >&2
  done
  while :; do
    ask 'Модель Jev' "$default_model"
    model=$reply
    printf '%s\n' "$model" | grep -Eq '^[A-Za-z0-9._:/-]+$' && break
    say 'Имя модели: латиница, цифры и . _ : / -' >&2
  done

  printf 'Ключ API (создаётся в панели провайдера; ввод не отображается): '
  if [ -t 0 ]; then stty -echo; echo_off=1; fi
  key=
  IFS= read -r key || key=
  if [ "$echo_off" -eq 1 ]; then stty echo; echo_off=0; fi
  printf '\n'
  key=$(printf '%s' "$key" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  if [ -z "$key" ]; then
    say 'make install: ключ не введён; .env не изменён.'
    exit 0
  fi
  # Значения пишутся в .env без кавычек: разрешены только символы, безопасные для shell.
  if printf '%s\n' "$key" | grep -Eqv '^[A-Za-z0-9._~+/=:-]+$'; then
    say 'make install: в ключе допустимы только латиница, цифры и . _ ~ + / = : -; .env не изменён.' >&2
    exit 0
  fi

  # Новый файл рядом с .env: mktemp создаёт его с правами 0600, затем атомарная замена.
  tmp=$(mktemp "$work_dir/.env.jev.XXXXXX")
  if [ -f "$env_file" ]; then
    grep -Ev '^[[:space:]]*(export[[:space:]]+)?JEV_AI_(API_KEY|BASE_URL|MODEL)[[:space:]]*=' \
      "$env_file" >"$tmp" || :
    end_with_newline "$tmp"
  fi
  {
    printf '%s\n' '# Jev для orchestrate (make install)'
    printf 'JEV_AI_BASE_URL=%s\n' "$base"
    printf 'JEV_AI_MODEL=%s\n' "$model"
    printf 'JEV_AI_API_KEY=%s\n' "$key"
  } >>"$tmp"
  key=
  chmod 600 "$tmp"
  mv -f -- "$tmp" "$env_file"
  tmp=
  say "make install: настройки Jev записаны в $env_file (права 0600)."
fi

if [ "$in_git" -eq 1 ] && ! git -C "$work_dir" check-ignore -q -- .env 2>/dev/null; then
  ask "Файл .env не в .gitignore проекта. Добавить строку .env в $work_dir/.gitignore? (Y/n)" 'Y'
  if yes_answer "$reply"; then
    ignore=$work_dir/.gitignore
    end_with_newline "$ignore"
    printf '%s\n' '.env' >>"$ignore"
    say 'make install: .env добавлен в .gitignore.'
  else
    say 'make install: внимание — .env не игнорируется git; не коммитьте его.' >&2
  fi
fi

if [ -n "$jev_py" ] && [ -f "$jev_py" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    say 'make install: нет python3 — orchestrate будет работать без Jev, пока он не появится.'
    exit 0
  fi
  ask 'Проверить подключение сейчас (GET /v1/models, баланс не расходуется)? (Y/n)' 'Y'
  if yes_answer "$reply"; then
    status=0
    out=$(python3 "$jev_py" --project "$work_dir" check) || status=$?
    say "  $out"
    if [ "$status" -eq 0 ]; then
      say 'make install: Jev отвечает; модели перечислены выше.'
    else
      say "make install: проверка не прошла (код $status); orchestrate будет работать без Jev." \
        '  Проверьте ключ, баланс и сеть до хоста из вывода выше.'
    fi
  fi
fi
exit 0
