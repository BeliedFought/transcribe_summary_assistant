# Human Text Dictionary Standards. Version 5.2.0

Denylist of Russian text: officialese, filler, amplifiers, evaluations without evidence, pleonasms. This document supplements `human_text_standards.md` and applies on top of it together with the other package dictionaries. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

Style abbreviations and applicability statuses - `human_text_standards.md`, 03.09: РЛ - conversational light, РС - conversational strict, ДЛ - business light, ДС - business strict, ТЛ - technical light, ТС - technical strict; statuses: запрет, ограничено, норма.

---

## Table of Contents

**01. Purpose and Application Order**

**02. Applicability by Styles**

**03. Officialese and Verbal Noun Constructions**

**04. Officialese Phrases and Prepositions**

**05. Filler and Introductory Constructions**

**06. Amplifiers**

**07. Evaluations without Evidence**

**08. Pleonasms**

**09. Corporate and Advertising Cliches**

**10. Newspaper and Everyday Cliches**

**11. Time Parasites**

**12. Uncertainty**

**13. Modal Softeners**

**14. Pretentiousness and Pseudo-Terminology**

**15. Structural Limits**

**16. Dictionary Enrichment**

**17. Relations and Versioning:** 17.01 Related Documents - 17.02 Versioning

---

## 01. Purpose and Application Order

*Mandatory.*

The dictionary contains words and phrases that weaken the text: those that carry no meaning, replace an action with nouns, or add uncertainty. The main part is officialese: the language of documents transferred into living text; method sources - `human_text_standards.md`, 08.02.

Order of fixing what is found:

1. A stop word from the table - the replacement from the "Replacement" column
2. No replacement in the table - rebuild the sentence: find who performs the action, restore the verb, remove empty words
3. Deletion test: remove the word or phrase - if the meaning is intact, delete it without a replacement
4. Check the style status against the marks in Section 02 and the "Deviations" column; the mark "норма" means the item is not corrected during self-check
5. The separator in tables is an arrow made of a hyphen and a greater-than sign (dashes are banned in package texts, 04.03)

---

## 02. Applicability by Styles

*Mandatory.*

The applicability matrix is common to the package: it lives in `human_text_standards.md`, 03.09, and is not duplicated here.

In ДС and ТС officialese is limited: legal and technical precision allows individual formulas («в соответствии с», «осуществляет учет»). Acceptability is checked against the "Deviations" column of the tables; without an explicit mark the item is corrected in both ДС and ТС. Filler, amplifiers, evaluations, and pleonasms are garbage in any style.

---

## 03. Officialese and Verbal Noun Constructions

*Mandatory.*

Base status: banned in РЛ, РС, ДЛ, ТЛ; limited in ДС and ТС (per marks). A verbal noun is replaced with a verb - this is the most frequent correction of agent text.

| Word or phrase | Replacement | Deviations |
|-------------------|--------|------------|
| является | это, входит в состав, тире-конструкция | в ДС и ТС допустимо в определениях терминов |
| данный, указанный | этот | в ДС и ТС допустимо в отсылках к пунктам и документам |
| вышеуказанный, вышеупомянутый | этот, выше названный | запрет везде, включая ДС и ТС |
| нижеследующий | следующий, такой | запрет везде |
| осуществлять | делать, проводить, вести | |
| осуществлять контроль | контролировать | |
| осуществлять поддержку | поддерживать | |
| производить | делать, выполнять | в ТС допустимо в значениях производства |
| производить оплату | платить, оплатить | в ДС допустимо |
| функционировать | работать | |
| задействовать | использовать | |
| имеет место, имеет место быть | есть, происходит | запрет везде, включая ДС и ТС |
| принять решение | решить | |
| оказать помощь, оказать содействие | помочь | |
| оказывать поддержку | поддерживать | |
| довести до сведения | сообщить | в ДС допустимо |
| проводить анализ | анализировать | |
| провести обсуждение | обсудить | |
| выполнение работ по | работа над | |
| осуществление, проведение, реализация, обеспечение (как существительные) | глагол: провести, реализовать, обеспечить | |
| реализовывать функциональность | умеет, поддерживает | в ТС допустимо про функции |
| присутствует возможность | можно | |
| представляет собой | это, перестроить | пустая связка (copula-патология); в ДС и ТС допустимо в определениях |
| выступает в качестве, служит, считается (как связка) | перестроить без связки | |
| надлежащий | нужный, правильный | |
| обеспечить (без действия) | указать конкретное действие | в ТС норма: «обеспечивает шифрование» |
| целесообразность | перестроить: зачем и почему | |
| а также | и | |
| уведомляем вас о необходимости | пришлите, пожалуйста | в ДС допустимо |
| производится оплата, производится отгрузка | оплатить, отгружаем | в ДС допустимо |

---

## 04. Officialese Phrases and Prepositions

*Mandatory.*

Base status: banned in РЛ, РС, ДЛ, ТЛ; limited in ДС and ТС (per marks).

| Phrase | Replacement | Deviations |
|--------|--------|------------|
| в настоящее время, в данный момент | сейчас | |
| на сегодняшний день | сегодня, сейчас | |
| в связи с тем, что | потому что, так как | |
| ввиду того, что | так как, из-за | |
| вследствие | из-за | |
| в целях, с целью | чтобы, для | в ДС допустимо в уведомлениях |
| в рамках | в, при, внутри | в ДС и ТС ограничено: допустимо про границы договоров и проектов |
| в соответствии с | по, согласно | в ДС и ТС норма жанра |
| на основании | по, на основе | в ДС допустимо |
| по причине | из-за | |
| в случае, если | если | в ДС допустимо |
| при наличии отсутствия | если нет | запрет везде |
| в деле, в части, по линии | перестроить предложение | запрет везде |
| по вопросу | о, про | |
| по факту | по итогам, после | |
| необходимо осуществить | нужно сделать | |
| при осуществлении | при | |
| в рамках данного проекта | в проекте | |
| в адрес | от, для | перестраивать: «в адрес школы поступило обращение» -> «школе написали» |
| в контексте | вырезать или перестроить | |
| в русле | перестроить | запрет везде |
| на предмет | перестроить: «на предмет проверки» -> «чтобы проверить» | |
| в отношении | перестроить | |
| с точки зрения | перестроить | в ДС и ТС допустимо при явном ракурсе рассмотрения |
| что касается | начать сразу с темы | |
| в ходе | в, при, во время | |

---

## 05. Filler and Introductory Constructions

*Mandatory.*

Status: banned in all styles. Empty words and introductory phrases carrying no meaning: the deletion test works almost always.

| Word or phrase | Replacement |
|-------------------|--------|
| в принципе, в общем, в целом | удалить |
| на самом деле, действительно | удалить или дать факт |
| как известно, не секрет, что | удалить или дать источник |
| кстати, между прочим | удалить |
| мягко говоря, если честно, честно говоря | удалить |
| вообще-то, собственно говоря | удалить |
| по сути, по большому счету | удалить |
| так сказать, скажем так | удалить |
| безусловно, бесспорно, очевидно | удалить или дать доказательство |
| разумеется, конечно (вводные) | удалить; «конечно» прямым ответом на вопрос - легитимно |
| как бы, типа того | удалить |
| достаточно (оценка без меры) | удалить или указать меру; «достаточно» с измеримой мерой (достаточно 2 ГБ диска) - легитимно |
| фактически | удалить или дать факт |
| вправду, реально | удалить |
| ну | удалить |
| ах, ох, ух (междометия) | удалить |

---

## 06. Amplifiers

*Mandatory.*

Status: banned in all styles. Add-on words that amplify without justification: you can amplify with a fact, not with a word.

| Word | Replacement |
|--------|--------|
| очень | удалить; усилить фактом |
| крайне, чрезвычайно, максимально, предельно | удалить |
| невероятно, немыслимо, страшно | удалить |
| значительно, существенно | указать, насколько: число или сравнение |
| наиболее, самый | удалить или дать сравнение |
| уникальный, исключительный, непревзойденный | удалить или дать факт |
| потрясающий, шокирующий, сногсшибательный | удалить |
| особо, особенно | удалить или дать критерий |
| абсолютно | удалить или обосновать |
| весьма | удалить |
| буквально | удалить или использовать по назначению |
| по-настоящему | удалить |
| в значительной степени | удалить или дать меру |

---

## 07. Evaluations without Evidence

*Mandatory.*

Status: banned in all styles. An evaluative adjective is allowed only with a measurable criterion next to it (in ТС - by the requirements rules, `human_text_standards.md`, 02.03).

| Word or phrase | Replacement |
|-------------------|--------|
| удобный, комфортный | дать критерий: количество действий, время |
| быстрый, медленный | дать число: секунды, операции в секунду |
| эффективный, результативный | дать сравнение до и после |
| качественный, надежный | дать факт: гарантии, тесты, срок работы |
| современный, передовой, инновационный | удалить или назвать технологию и версию |
| оптимальный | дать критерий оптимизации |
| играет важную роль, играет ключевую роль | указать роль фактом |
| значимый, существенный | дать число или влияние |
| простой, легкий (о решении) | дать число шагов или операций |
| гибкий, масштабируемый | дать способность: что именно умеет |
| лучший | дать критерий сравнения |
| идеальный, прекрасный, замечательный | дать свойства |
| отличный, великолепный, превосходный | дать свойства или факт |
| красивый (о решении) | дать свойство |
| высококлассный | дать факты: сертификаты, рейтинги, кейсы |
| выгодный | показать числа |
| гарантированный (без условий гарантии) | дать условия гарантии |
| номер 1, не имеет аналогов | дать проверяемый факт |
| изменит вашу жизнь | удалить или дать измеримый эффект |
| наконец-то | удалить |

---

## 08. Pleonasms

*Mandatory.*

Status: banned in all styles. Redundant doubling of meaning is a language error, not a matter of style.

| Phrase | Replacement |
|--------|--------|
| свободная вакансия | вакансия |
| прейскурант цен | прейскурант |
| главная суть, основная суть | суть |
| полностью отсутствует | отсутствует |
| предварительно предупредить | предупредить |
| период времени | период |
| подробные детали | детали |
| конечная цель | цель |
| совместное сотрудничество | сотрудничество |
| первый дебют | дебют |
| памятный сувенир | сувенир |
| стоимость тарифа | стоимость |
| своя автобиография | автобиография |
| главные приоритеты | приоритеты |

---

## 09. Corporate and Advertising Cliches

*Mandatory.*

Status: banned in all styles. Ready-made phrases that the reader skips without seeing. The cliche test: could a competing company write the same thing word for word - if yes, it is a cliche.

| Cliche | Replacement |
|--------|--------|
| команда профессионалов | квалификация и опыт: число специалистов, годы |
| молодая динамично развивающаяся компания | год основания, рост |
| индивидуальный подход | конкретный процесс работы с клиентом |
| широкий ассортимент | число позиций или категории |
| выгодные цены | цены или сравнение |
| работы любой сложности | примеры выполненных работ |
| гибкая система скидок | размер и условия скидок |
| в кратчайшие сроки | конкретный срок |
| лидер рынка | доля рынка или рейтинг |
| богатый опыт | годы, проекты, клиенты |
| высокий профессионализм | сертификаты, кейсы |
| комплексные решения | состав решения |
| лояльная ценовая политика | цены и условия |
| оптимальное соотношение цены и качества | критерии и числа |
| клиентоориентированный подход | конкретика обслуживания |
| полный спектр услуг | перечень услуг |

---

## 10. Newspaper and Everyday Cliches

*Mandatory.*

Status: banned in all styles. Dead metaphors and colloquial cliches.

| Cliche | Replacement |
|--------|--------|
| виновники торжества | имена |
| ударными темпами | дать темп: сроки и объемы |
| царила атмосфера | дать детали |
| в лучших традициях | удалить или дать источник |
| бить ключом | дать факт |
| ломать голову | искать решение |
| краеугольный камень | основа, главное условие |
| в центре внимания | дать факт внимания |
| дать зеленый свет | разрешить, согласовать |
| оставить свой след | дать результат |
| на стыке, на передовой, на пике | дать конкретное положение |
| бросить вызов | противостоять, названо чему |
| поживем-увидим | удалить или дать критерий проверки |
| головная боль | назвать проблему |
| в двух шагах от | дать расстояние |
| давайте разберемся (как заполнитель) | дать план разбора или удалить |

---

## 11. Time Parasites

*Mandatory.*

Status: banned in all styles. Redundant time references when the context already sets them. Exception - an explicit contrast between past and present.

| Phrase | Replacement |
|--------|--------|
| в наши дни | удалить; при важности - назвать год |
| нынче | удалить |
| на протяжении долгих лет | указать количество лет |
| испокон веков | удалить или дать дату |
| в скором времени | указать срок |
| не за горами | назвать срок или событие |
| в ближайшее время | назвать дату или месяц |
| в последнее время | удалить или назвать период |

---

## 12. Uncertainty

*Mandatory.*

Status: banned in РЛ, РС, ДЛ, and ТЛ; limited in ДС and ТС - allowed when precision is fundamentally unattainable and this is stated. Words that hide specifics.

| Word | Replacement |
|--------|--------|
| кто-то, какой-то, что-то, где-то, как-то | назвать конкретно |
| некий, некоторый | указать количество или убрать |
| около, свыше, порядка | дать точное число; при недоступности точного - диапазон с источником оценки |
| более (без числа) | дать число |
| ряд (о перечислении) | перечислить или дать число |
| определенный, соответствующий (без референта) | назвать конкретно |
| различный, всевозможный | удалить или перечислить |

Transformation: «Более 15 лет на рынке» -> «Работаем с 2010 года»; «Ряд преимуществ» -> перечислить преимущества.

---

## 13. Modal Softeners

*Mandatory.*

Status: limited. In instructions (РЛ, ТЛ) they are replaced with the imperative; in requirements and charters (ДС, ТС) they are the genre norm; elsewhere - rebuild directly.

| Word | Replacement | Deviations |
|--------|--------|------------|
| можно (в инструкции) | императив: «сделайте» вместо «можно сделать» | в РС и ДЛ допустимо о внешних возможностях |
| нужно, необходимо | в инструкциях - императив; в остальных указать, кому и зачем | в ДС и ТС норма жанра |
| следует | указать, кто и почему | в ДС и ТС норма жанра |
| стоит (в значении «стоит сделать») | императив или прямое предложение | |
| мне бы хотелось | писать прямо: «предлагаю» | запрет везде |
| было бы неплохо | прямая формулировка | запрет везде |

---

## 14. Pretentiousness and Pseudo-Terminology

*Mandatory.*

Status: banned in all styles. Pretentious words meant to impress instead of convey meaning. A term needed for the point stays and is explained at first use.

| Word | Replacement |
|--------|--------|
| имплементация | внедрение, реализация |
| синергия | совместный эффект |
| парадигма | подход, модель |
| экзистенциальный (вне философии) | перестроить по смыслу |
| когнитивный (вне научного текста) | мыслительный, связанный с восприятием |
| подсознательно | неосознанно; лучше перестроить: назван признак |
| гештальт (вне психотерапии) | незавершенное дело |
| абьюзер | обидчик |
| фобия (вне клиники) | страх |
| нарцисс (о человеке вне клиники) | дать поведение: «думает только о себе» |

---

## 15. Structural Limits

*Mandatory.*

Status: limited in all styles. Rules of sentence form; exceeding them is a reason to rebuild the sentence.

1. Participial phrases: at most one per sentence; more - split into separate sentences
2. Genitive case: three or more nouns in a row - rewrite («решение задачи оптимизации функции награды агента» -> «как подобрать функцию награды для агента»)
3. Passive voice: if the actor is known and important - active («банк решает за 2 часа», not «решение принимается банком»); allowed when the actor is unknown or unimportant, and also in ДС and ТС
4. Redundant pronouns: «мы предлагаем вам попробовать» -> «попробуйте»
5. Enumerations: alternate lengths; triples "X, Y и Z" in every paragraph are a rhythm marker (see `human_text_dict_ai_standards.md`, 08)

---

## 16. Dictionary Enrichment

*Mandatory.*

The enrichment mechanism is in `human_text_standards.md`, 05.04. Adding an entry:

1. Word or phrase - into the category by meaning
2. Replacement - concrete and applicable in most contexts; if there is no replacement - rebuild the sentence
3. Deviations - a style mark and condition if the item is allowed in ДС or ТС
4. Source - a link to a style guide, reference book, or the note "user correction"

---

## 17.01. Related Documents

| Document | Relation |
|----------|-------|
| `human_text_standards.md` | Main document: genres, styles, method, applicability statuses (03.09), enrichment mechanism (05.04) |
| `human_text_dict_ai_standards.md` | Paired denylist: AI text markers, forbidden replacements |
| `human_text_allowlist_standards.md` | Canon lexicon: what to replace with when rebuilding |
| `project_standards.md` | Text micro level (04.03), package editing (07.05) |
| `doc/specs/text_overrides.md` | Override template: domain prohibitions and permissions on top of this dictionary |

---

## 17.02. Versioning

Versioning of the standards package is unified for all package documents. The versioning policy, registry, and routing map are in `doc/standards/_index_standards.md`. A package version bump is performed only on explicit user request.
