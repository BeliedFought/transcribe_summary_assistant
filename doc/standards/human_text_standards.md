# Human Text Standards. Version 5.0.0

Canon for human-facing texts written by an AI agent: the registry of document types, the speech style matrix, the writing and self-check method, the composition of the dictionaries, and the repo override mechanism. This document supplements `project_standards.md` and applies on top of it. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

The micro level of text (language, the letter е without diacritics, hyphen instead of dash, naming, placeholders) is canonized in `project_standards.md`, 04.03. This document defines the document and speech level: genre, structure, style. The rules of 04.03 always apply and are not overridden by this document.

---

## Table of Contents

**01. Scope and Terms:** 01.01 Scope - 01.02 Boundary with Section 04.03 - 01.03 Terms

**02. Document Type Registry:** 02.01 Genre Selection Rule - 02.02 User Guide - 02.03 Functional Requirements - 02.04 Business Message - 02.05 Interface Texts - 02.06 Policy (Regulation) - 02.07 Genres Outside the Registry

**03. Style Matrix:** 03.01 Axes and Style List - 03.02 Style Parameters - 03.03 Conversational Light - 03.04 Conversational Strict - 03.05 Business Light - 03.06 Business Strict - 03.07 Technical Light - 03.08 Technical Strict - 03.09 Dictionary Applicability by Style

**04. Writing Method:** 04.01 Process - 04.02 Chat Style - 04.03 Invariants - 04.04 Style Change on Request

**05. Dictionaries and Levels:** 05.01 Package Dictionary Composition - 05.02 Application Order - 05.03 Repo Override - 05.04 Dictionary Enrichment

**06. Self-Check Checklist**

**07. Antipatterns**

**08. Sources and Tools:** 08.01 Checking Tools - 08.02 Style Guides and Reference Books - 08.03 Agent Rule Sets - 08.04 Automation Outlook

**09. Relations and Versioning:** 09.01 Related Documents - 09.02 Versioning

---

## 01.01. Scope

*Mandatory.*

The document covers all human-readable texts the agent creates: documentation and user instructions, functional requirements and specifications, business messages and announcements, answers to user questions, user-facing messages in the interface, and the agent's communication with the user in chat. It does not cover: executable code and program string literals; agent navigation documents (indexes, `AGENTS.md` - `index_nav_standards.md`); change requests (CR - `change_request_standards.md`).

User-facing strings embedded in code are human text, not program literals: interface labels, help headings and content, hints, error messages, instruction texts, export legends, chat answers. They fall under the standard on par with standalone documents. The exclusion for "program string literals" covers only service strings not addressed to a human: keys, codes, technical identifiers, debug strings.

---

## 01.02. Boundary with Section 04.03

*Mandatory.*

Separation of levels:

| Level | What it governs | Canon |
|----------|----------------|-------|
| Micro | Language, the letter е, hyphen instead of dash, ellipses, emoji, naming, placeholders, case | `project_standards.md` (04.03) |
| Document and speech | Genre, structure skeleton, speech style, dictionaries of words and phrases | This document |

On conflict, Section 04.03 takes priority. Example: the conversational light style allows lively turns of phrase, but exclamation marks, emoji, the letter е with diacritics, and dashes are banned by 04.03 itself - the 04.03 restriction is stronger.

---

## 01.03. Terms

*Mandatory.*

- **Genre** - a document type from the registry in Section 02; it determines the structure skeleton and the default style
- **Style** - a combination of register (conversational, business, technical) and tone (light, strict); six styles in total
- **Anchor sample** (anchor) - a reference fragment of a style that sets the voice; rules fix prohibitions, the anchor sets the sound
- **Stop list** - a list of words and phrases not allowed in the text (denylist)
- **Canon lexicon** - preferred words, phrases, and constructions (allowlist)
- **AI text markers** - turns of phrase and structures typical of generated text that give it away
- **Override** - a repo-specific addition or a pinpoint cancellation of dictionary rules in `doc/specs/text_overrides.md`

---

## 02.01. Genre Selection Rule

*Mandatory.*

1. The genre is determined by the text structure and the default style; the user can override the style with one phrase without changing the genre
2. The user set the genre explicitly - that genre applies
3. The genre is not set - the agent determines it from the task (what the reader must get: perform an action, make a decision, learn a status)
4. The genre is not in the registry - take the closest one by purpose; when in doubt between two genres - ask the user
5. Extending the registry - only in this document in the hub (by the package editing rules, `project_standards.md`, 07.05)

---

## 02.02. User Guide

*Mandatory.*

- **Purpose:** step-by-step task execution by the user with their own hands
- **Audience:** a user without access to code or the project's internal workings
- **Default style:** conversational light (03.03); for advanced instructions - technical light (03.07)
- **Skeleton:**
  1. Что получится в итоге - the result in 1-3 sentences
  2. Что нужно перед началом - access, accounts, versions, restrictions
  3. Шаги - numbered; a step = action + command or click + expected result (what the user will see on screen)
  4. Проверка результата - how to make sure everything works
  5. Если не получилось - 2-4 common errors and actions for each
- **Antipatterns:** a step without an expected result; "see the code" or "see the documentation" instead of a description; retelling the internal implementation; important information only in a screenshot (the text duplicates what is visible in the screenshot)

---

## 02.03. Functional Requirements

*Mandatory.*

- **Purpose:** capturing system requirements for development and acceptance
- **Audience:** developer, analyst, customer; a reader who will verify compliance
- **Default style:** technical strict (03.08)
- **Skeleton:**
  1. Обзор - what the system is, boundaries, and context
  2. Термины - domain glossary
  3. Функциональные требования - with identifiers (`FR-001`, `FR-001.1`); one requirement - one verifiable function
  4. Нефункциональные требования - performance, reliability, security (`NFR-001`)
  5. Ограничения - stack, environment, regulatory conditions
  6. Критерии приемки - how each requirement is verified
- **Wording rules:** fixed modality - «должна», «допускается», «запрещено»; an evaluation is allowed only with a measurable criterion («открывает список не более чем за 2 секунды», not «быстро»)
- **Antipatterns:** immeasurable requirements («система должна быть удобной»); requirements without identifiers; mixing a requirement with a solution (a requirement fixes what, not how); numbering without hierarchy

---

## 02.04. Business Message

*Mandatory.*

- **Purpose:** informing, requesting, announcing, explaining a situation
- **Audience:** a specific recipient - a colleague, a customer, a user group
- **Default style:** business light (03.05); for official notifications - business strict (03.06)
- **Skeleton:**
  1. Суть в первом абзаце - what happened, what is proposed, what changes
  2. Детали и причины - details and reasons
  3. Что нужно от получателя - action and deadline
  4. Куда писать вопросы - where to ask questions
- **Antipatterns:** a long introduction before the point; an action without a deadline; no action (the message asks nothing of the recipient); retelling the whole story instead of the point

---

## 02.05. Interface Texts

*Mandatory.*

- **Purpose:** labels of controls, help, hints, error messages, screen microtext
- **Audience:** a user at the screen, without access to code
- **Default style:** conversational light (03.03); for technical hints - technical light (03.07)
- **Skeleton:** label - a noun naming the action; hint - one meaning in one or two sentences; error - what happened and what to do
- **Wording rules:** one concept - one name across the screen, help, and instruction; domain concepts are explained before first use; table names, field names, internal system names, codes and enum values, and config keys do not appear in the text (`project_standards.md`, 04.03)
- **Antipatterns:** a wall of text in a hint; a table or field name instead of a human word; different words for one object in a label, help, and instruction
- Output contract, roles, keys, and interface layout - `console_ui_standards.md`; this section defines wording

---

## 02.06. Policy (Regulation)

*Mandatory.*

- **Purpose:** establish the mandatory process order, applicability criteria, limits, and metrics
- **Audience:** departments and employees affected by the process; the reviewer
- **Default style:** business strict (03.06)
- **Skeleton:**
  1. Назначение и область действия - purpose and scope
  2. Термины и сокращения - terms and abbreviations
  3. Критерии применения и лимиты - applicability criteria and limits
  4. Процесс и матрица ролей - process and role matrix
  5. Метрики с целевыми ориентирами - metrics with targets
  6. Ответственность и контроль - responsibility and control
  7. Порядок утверждения, версии и пересмотра - approval, versions, and revision
- **Wording rules:** fixed modality («должен», «допускается», «запрещено»); an abbreviation is explained at first use (`project_standards.md`, 04.03); one object - one name throughout the document; table names, field names, and internal system names do not appear in the text (`project_standards.md`, 04.03)
- **Antipatterns:** intensifiers and evaluations without evidence; different names for one department; unexplained abbreviations; a "target" column without numbers; duplicating metrics across sections

---

## 02.07. Genres Outside the Registry

*Mandatory.*

| Text type | Structure canon | Style and dictionaries |
|-------------|-----------------|------------------|
| README, repository descriptions | `repo_info_doc_standards.md` | this document (03, 05) |
| Software installation documents | `software_doc_standards.md` | this document (03, 05) |
| Change requests (CR) | `change_request_standards.md` | business light or strict (03.05, 03.06) |
| Project specifications | `project_standards.md` (07.02) | technical strict (03.08) for production specs |

---

## 03.01. Axes and Style List

*Mandatory.*

Style = register x tone:

| | Light tone | Strict tone |
|---|---|---|
| **Conversational register** | 03.03 conversational light | 03.04 conversational strict |
| **Business register** | 03.05 business light | 03.06 business strict |
| **Technical register** | 03.07 technical light | 03.08 technical strict |

- The register selects the reader's dictionary: everyday, business, or domain-technical
- The tone selects distance and freedom: light - lively and short, strict - neutrally precise, without liberties
- Light does not mean careless: the rules of 04.03 and the dictionaries (Section 05) apply in all six styles

---

## 03.02. Style Parameters

*Mandatory.*

Each style is described by a fixed set of parameters - measurable rules, not adjectives:

| Parameter | What it fixes |
|----------|----------------|
| Forms of address | How the text addresses the reader: «вы», impersonal |
| Sentence | Average and maximum length, allowed constructions |
| Paragraph | Number of sentences |
| Vocabulary | Acceptability of terms and jargon, explanation of terms |
| Analogies | Acceptability of comparisons and everyday examples |
| Hedging | Acceptability of uncertainty («возможно», «как правило») |
| Structure | Ratio of prose, lists, tables, steps |
| Stop list | Additions to the common dictionaries, characteristic agent errors |

---

## 03.03. Conversational Light

*Mandatory.*

Default genres: user guide, FAQ.

| Parameter | Value |
|----------|----------|
| Forms of address | «вы» |
| Sentence | up to 15 words, simple constructions |
| Paragraph | 1-3 sentences |
| Vocabulary | everyday vocabulary; a term only if widely known or explained immediately |
| Analogies | yes, from everyday life, one per concept |
| Hedging | minimal; an instruction speaks directly |
| Structure | short paragraphs, numbered steps, a question heading is allowed |

Stop list: all officialese (stop-word dictionary, Section 03); unexplained terms; chains of subordinate clauses.

Agent errors: imitating "friendliness" with exclamations and emoji (banned by 04.03); sycophancy («отличный вопрос»); fussy turns of phrase («не за горами», «давайте разберемся»).

Anchor sample (restoring access):

```
Вернуть доступ можно за пару минут.

1. На странице входа нажмите «Забыли пароль».
2. Введите почту, на которую регистрировались.
3. Откройте письмо и нажмите «Создать новый пароль».

Письмо приходит примерно через минуту. Если письма нет - загляните
в папку «Спам»: фильтры иногда отправляют туда автоматические письма.
```

---

## 03.04. Conversational Strict

*Mandatory.*

Default genres: support answer, explanation of a failure or error, answer to a user question.

| Parameter | Value |
|----------|----------|
| Forms of address | «вы» |
| Sentence | up to 15 words |
| Paragraph | 1-3 sentences |
| Vocabulary | simple vocabulary, precise wording; a term with an explanation |
| Analogies | selective, not for explaining facts |
| Hedging | only under real uncertainty; an established fact is stated directly |
| Structure | scheme: point - details - action |

Stop list: sycophancy and emotiveness; evaluative judgments without facts; AI text markers (the whole AI marker dictionary by matrix 03.09; priority sections - 03-06).

Agent errors: imitation of involvement («полностью понимаю ваше разочарование»); promises without authority («это точно больше не повторится»).

Anchor sample (support answer about a failure):

```
Проверили: сбой был на нашей стороне, доступ восстановлен в 14:40.

Что произошло: обновление базы началось раньше планового времени
и блокировало вход около 40 минут. Данные пользователей не затронуты.

Если вход по-прежнему не проходит - выйдите из аккаунта и войдите
заново. Не поможет - ответьте на это письмо, разберемся в тот же день.
```

---

## 03.05. Business Light

*Mandatory.*

Default genres: business message, announcement, letter to a colleague or customer.

| Parameter | Value |
|----------|----------|
| Forms of address | «вы» to the addressee; greeting per the channel format |
| Sentence | up to 20 words |
| Paragraph | 2-4 sentences |
| Vocabulary | business vocabulary without officialese |
| Analogies | none |
| Hedging | moderate; obligations without ambiguity |
| Structure | point in the first paragraph, details, action and deadline, contact for questions |

Stop list: officialese (the whole stop-word dictionary by matrix 03.09; priority sections - 03-04); truisms and formulaic conclusions (AI marker dictionary, Section 06).

Agent errors: bureaucratic openings («Настоящим сообщаем Вам»); recipient action without a deadline; a final retelling of the whole letter.

Anchor sample (letter about postponing deadlines):

```
Добрый день.

Сообщаю: сдачу отчета переносим с 10 на 14 июня. Причина - заказчик
прислал правки по методике, их нужно учесть в финальной версии.

Что нужно от вас: замечания по новой редакции методики до 12 июня,
чтобы уложиться в срок.

Если перенос ломает ваши планы - напишите, обсудим формат.
```

---

## 03.06. Business Strict

*Mandatory.*

Default genres: official notification, policy, regulation, terms of service.

| Parameter | Value |
|----------|----------|
| Forms of address | impersonal or «вы» in the official form |
| Sentence | up to 25 words; complex constructions with unambiguous relations are allowed |
| Paragraph | 3-5 sentences or numbered clauses |
| Vocabulary | business and legal vocabulary is allowed; part of the officialese is the genre norm (marked in the stop-word dictionary) |
| Analogies | none |
| Hedging | minimal; dates and conditions are stated unambiguously |
| Structure | numbered clauses, cross-references to clauses |

Stop list: filler and introductory phrases, amplifiers, truisms - banned (stop-word dictionary, Sections 05-06; AI marker dictionary, Section 06); officialese - per dictionary marks.

Agent errors: mixing registers (legal precision mixed with colloquialism); vague dates («в ближайшее время»).

Anchor sample (notification about changed terms):

```
Уведомляем об изменении условий обслуживания с 01.10.2026.

1. Комиссия за перевод между своими счетами отменяется.
2. Комиссия за снятие средств в банкоматах сторонних банков
   устанавливается в размере 1%, минимум 100 рублей.
3. Полная редакция условий опубликована по адресу example.com/terms.

Изменения применяются к договорам, действующим на дату вступления
изменений. До 30.09.2026 применяются прежние условия.
```

---

## 03.07. Technical Light

*Mandatory.*

Default genres: guide, administrator manual, instruction for an experienced user.

| Parameter | Value |
|----------|----------|
| Forms of address | «вы» + imperative («откройте», «запустите») |
| Sentence | up to 20 words |
| Paragraph | 1-3 sentences |
| Vocabulary | domain terms are allowed; explained at first use; commands and paths in code blocks |
| Analogies | none; input and output examples instead |
| Hedging | none; a step either succeeds or returns an error |
| Structure | steps by the scheme: action - command - expected result |

Stop list: officialese (the whole stop-word dictionary by matrix 03.09; priority sections - 03-04); passive voice in steps; describing internal implementation instead of user actions.

Agent errors: a step without an expected result; a command without saying where to run it from; retelling code instead of actions.

Anchor sample (setting up a connection):

```
1. Откройте файл config/config.ini.
2. Впишите адрес сервера в параметр server_host.
3. Запустите проверку подключения:

   python -m app.check_connection

4. Дождитесь строки Connection OK. Если вывод - Connection refused,
   сервер недоступен: проверьте адрес и порт, затем повторите шаг 3.
```

---

## 03.08. Technical Strict

*Mandatory.*

Default genres: functional requirements, technical specification, production specs.

| Parameter | Value |
|----------|----------|
| Forms of address | impersonal («система должна», «модуль выполняет») |
| Sentence | up to 25 words |
| Paragraph | numbered clauses with identifier hierarchy |
| Vocabulary | domain terminology, a single glossary; synonymy of terms is banned (04.03, canonical naming) |
| Analogies | banned |
| Hedging | banned; fixed modality: «должна», «допускается», «запрещено» |
| Structure | requirements with identifiers (`FR-NNN`, `NFR-NNN`), acceptance criteria |

Stop list: analogies, evaluations without a measurable criterion, hedging - banned; part of the officialese is the genre norm (marked in the stop-word dictionary); AI markers - banned (AI marker dictionary).

Agent errors: immeasurable requirements; different terms for one concept; requirements without acceptance criteria.

Anchor sample (fragment of authorization requirements):

```
FR-001. Система выполняет аутентификацию пользователя по паре
логин и пароль.

FR-001.1. Пароль хранится в виде хэша bcrypt, стоимость - 12.
FR-001.2. При пяти неуспешных попытках входа подряд аккаунт
блокируется на 15 минут.
FR-001.3. Сообщение об ошибке не раскрывает, какой из параметров
введен неверно.

Критерий приемки: сценарий из раздела 05.02 выполняется без
отклонений.
```

---

## 03.09. Dictionary Applicability by Style

*Mandatory.*

Style abbreviations: РЛ - conversational light, РС - conversational strict, ДЛ - business light, ДС - business strict, ТЛ - technical light, ТС - technical strict.

Status values: **запрет** - not allowed; **ограничено** - allowed under the conditions specified in the dictionary; **норма** - allowed as a genre norm, not corrected during self-check.

Summary matrix by dictionary categories (detailed marks for individual words are in the dictionary tables):

| Category | РЛ | РС | ДЛ | ДС | ТЛ | ТС |
|-----------|----|----|----|----|----|----|
| Officialese words (является, данный) | запрет | запрет | запрет | ограничено | запрет | ограничено |
| Officialese phrases (в целях, в рамках) | запрет | запрет | запрет | ограничено | запрет | ограничено |
| Filler and introductory phrases | запрет | запрет | запрет | запрет | запрет | запрет |
| Amplifiers | запрет | запрет | запрет | запрет | запрет | запрет |
| Evaluations without evidence | запрет | запрет | запрет | запрет | запрет | запрет |
| Pleonasms | запрет | запрет | запрет | запрет | запрет | запрет |
| Corporate and advertising cliches | запрет | запрет | запрет | запрет | запрет | запрет |
| Newspaper and everyday cliches | запрет | запрет | запрет | запрет | запрет | запрет |
| Time parasites | запрет | запрет | запрет | запрет | запрет | запрет |
| Uncertainty (около, ряд, некий) | запрет | запрет | запрет | ограничено | запрет | ограничено |
| Modal softeners (можно, следует) | ограничено | ограничено | ограничено | норма | ограничено | норма |
| Pretentiousness and pseudo-terminology | запрет | запрет | запрет | запрет | запрет | запрет |
| Structural limits (participles, genitive chains) | ограничено | ограничено | ограничено | ограничено | ограничено | ограничено |
| AI opening introductions | запрет | запрет | запрет | запрет | запрет | запрет |
| Motivational cliches, marketing stamps | запрет | запрет | запрет | запрет | запрет | запрет |
| Truisms and formulaic conclusions | запрет | запрет | запрет | запрет | запрет | запрет |
| Pseudo-Socratic and rhetorical constructions | запрет | запрет | запрет | запрет | запрет | запрет |
| Parallelisms «не просто X, а Y» | запрет | запрет | запрет | запрет | запрет | запрет |
| Calques from English | запрет | запрет | запрет | запрет | запрет | запрет |
| Pseudo-therapeutic phrases | запрет | запрет | запрет | запрет | запрет | запрет |
| Inanimate subject (документ подчеркивает) | запрет | запрет | запрет | запрет | запрет | ограничено |
| Honesty self-labeling (без воды, честный разбор) | запрет | запрет | запрет | запрет | запрет | запрет |
| AI lexicon and formulaic finales | запрет | запрет | запрет | запрет | запрет | запрет |
| Modal hedges | запрет | ограничено | ограничено | ограничено | запрет | ограничено |

Hedging is allowed only under real uncertainty of fact; on established facts it is banned in all styles (AI marker dictionary, Section 04 and Section 15).

---

## 04.01. Process

*Mandatory.*

The agent's workflow for a human-facing text:

1. Determine the genre (Section 02) - from the task or an explicit user instruction
2. Name the reader specifically: who they are, what they already know, what they must achieve; «пользователь без доступа к коду» and «разработчик смежной команды» are different readers
3. Determine the style: the genre default or the style specified by the user
4. Build the text by the genre skeleton; the main point goes at the start of the document and each section
5. Run the self-check checklist (Section 06) and the dictionaries (Section 05)

---

## 04.02. Chat Style

*Mandatory.*

- The base chat style of the agent is business light (03.05)
- The agent adjusts the register to the user's message style: if the user writes conversationally, the agent lowers formality within business light, not below it
- Strict styles (03.06, 03.08) in chat - for formal topics: requirements, notifications, final wording
- The rules of 04.03 and the dictionaries apply in chat on par with documents
- The answer is built on the substance of the request; opening phrases («Отличный вопрос», «Конечно») are banned

---

## 04.03. Invariants

*Mandatory.*

Style controls form, not content. No style cancels:

- facts, numbers, versions, commands, paths - accuracy and completeness are preserved
- requirement identifiers and section references
- the rules of 04.03 (hyphen, е without diacritics, no emoji, no ellipses)
- the dictionaries of Section 05 with the statuses of 03.09
- canonical naming: one term for one concept throughout the text
- human-facing text without table names, field names, internal system names, codes and enum values, config keys (`project_standards.md`, 04.03)

---

## 04.04. Style Change on Request

*Mandatory.*

- The user names the style or direction: «строже» - same register, strict tone; «проще» - conversational light; «официально» - business strict; «по-технически» - technical register
- Rewriting keeps the same content: facts and data structure do not change, only the form changes
- A style change does not require renegotiating the genre if the skeleton is preserved

---

## 05.01. Package Dictionary Composition

*Mandatory.*

| File | Type | Purpose |
|------|-----|------------|
| `human_text_dict_standards.md` | denylist | stop words of Russian text: officialese, filler, amplifiers, evaluations, pleonasms |
| `human_text_dict_ai_standards.md` | denylist | AI text markers: opening introductions, cliches, truisms, parallelisms, calques; forbidden replacements |
| `human_text_allowlist_standards.md` | allowlist | canon lexicon: preferred phrases and constructions by style |

Each denylist entry contains: a word or phrase, a replacement, a status by style (03.09); allowlist entries are "technique - example" pairs without replacements or statuses (format - `human_text_allowlist_standards.md`).

---

## 05.02. Application Order

*Mandatory.*

1. When writing - the rules of this document (genre, style, method); full dictionaries are not loaded into context before writing
2. During self-check - load the three dictionaries and the repo override (05.03), run the text through the checklist (Section 06); if the ru-text skill is available, a run through its antipattern catalog is mandatory (08.01), the skill's typography does not apply (caveat in 08.01); if the skill is unavailable - check against the package dictionaries and the checklist (Section 06)
3. Fixing what is found: a stop word - the replacement from the table; no replacement in the table - rebuild the sentence; deletion test: removed it and the meaning is intact, so delete it
4. The marks "ограничено" and "норма" are checked against the conditions in the dictionary, not against a general feeling

---

## 05.03. Repo Override

*Mandatory.*

Repo-specific text rules are fixed in `doc/specs/text_overrides.md` of the derivative repository; the reference template is in the hub at `doc/specs/text_overrides.md`. The standards package is read-only in derivative repositories, so domain vocabulary and industry prohibitions live in the override, not in dictionary edits.

Rules:

- Priority: the repo override is above the package dictionaries
- Three entry types: **запретить** (the word is not in the hub stop list), **разрешить** (a pinpoint cancellation of a hub dictionary status for a style or genre), **предпочесть** (domain canon lexicon)
- Each entry names the style or genre it affects; an entry without a style applies to all
- The override supplements and cancels pinpoint rules; rewriting dictionary categories wholesale is banned
- The template in the hub is not filled in: in the hub it is the form reference, filled-in instances exist only in derivative repositories

---

## 05.04. Dictionary Enrichment

*Mandatory.*

Trigger: the user corrected the agent's text manually.

1. The agent compares the correction with the three dictionaries and the override
2. The correction is covered by an existing entry - nothing is proposed
3. The new word is not in the dictionaries - the agent determines the level: a general word - a proposal for the hub dictionary; a domain word - a proposal for the repo override
4. The agent proposes a row in chat: word, replacement, status by style
5. On user confirmation, the entry is added to the dictionary or override

Enrichment follows the same package editing rules as other changes (`project_standards.md`, 07.05).

---

## 06. Self-Check Checklist

*Mandatory.*

Before handing the text to the user, the agent checks:

- [ ] Genre defined, structure matches the genre skeleton
- [ ] Reader named specifically; the text is addressed to them, not to the agent or developer
- [ ] Style matches the genre default or the explicit user instruction
- [ ] No stop-list words or phrases (style statuses from 03.09 taken into account)
- [ ] No AI text markers or forbidden replacements (the replacement is not the same marker)
- [ ] The text has been run through the ru-text skill antipattern catalog; if the skill is unavailable - check against the package dictionaries and this checklist (05.02, 08.01)
- [ ] Canon lexicon applied: active voice, verb instead of a verbal noun, specifics
- [ ] Every instruction step contains an action and an expected result
- [ ] The main point is at the start of the document and each section
- [ ] Terms are consistent throughout; explained at first use
- [ ] No dashes (U+2014, U+2013), ellipses (U+2026), emoji, letters with diacritics (U+0451, U+0401, including е + U+0308), non-breaking and narrow spaces (U+00A0, U+202F) (04.03)
- [ ] Facts, commands, paths, and identifiers are not distorted by styling
- [ ] Repo override entries taken into account

Three or more findings - rewrite the paragraph or section completely; one or two - fix precisely.

---

## 07. Antipatterns

*Mandatory.*

| Bad | Good | Reason |
|--------|---------|---------|
| Осуществите вход в систему | Войдите в систему | officialese, verbal noun construction |
| Данный модуль является компонентом ядра | Модуль входит в состав ядра | «данный», «является» |
| Стоит отметить, что система позволяет экспорт | Система экспортирует отчеты в CSV и XLSX | truism, abstraction without fact |
| В современном мире безопасность играет ключевую роль | Безопасность: пароли хранятся в виде хэша bcrypt | AI opening, evaluation without fact |
| Это не просто ускоряет работу, а революционизирует ее | Ускоряет загрузку в 3 раза (замер: таблица 04) | parallelism, evaluation without proof |
| Шаг 3. Настройте подключение | Шаг 3. Впишите адрес в `server_host`. Ожидаемый результат: строка Connection OK | step without a result |
| Система должна быть удобной | Система открывает список задач не более чем за 2 секунды | immeasurable requirement |
| Таким образом, мы рассмотрели настройку подключения | конец на действии или факте, без пересказа | formulaic conclusion |

---

## 08.01. Checking Tools

*Mandatory.*

Tools are auxiliary: the canon is the package dictionaries and this document; a tool's result does not cancel the canon. A run through the ru-text skill antipattern catalog, when the skill is available, is a mandatory part of self-checking a human-facing text (05.02, Section 06).

- The ru-text skill (OpenCode) is the primary editing and self-check tool: an antipattern catalog by severity, stop words, and a ru-score quality score 0-10 across five dimensions (typography, language purity, literacy, structure, reader precision). Caveat below
- Glavred (glvrd.ru) - information style, stop words, text scoring
- Orfogrammka (orfogrammka.ru), Gramota.ru (gramota.ru) - spelling, punctuation
- Typographer (typograf.artlebedev.ru) - not used: it inserts dashes and ellipses banned by 04.03

Caveat on ru-text typography: the typography rules of the skill (em dash, en dash in ranges, single-character ellipsis, non-breaking spaces) do not apply - `project_standards.md`, 04.03 applies: hyphen-minus (U+002D) in all positions, no ellipses, no invisible characters. In OpenCode this is additionally fixed by the machine-level override in `~/.config/opencode/AGENTS.md`, which takes precedence over the skill's typography rules. In ru-score, the "Typography" dimension is not counted and its weight is split among the other four dimensions; the final score is a guide, not the canon. The other dimensions (language purity, literacy, structure, reader precision) apply as is.

Caveat on hierarchy: the skill's antipattern catalog and the package dictionaries overlap; when a word status differs, the package dictionaries with style marks (03.09) take priority, then the repo override.

Global override of text norms (OpenCode). For the OpenCode tool, the rules of 04.03 may be duplicated at the agent configuration level: OpenCode reads `~/.config/opencode/AGENTS.md` in all sessions. The caveat is tool-specific - it applies only to OpenCode; other tools use their own configuration. The single source of the norm is `project_standards.md`, 04.03; the machine file states the rules by reference to 04.03 without rewriting the text, so copies do not diverge. The file is not stored in the repository: creating it is a machine setup operation similar to enabling pre-commit (`git config core.hooksPath .githooks`).

---

## 08.02. Style Guides and Reference Books

*Mandatory.*

Sources of the methods on which the dictionaries are built:

- T-J style guide (Maxim Ilyakhov) - maximilyahov.ru/blog/all/tinkoff-bootcamp-5
- "Пиши, сокращай" (Maxim Ilyakhov, Lena Sarycheva) - the infostyle method and stop words
- Rosenthal's reference book - officialese and stamps (Section 140)
- Reference book of the publisher and author (A. E. Milchin) - editorial revision

---

## 08.03. Agent Rule Sets

*Mandatory.*

Rule and dictionary sets for AI agents used in compiling the package dictionaries:

- github.com/talkstream/ru-text - a catalog of Russian text stop words with replacements; deployed as the local ru-text skill (checking tool - 08.01)
- github.com/ilyautov/humanizer-ru - Russian AI text markers, calques, hedges
- github.com/Osmosy/russian-vector - AI pathologies of Russian text, stop words with replacements
- github.com/n1arko/redaktura-skills - officialese, editing order
- github.com/artgas1/infostyle-skill - 15 stop-word categories by the infostyle method
- github.com/johan--/agent-stylebooks - editorial systems for agents (Google, GOV.UK, Microsoft, and others)
- github.com/yzhao062/agent-style - writing rules for coding agents

When an unfamiliar pattern appears - check it against the sources; a new, confirmed one is formatted as a dictionary proposal (Section 05.04).

---

## 08.04. Automation Outlook

*Mandatory.*

Not implemented in the package; addressed on explicit user request:

- Partially covered by the ru-text skill: ru-score is computed by the agent without external services (08.01)
- Control of forbidden characters (dashes U+2014, U+2013, ellipsis U+2026, е with diacritics U+0451, U+0401 and U+0308, non-breaking spaces U+00A0, U+202F) - on the agent via the checklist (06); auto-control at commit is not introduced: a scanner gives false positives on the standards themselves, where the characters are given as prohibition examples
- Converting stop lists to a Vale style and connecting Vale MCP - automatic text checking against stop lists
- A custom OpenCode tool over the Glavred API - per `opencode_tool_standards.md`

Automation limit: Russian morphology (case forms) is covered by regular expressions only partially; the final check is up to the agent.

---

## 09.01. Related Documents

| Document | Relation |
|----------|-------|
| `project_standards.md` | Core standard; text micro level (04.03), source hierarchy (07.06), package editing (07.05) |
| `repo_info_doc_standards.md` | Structure of README and human repository documents; style inside them - per this document |
| `software_doc_standards.md` | Structure of installation documents; style - per this document |
| `console_ui_standards.md` | Output contract and layout; UI wording - genre 02.05 |
| `code_standards.md` | Technical naming (Section 02.01) |
| `change_request_standards.md` | CR genre: structure there, style per this document (02.07) |
| `opencode_tool_standards.md` | Canon for a custom tool when automating checks (08.04) |
| `doc/specs/text_overrides.md` | Dictionary override template (05.03) |
| `human_text_dict_standards.md` | Russian text stop-word dictionary |
| `human_text_dict_ai_standards.md` | AI text marker dictionary |
| `human_text_allowlist_standards.md` | Canon lexicon dictionary |

---

## 09.02. Versioning

Versioning of the standards package is unified for all package documents. The versioning policy, registry, and routing map are in `doc/standards/_index_standards.md`. A package version bump is performed only on explicit user request.
