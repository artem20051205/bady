color_dict ={
    "Ви відчуваєте нестачу енергії?": {"yellow": 1, "green": 0, "cyan": 1, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Часто хворієте (більше 2 разів на рік)?": {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Неприємний запах тіла або з рота (або важке дихання)?": {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 1, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
  "Погане перетравлення деяких продуктів?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Ви їсте червоне м’ясо ≥ 2 рази на тиждень?": {"yellow": 0, "green": 1, "cyan": 1, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Проблеми з менструальним циклом (для жінок)?": {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 1, "blue": 0, "pink": 0},
#  "Використовуєте антибіотики (інші ліки) більше 2 разів на рік?": {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Регулярне вживання алкоголю?": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Перепади настрою?": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Лущення шкіри?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
#  "Темні кола (і/або набряклість) під очима?": {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 1},
#  "Кола (і набряки) під очима?": {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
#  "Важко зосередитися, погана пам’ять?": {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Підвищена сприйнятливість до хвороб?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Дискомфорт у печінці?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Нервова обстановка, надлишок стресів?": {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 1},
#  "Проблеми зі шкірою?": {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 1, "blue": 1, "pink": 1},
#  "Ви відчуваєте тягу до солодко та факту фуд": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Надмірне споживання молочних продуктів?": {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Відчуття апатії, млявості, депресія?": {"yellow": 0, "green": 1, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Сон, що не приносить відпочинку?": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Період менопаузи?": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
#  "Проблеми з сечовипусканням?": {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
#  "Чутлива (потоншена) шкіра, зморшки?": {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
#  "Випадіння волосся?": {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
#  "Набряки та біль у суглобах?": {"yellow": 0, "green": 0, "cyan": 1, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
#  "Важко підтримувати нормальну вагу?": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
#  "Швидка втомлюваність (нестача сил, витривалості)?": {"yellow": 0, "green": 0, "cyan": 1, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
#  "Недотримання режиму харчування?": {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 1},
#  "Повільне одужання?": {"yellow": 0, "green": 1, "cyan": 1, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Нерегулярний стул?": {"yellow": 1, "green": 1, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
#  "Поганий апетит?": {"yellow": 1, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Низька сексуальна активність?": {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Потоншені та ламкі нігті (шаруються нігті)?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
#  "Сухе, тьмяне, пошкоджене волосся?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
#  "Споживання жирної їжі?": {"yellow": 1, "green": 1, "cyan": 1, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Недостатня кількість клітковини в раціоні?": {"yellow": 0, "green": 1, "cyan": 1, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "М’язовий дискомфорт (болі, судоми)?": {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
#  "Несприятлива екологія?": {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
#  "Денна сонливість?": {"yellow": 0, "green": 0, "cyan": 1, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Щоденне споживання більше 2 чашок коли, кави або міцного чаю?": {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
#  "Чутливість до хімікатів, ліків, їжі?42": {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Грибкові ураження?": {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
#  "Слабкість у м’язах, крихкість кісток?": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
#  "Постійна тривога?": {"yellow": 1, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
#  "Підвищена дратівливість, надмірна збудливість, злість?": {"yellow": 0, "green": 1, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
#  "Малорухливий спосіб життя, низька фізична активність?": {"yellow": 0, "green": 1, "cyan": 1, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
#  "Підвищене виділення мокротиння (виділення слизу)?": {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
    "Великі пори на шкірі, підвищене саловиділення, вугрі?": {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1}
}
evaluation_criteria = {
    "yellow": [(2, "дуже добре"), (4, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "green": [(2, "дуже добре"), (4, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "cyan": [(2, "дуже добре"), (3, "добре"), (7, "задовільно"), (float('inf'), "незадовільно")],
    "red": [(2, "дуже добре"), (5, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "gray": [(2, "дуже добре"), (4, "добре"), (7, "задовільно"), (float('inf'), "незадовільно")],
    "purple": [(0, "дуже добре"), (3, "добре"), (5, "задовільно"), (float('inf'), "незадовільно")],
    "orange": [(0, "дуже добре"), (1, "добре"), (4, "задовільно"), (float('inf'), "незадовільно")],
    "magenta": [(2, "дуже добре"), (5, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "blue": [(1, "дуже добре"), (3, "добре"), (8, "задовільно"), (float('inf'), "незадовільно")],
    "pink": [(1, "дуже добре"), (3, "добре"), (6, "задовільно"), (float('inf'), "незадовільно")]
}
color_to_system = {
    "yellow": "Травна система",
    "green": "Шлунково-кишковий тракт",
    "cyan": "Серцево-судинна система",
    "red": "Нервова система",
    "gray": "Імунна система",
    "purple": "Дихальна система",
    "orange": "Сечовидільна система",
    "magenta": "Ендокринна система",
    "blue": "Опорно-рухова система",
    "pink": "Шкіра"
}
evaluation_icons = {
    "дуже добре": "🟢",   # Зеленый круг
    "добре": "🟡",       # Желтый круг
    "задовільно": "🟠",   # Оранжевый круг
    "незадовільно": "🔴"  # Красный круг
}
