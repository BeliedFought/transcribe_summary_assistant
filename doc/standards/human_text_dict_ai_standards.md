# Human Text AI Dictionary Standards. Version 5.2.0

Denylist of phrases and structures that give away generated text: opening introductions, modal hedges, motivational cliches, truisms, parallelisms, calques from English. This document supplements `human_text_standards.md` and applies on top of it together with the other package dictionaries. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

Style abbreviations and applicability statuses - `human_text_standards.md`, 03.09: РЛ - conversational light, РС - conversational strict, ДЛ - business light, ДС - business strict, ТЛ - technical light, ТС - technical strict; statuses: запрет, ограничено, норма.

---

## Table of Contents

**01. Purpose and Application Order**

**02. Applicability by Styles**

**03. Opening Introductions**

**04. Modal Hedges**

**05. Motivational Cliches and Marketing Stamps**

**06. Truisms and Formulaic Conclusions**

**07. Pseudo-Socratic and Rhetorical Constructions**

**08. Parallelisms**

**09. Calques from English**

**10. Pseudo-Therapeutic Phrases**

**11. Inanimate Subject**

**12. Honesty Self-Labeling**

**13. AI Lexicon and Formulaic Finales**

**14. Forbidden Replacements**

**15. Do Not Ban: Logical Connectors and Calibration**

**16. Dictionary Enrichment**

**17. Relations and Versioning:** 17.01 Related Documents - 17.02 Versioning

---

## 01. Purpose and Application Order

*Mandatory.*

AI text markers are phrases that language models reproduce more often than people: an averaged register, false involvement, overcaution, calques of English logic. The dictionary serves the goal "the text must not read as generated": the user recognizes awkward agent text precisely by these patterns.

Order of fixing:

1. A marker from the table - the replacement from the "Replacement" column
2. No replacement - rebuild the sentence or remove the phrase entirely
3. Take the replacement from the canon lexicon (`human_text_allowlist_standards.md`) or build anew; Section 14 bans treating a marker with a related marker
4. Style status - per the marks in Section 02 and the "Deviations" column

---

## 02. Applicability by Styles

*Mandatory.*

The applicability matrix is common to the package: it lives in `human_text_standards.md`, 03.09, and is not duplicated here.

Hedging in РС, ДЛ, ДС, and ТС is limited: allowed only under real uncertainty of fact; on established facts hedging is banned in all styles (Section 04, Section 15).

---

## 03. Opening Introductions

*Mandatory.*

Status: banned in all styles. Universal topic openings instead of moving to the point.

| Phrase | Replacement |
|--------|--------|
| в современном мире, в современном обществе | удалить; начать с сути |
| в эпоху цифровизации, в эпоху чего-либо | удалить |
| сегодня, как никогда | удалить |
| все чаще | дать частоту фактом |
| по мнению экспертов | назвать источник или удалить |
| специалисты отмечают | назвать источник или удалить |
| вопрос стоит особенно остро | удалить; дать факт |
| нельзя не отметить | удалить; дать факт |

---

## 04. Modal Hedges

*Mandatory.*

Status: banned in РЛ and ТЛ; limited in РС, ДЛ, ДС, and ТС - only under real uncertainty. Habitual hedging on hard facts shifts responsibility and reads as machine overcaution.

| Phrase | Replacement | Deviations |
|--------|--------|------------|
| может стать, может повлиять | дать факт или убрать модальность | в остальных стилях при реальной неопределенности |
| способен обеспечить | обеспечить | |
| призван решить | решает | |
| позволяет достичь | дает | в ТЛ и ТС допустимо о функциях системы |
| потенциально возможно | возможно | |
| как правило, обычно, зачастую | удалить или указать условие | допустимо при реальной вариативности, в остальных - запрет |
| в определенной степени | удалить или дать меру | |
| в некотором роде | удалить | |
| теоретически возможно | возможно | |

---

## 05. Motivational Cliches and Marketing Stamps

*Mandatory.*

Status: banned in all styles. Empty aggrandizement without substance.

| Phrase | Replacement |
|--------|--------|
| раскрыть потенциал | удалить или дать конкретику |
| вывести на новый уровень | удалить или дать факт |
| открывает новые горизонты | удалить |
| открывает новые возможности | дать перечень возможностей |
| комплексный подход | дать состав: что именно включается |
| индивидуальный подход | указать конкретику (словарь стоп-слов, раздел 09) |
| инновационное решение | удалить или назвать технологию |
| revolutionary, революционный | удалить или дать факт |
| идеальное решение | удалить |
| экономия времени и средств | дать число |
| под ключ | дать состав работ |

---

## 06. Truisms and Formulaic Conclusions

*Mandatory.*

Status: banned in all styles. False authority props and completion formulas that retell the text.

| Phrase | Replacement |
|--------|--------|
| стоит отметить, что | удалить; факт - сразу |
| важно отметить, важно понимать, важно учитывать | удалить; факт - сразу |
| следует отметить, следует признать | удалить |
| необходимо подчеркнуть | удалить |
| самое важное - это | удалить |
| вот ключевой вывод | удалить |
| первый шаг - это | удалить |
| по своей сути | удалить |
| в конечном счете, в конечном итоге | удалить или в итоге |
| подводя итог | удалить; закончить фактом или действием |
| таким образом (как открывашка финала) | удалить |
| можно сделать вывод | удалить; дать вывод |
| резюмируя | удалить |

---

## 07. Pseudo-Socratic and Rhetorical Constructions

*Mandatory.*

Status: banned in all styles. Imitation of dialogue and involvement.

| Construction | Replacement |
|--------------|--------|
| вопрос к себе с коротким ответом: «Зачем? Потому что.» | развернуть в предложение |
| риторический вопрос в начале раздела | удалить; дать утверждение |
| «И что это меняет? Меняет все.» | дать факт изменений |
| «Не переключайтесь», «оставайтесь с нами» | удалить |
| серия коротких односоставных предложений-кивков: «Коротко. Точно. По делу.» | обычное предложение |

---

## 08. Parallelisms

*Mandatory.*

Status: banned in all styles. The construction «не просто X, а Y» and its relatives are the most frequent marker of agent text.

| Construction | Replacement | Deviations |
|--------------|--------|------------|
| не просто X, а Y | дать X и Y прямо | запрет везде |
| это не X, это Y | дать X и Y прямо | живая речь («это не может не радовать») маркером не считается |
| не только X, но и Y | X и Y | допустимо, когда оба элемента несут самостоятельный факт |
| триада «X, Y и Z» в каждом абзаце | менять длину перечислений | ограничение на ритм, не запрет перечислений |
| однотипные заголовки секций одной длины | менять структуру заголовков | ограничение на ритм |

---

## 09. Calques from English

*Mandatory.*

Status: banned in all styles. A literal translation of English phrases; the Russian reader winces, the editor corrects it immediately.

| Calque | Replacement |
|--------|--------|
| в конце дня (at the end of the day) | в итоге |
| думать за пределами коробки (outside the box) | искать нестандартные решения |
| это меняет игру (game-changer) | удалить или дать факт |
| погрузимся в тему, глубокое погружение (dive in, deep dive) | рассмотрим, подробный разбор |
| данный подход позволяет | этот подход дает |
| делает разницу (makes a difference) | меняет результат |
| играть ключевую роль | дать факт роли |
| мощный инструмент | удалить или дать возможность |
| seamless, бесшовный | удалить или описать поведение |
| леверидж, leverage | рычаг, влияние |
| фича (в человеческом тексте) | возможность, функция |

---

## 10. Pseudo-Therapeutic Phrases

*Mandatory.*

Status: banned in all styles. Imitation of care instead of help.

| Phrase | Replacement |
|--------|--------|
| ты не ошибаешься, что так чувствуешь | удалить; дать решение |
| это не слабость | удалить |
| ты все еще здесь, ты настоящий | удалить |
| сам факт этого - уже тихое подтверждение | удалить |
| каждый на своем пути встречает трудности | удалить; дать решение |

---

## 11. Inanimate Subject

*Mandatory.*

Status: banned in all styles; limited in ТС. An object or abstraction in the role of an actor with a metaphorical verb of intention, emotion, or evaluation: a work "подчеркивает", a document "демонстрирует заботу", a system "стремится".

| Construction | Replacement |
|--------------|--------|
| исследование подчеркивает, работа демонстрирует | назвать автора и факт: «Авторы показали (Mnih et al., 2016)» |
| система стремится обеспечить | дать факт работы: «система повторяет попытку три раза» |
| документ отражает заботу о пользователе | перестроить: назван признак |
| отчет подтверждает эффективность | дать число из отчета |

Deviations in ТС: functional wording («система проверяет», «модуль выполняет») is the genre norm, not a marker; the marker is only metaphorical attribution of intention and evaluation.

---

## 12. Honesty Self-Labeling

*Mandatory.*

Status: banned in all styles. The text awards itself a virtue instead of presenting facts.

| Phrase | Replacement |
|--------|--------|
| честный список, честный разбор, объективный разбор | дать методику: как проверялось |
| без воды, без прикрас | удалить; дать факт |
| буду (с вами) откровенен, если честно | удалить; дать факт |
| это не очередной X | дать отличие от X |
| без преувеличения | удалить; дать проверяемое утверждение |

---

## 13. AI Lexicon and Formulaic Finales

*Mandatory.*

Status: banned in all styles. Marker words of generation and template endings.

| Phrase | Replacement |
|--------|--------|
| углубиться в тему, погрузиться в тему | рассмотреть |
| полотно, мозаика, ландшафт (о тексте, рынке, отрасли) | дать структуру: перечисление |
| экосистема (не про программные продукты) | дать состав |
| путешествие (о процессе) | удалить |
| открывает двери | удалить или дать возможность |
| сердцем системы является | дать главный элемент |
| играет важную роль (см. также словарь стоп-слов, раздел 07) | указать роль фактом |
| исследования показывают (без источника) | назвать источник или удалить |
| несмотря на трудности, у технологии большое будущее | заменить следующим действием или вопросом |
| надеюсь, это поможет | удалить; закончить делом |
| если остались вопросы, обращайтесь | норма ответа поддержки (РС, ДЛ); в остальных - удалить |

---

## 14. Forbidden Replacements

*Mandatory.*

A marker replaced with a related marker remains a marker. Rule: the replacement comes from the canon lexicon or the sentence is rebuilt.

| Instead of | Not allowed to use | Reason |
|--------|-----------|---------|
| очень важно | крайне важно, чрезвычайно важно | усилитель заменен усилителем |
| стоит отметить | важно подчеркнуть, следует отметить | трюизм заменен трюизмом |
| в современном мире | в сегодняшнем мире, в наше время | та же вводная |
| уникальный | исключительный, непревзойденный | оценка заменена оценкой |
| играет ключевую роль | имеет первостепенное значение | та же пустая роль |
| раскрыть потенциал | unlock потенциал, максимально раскрыть возможности | клише заменено клише |
| подводя итог | резюмируя сказанное | тот же формульный вывод |

---

## 15. Do Not Ban: Logical Connectors and Calibration

*Mandatory.*

The dictionary bans decorations and stamps, but not the logic of the text. The following means are not markers and are not subject to correction:

- causal: потому что, так как, следовательно, отсюда, поэтому
- conditional: если - то, при условии что, только если
- contrasts: в отличие от, тогда как, а не
- clarifications: то есть, в частности, например, именно
- sequences: сначала - затем - в итоге
- confidence calibration: вероятно, возможно, как правило - under real uncertainty of fact

Principle: constructions that set relations between objects (cause, boundary, condition, hierarchy) are thinking tools; banning them breaks the meaning. Modality is banned only where it serves as overcaution on established facts (Section 04).

---

## 16. Dictionary Enrichment

*Mandatory.*

The enrichment mechanism is in `human_text_standards.md`, 05.04. Dictionary specifics: new markers appear as models and prompt modes change; when a recurring phrase is found in other people's and own agent texts - an entry by the category rules, with an example and a replacement. The source is stated: a catalog repository, an article, or a user correction.

---

## 17.01. Related Documents

| Document | Relation |
|----------|-------|
| `human_text_standards.md` | Main document: genres, styles, method, applicability statuses (03.09), enrichment mechanism (05.04) |
| `human_text_dict_standards.md` | Paired denylist: officialese, filler, amplifiers, pleonasms |
| `human_text_allowlist_standards.md` | Canon lexicon: source of allowed replacements |
| `project_standards.md` | Text micro level (04.03), package editing (07.05) |
| `doc/specs/text_overrides.md` | Override template: domain prohibitions on top of this dictionary |

---

## 17.02. Versioning

Versioning of the standards package is unified for all package documents. The versioning policy, registry, and routing map are in `doc/standards/_index_standards.md`. A package version bump is performed only on explicit user request.
