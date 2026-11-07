.PHONY: install

install:
	@if [ ! -t 0 ] || [ ! -t 1 ]; then printf '%s\n' 'make install: запустите команду в интерактивном терминале; ничего не установлено.' >&2; exit 1; fi
	@env -u AI_AGENT -u CLAUDECODE -u CLAUDE_CODE DISABLE_TELEMETRY=1 npx skills@1.7.6 add ./skills
