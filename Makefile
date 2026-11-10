.PHONY: install

# Каталог публичных скилов этого репозитория и проект, куда они ставятся.
# По умолчанию проект — сам репозиторий; другой проект: make install PROJECT=/путь/к/проекту
SKILLS_DIR := $(CURDIR)/skills
PROJECT ?= $(CURDIR)

install:
	@if [ ! -t 0 ] || [ ! -t 1 ]; then printf '%s\n' 'make install: запустите команду в интерактивном терминале; ничего не установлено.' >&2; exit 1; fi
	@if [ ! -d "$(PROJECT)" ]; then printf 'make install: нет каталога проекта %s; ничего не установлено.\n' "$(PROJECT)" >&2; exit 1; fi
	@printf 'make install: проект %s, источник %s\n' "$(PROJECT)" "$(SKILLS_DIR)"
	@cd "$(PROJECT)" && env -u AI_AGENT -u CLAUDECODE -u CLAUDE_CODE DISABLE_TELEMETRY=1 npx skills@1.7.6 add "$(SKILLS_DIR)"
