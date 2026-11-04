# Human Text Allowlist Standards. Version 5.0.0

Allowlist of human-facing texts: preferred constructions, phrases, and schemes that replace stop words and AI text markers. This document supplements `human_text_standards.md` and applies together with the other package dictionaries. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

Style abbreviations - `human_text_standards.md`, 03.09: РЛ - conversational light, РС - conversational strict, ДЛ - business light, ДС - business strict, ТЛ - technical light, ТС - technical strict.

---

## Table of Contents

**01. Purpose and Application Order**

**02. General Preferences**

**03. Preferences by Style**

**04. Dictionary Enrichment**

**05. Relations and Versioning:** 05.01 Related Documents - 05.02 Versioning

---

## 01. Purpose and Application Order

*Mandatory.*

Stop lists prohibit, the canon lexicon proposes: the "always - never" pair gives the model an exact target image, not just boundaries. The dictionary is applied:

1. When rebuilding a sentence and the denylist tables have no replacement
2. When writing - as a form reference for the chosen style
3. When editing weak text: a weak construction - the strong one from the table

The pair of tables must not duplicate the denylist: here - what to write, there - what not to write. The separator in tables is an arrow made of a hyphen and a greater-than sign (dashes are banned, 04.03).

---

## 02. General Preferences

*Mandatory.*

Apply in all six styles.

| Principle | Weak | Strong |
|----------|--------|---------|
| Активный залог: назван тот, кто делает | Наблюдалась недоступность сервиса | Сервис был недоступен 40 минут |
| Глагол вместо отглагольной конструкции | была произведена настройка | настроили |
| Конкретика вместо абстракции | улучшили производительность | время ответа снизилось с 800 до 200 мс |
| Одна идея - одно предложение | длинное предложение с тремя мыслями | три предложения |
| Главное - в начале | вводный абзац перед сутью | суть в первом предложении |
| Число вместо оценки | существенно быстрее | в 3 раза быстрее |
| Короткое слово вместо длинного | осуществлять, производить | делать, проводить |
| Число с источником и базой | рост на 25% | с 8 до 10 млн за год (отчет N, 2025) |
| Сценарий вместо абстракции | повышает эффективность работы | бухгалтер тратил 3 дня на закрытие месяца; после внедрения - 4 часа |
| Сравнение с привычным | экран 12.9 дюйма | экран чуть больше листа A4 |

Replacing a long word: «в настоящее время» -> «сейчас», «осуществляет подключение» -> «подключает», «имеет возможность» -> «может».

---

## 03. Preferences by Style

*Mandatory.*

### 03.01. Conversational Light

| Technique | Example |
|--------|--------|
| Обращение «вы», глаголы действия | «Введите почту», «Нажмите кнопку» |
| Заголовок-вопрос для раздела помощи | «Не приходит письмо?» |
| Бытовая аналогия - одна на понятие | «Кэш - как записка на холодильнике» |
| Ожидаемый результат в каждом шаге | «Появится сообщение о успешной смене пароля» |
| Подсказка на частую ошибку | «Если письма нет - проверьте папку «Спам»» |

### 03.02. Conversational Strict

| Technique | Example |
|--------|--------|
| Схема ответа: суть - детали - действие | «Проверили: сбой на нашей стороне.» |
| Маркеры структуры внутри ответа | «Что произошло:», «Что делать:» |
| Факт вместо извинения-ритуала | «Восстановлено в 14:40» вместо «приносим извинения за доставленные неудобства» |
| Конкретный следующий шаг | «Выйдите из аккаунта и войдите заново» |

### 03.03. Business Light

| Technique | Example |
|--------|--------|
| Суть в первом абзаце | «Сдачу отчета переносим с 10 на 14 июня.» |
| Прямое указание действия и срока | «Замечания - до 12 июня» |
| Причина после сути | «Причина - правки методики от заказчика» |
| Предложение решения вместо констатации проблемы | «Если перенос ломает планы - напишите, обсудим» |

### 03.04. Business Strict

| Technique | Example |
|--------|--------|
| Нумерованные пункты изменений | «1. Комиссия отменяется.» |
| Однозначные даты и условия | «с 01.10.2026», «до 30.09.2026 применяются прежние условия» |
| Формулы уведомлений как норма жанра | «Уведомляем об изменении условий» |
| Ссылка на полную редакцию | «Полная редакция опубликована по адресу <url>» |

### 03.05. Technical Light

| Technique | Example |
|--------|--------|
| Шаг = действие + команда + ожидаемый результат | «Запустите проверку: `python -m app.check_connection`. Ожидаемый результат: строка Connection OK» |
| Команды и пути только в code-блоках | `config/config.ini` |
| Разбор ошибки рядом с шагом | «Connection refused - сервер недоступен: проверьте адрес и порт» |
| Версии и требования явно | «требуется Python 3.10 и выше» |

### 03.06. Technical Strict

| Technique | Example |
|--------|--------|
| Идентификаторы требований с иерархией | `FR-001`, `FR-001.1`, `NFR-002` |
| Фиксированная модальность | «должна», «допускается», «запрещено» |
| Измеримый критерий в каждом требовании | «не более чем за 2 секунды» |
| Критерии приемки отдельным блоком | «Критерий приемки: сценарий из раздела 05.02 выполняется без отклонений» |
| Один термин для одного понятия | глоссарий в начале документа |

---

## 04. Dictionary Enrichment

*Mandatory.*

The enrichment mechanism is in `human_text_standards.md`, 05.04. Adding an entry: a technique or phrase - into the general section or a style section; the example - short and real; on conflict with the denylist, the denylist takes priority.

---

## 05.01. Related Documents

| Document | Relation |
|----------|-------|
| `human_text_standards.md` | Main document: genres, styles, method, enrichment mechanism (05.04) |
| `human_text_dict_standards.md` | Paired denylist: what is banned; here - what to replace it with |
| `human_text_dict_ai_standards.md` | Paired denylist: AI text markers; Section 14 bans replacements not from here |
| `project_standards.md` | Text micro level (04.03), package editing (07.05) |
| `doc/specs/text_overrides.md` | Override template: domain canon lexicon on top of this dictionary |

---

## 05.02. Versioning

Versioning of the standards package is unified for all package documents. The versioning policy, registry, and routing map are in `doc/standards/_index_standards.md`. A package version bump is performed only on explicit user request.
