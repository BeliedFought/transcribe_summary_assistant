# Индекс навыков репозитория transcribe_summary_assistant

Локальный индекс навыков этого репозитория. Формируется автоматически навыком `glob_update_indexes` из состава `doc/skills/`. Перечисляет общие (`glob_*`) и проектные навыки репо. Порядок принятия решений агента при отсутствии нормы - `project_standards.md`, раздел 07.06.

| Навык | Класс | Автоприменение | Версия | Назначение |
|-------|-------|----------------|--------|-----------|
| `glob_audit_repository` | общий | true | 2.5.0 | Двухуровневый аудит и исправление репозитория на соответствие стандарту с учетом зафиксированных оверрайдов проекта |
| `glob_setup_pip_mirror` | общий | true | 1.0.0 | Подбирает и настраивает зеркало PyPI в pip.conf при недоступности pypi.org |
| `glob_update_indexes` | общий | true | 1.1.1 | Актуализирует локальные индексы репозитория - индекс навыков _index_skills_repo.md из состава doc/skills/ и индекс спецификаций doc/specs/_index_specs.md из состава doc/specs/ |
| `glob_update_kilo_rules` | общий | true | 1.1.2 | Проверяет MCP-серверы и правила, загружаемые агенту в начале сессии |

## Навыки формата Anthropic Agent Skills (SKILL.md)

| Навык | Путь | Назначение |
|-------|------|-----------|
| `glob-skill-deploy` | `doc/skills/glob-skill-deploy/SKILL.md` | Деплоит навык формата Anthropic Agent Skills из doc/skills/<name>/ в боевые каталоги инструментов - opencode, Kilo Code, Cursor (проектные или персональные). |
| `glob-skill-migrate-anthropic` | `doc/skills/glob-skill-migrate-anthropic/SKILL.md` | Переносит навык внутреннего формата (doc/skills/<name>.md) в формат Anthropic Agent Skills - каталог <name>/SKILL.md с ресурсами. |

