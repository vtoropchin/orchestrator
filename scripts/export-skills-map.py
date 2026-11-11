#!/usr/bin/env python3
"""Выгрузить рисунки docs/skills-map.html в отдельные SVG для README.

GitHub не показывает HTML в README, но показывает SVG как картинку. Скрипт берёт
встроенные <svg> по порядку, добавляет xmlns, размеры из viewBox и стили страницы
(светлая тема и тёмная через prefers-color-scheme). Запуск из корня репозитория:

    python3 scripts/export-skills-map.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "skills-map.html"
NAMES = ["skills-map-install.svg", "skills-map-orchestrate.svg", "skills-map-git.svg"]


def main() -> int:
    html = SRC.read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    light = re.search(r":root \{(.*?)\}", style, re.S).group(1).strip()
    dark = re.search(r':root\[data-theme="dark"\] \{(.*?)\}', style, re.S).group(1).strip()
    rules = [
        line.strip().replace("svg text", "text").replace("svg .", ".")
        for line in style.splitlines()
        if line.strip().startswith("svg ") and not line.strip().startswith("svg {")
    ]
    css = (
        f"svg {{ {light} color: var(--fg); }}\n"
        f"@media (prefers-color-scheme: dark) {{ svg {{ {dark} }} }}\n" + "\n".join(rules)
    )
    svgs = re.findall(r"<svg\b.*?</svg>", html, re.S)
    if len(svgs) != len(NAMES):
        print(f"export-skills-map: в {SRC.name} {len(svgs)} рисунков, ожидалось {len(NAMES)};"
              " обновите NAMES", file=sys.stderr)
        return 1
    for name, svg in zip(NAMES, svgs):
        width, height = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups()
        svg = svg.replace(
            "<svg ", f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" ', 1)
        svg = re.sub(r"(<svg[^>]*>)", lambda m: f"{m.group(1)}\n<style>\n{css}\n</style>", svg, count=1)
        (SRC.parent / name).write_text(svg + "\n", encoding="utf-8")
        print(f"export-skills-map: docs/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
