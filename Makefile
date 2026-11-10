.PHONY: install

# Корень этого репозитория — по расположению Makefile, а не по текущему каталогу,
# поэтому работают и `make -C`, и `make -f`.
REPO_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SKILLS_DIR := $(REPO_DIR)/skills

# Каталог, откуда запущен make: $(PWD) из окружения не меняется при `make -C`.
LAUNCH_DIR := $(if $(PWD),$(PWD),$(CURDIR))

# Рабочая директория по умолчанию в первом вопросе; можно задать заранее:
# make install PROJECT=/путь/к/проекту
PROJECT ?= $(LAUNCH_DIR)

install:
	@cd "$(LAUNCH_DIR)" 2>/dev/null || cd "$(CURDIR)"; sh "$(REPO_DIR)/scripts/install.sh" "$(SKILLS_DIR)" "$(PROJECT)"
