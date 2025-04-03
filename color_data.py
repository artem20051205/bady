color_dict ={
  "У вас є відчуття нестачі енергії?":                                                  {"yellow": 1, "green": 0, "cyan": 1, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Ви часто хворієте (більше 2 разів на рік)?":                                         {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Неприємний запах тіла або з рота (або тяжке дихання).":                              {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 1, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
  "Погано перетравлюються деякі продукти. У вас є важкість, здуття, проноси, закрепи.": {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Ви їсте червоне м'ясо 2 і більше разів на тиждень?":                                 {"yellow": 0, "green": 1, "cyan": 1, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Проблеми з менструальним циклом (для жінок).":                                       {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 1, "blue": 0, "pink": 0},
  "Використовуєте антибіотики (інші ліки) більше 2 разів на рік.":                      {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Регулярно споживаєте алкоголь.":                                                     {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Перепади настрою.":                                                                  {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Харчова алергія.":                                                                   {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Темні кола та (або) набряклість під очима.":                                         {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 1},
  "Ви палите будь які цигарки(в тому числі пасивно)?":                                  {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Важко сконцентруватися, погане запам'ятовування.":                                   {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Погана переносимость хворобливих станів.":                                           {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Будь який дискомфорт після прийняття їжі.":                                          {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Нервова обстановка, надлишок стресів.":                                              {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 1},
  "Проблеми зі шкірою.":                                                                {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 1, "blue": 1, "pink": 1},
  "Споживання солодкої та переробленої їжі.":                                           {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Надмірне вживання молочних продуктів.":                                              {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Почуття апатії, млявості, депресія.":                                                {"yellow": 0, "green": 1, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Сон, що не приносить відпочинку.":                                                   {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Період менопаузи.":                                                                  {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
  "Проблеми з сечовипусканням.":                                                        {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
  "Чутлива витончена шкіра, зморшки, відчуття сухості.":                                {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Випадання волосся.":                                                                 {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
  "Набряки та болі в суглобах.":                                                        {"yellow": 0, "green": 0, "cyan": 1, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
  "Проблеми збереження нормальної ваги.":                                               {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
  "Швидка стомлюваність (брак сили, витривалості).":                                    {"yellow": 0, "green": 0, "cyan": 1, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
  "Недотримання режиму живлення (харчування та питного режиму).":                       {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 1},
  "Повільне одужання від застуд та вірусів.":                                           {"yellow": 0, "green": 1, "cyan": 1, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Нерегулярний стілець.":                                                              {"yellow": 1, "green": 1, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Поганий апетит.":                                                                    {"yellow": 1, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Низька сексуальна активність.":                                                      {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Витончені і ламкі нігті (нігті, що шаруються).":                                     {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
  "Сухе, тьмяне, пошкоджене волосся.":                                                  {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
  "Вживання жирної їжі.":                                                               {"yellow": 1, "green": 1, "cyan": 1, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Нестача клітковини в раціоні.":                                                      {"yellow": 0, "green": 1, "cyan": 1, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "М'язовий дискомфорт (болі, судоми).":                                                {"yellow": 0, "green": 0, "cyan": 1, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
  "Несприятлива екологія.":                                                             {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 1, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 1},
  "Денна сонливість.":                                                                  {"yellow": 0, "green": 0, "cyan": 1, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Часте споживання кави або чаю.":                                                     {"yellow": 0, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
  "Гіперчутливість до хімікатів, ліків, їжі.":                                          {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Будь які грибкові ураження.":                                                        {"yellow": 1, "green": 1, "cyan": 0, "red": 0, "gray": 1, "purple": 0, "orange": 1, "magenta": 0, "blue": 0, "pink": 0},
  "Слабкість у м'язах, крихкість кісток.":                                              {"yellow": 1, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 1, "pink": 0},
  "Постійна тривога.":                                                                  {"yellow": 1, "green": 0, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Підвищена дратівливість, надмірна збудливість, агресія.":                            {"yellow": 0, "green": 1, "cyan": 0, "red": 1, "gray": 0, "purple": 0, "orange": 0, "magenta": 1, "blue": 0, "pink": 0},
  "Малорухливий спосіб життя, низька фізична активність.":                              {"yellow": 0, "green": 1, "cyan": 1, "red": 1, "gray": 1, "purple": 0, "orange": 0, "magenta": 1, "blue": 1, "pink": 0},
  "Підвищене виділення мокротиння (виділення слизу).":                                  {"yellow": 0, "green": 1, "cyan": 0, "red": 0, "gray": 0, "purple": 1, "orange": 0, "magenta": 0, "blue": 0, "pink": 0},
  "Великі пори на шкірі, підвищене саловиділення, вугри.":                              {"yellow": 0, "green": 0, "cyan": 0, "red": 0, "gray": 0, "purple": 0, "orange": 0, "magenta": 0, "blue": 0, "pink": 1}
}
evaluation_criteria = {
    "yellow":   [(2, "дуже добре"), (4, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "green":    [(2, "дуже добре"), (4, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "cyan":     [(2, "дуже добре"), (3, "добре"), (7, "задовільно"), (float('inf'), "незадовільно")],
    "red":      [(2, "дуже добре"), (5, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "gray":     [(2, "дуже добре"), (4, "добре"), (7, "задовільно"), (float('inf'), "незадовільно")],
    "purple":   [(0, "дуже добре"), (3, "добре"), (5, "задовільно"), (float('inf'), "незадовільно")],
    "orange":   [(0, "дуже добре"), (1, "добре"), (4, "задовільно"), (float('inf'), "незадовільно")],
    "magenta":  [(2, "дуже добре"), (5, "добре"), (9, "задовільно"), (float('inf'), "незадовільно")],
    "blue":     [(1, "дуже добре"), (3, "добре"), (8, "задовільно"), (float('inf'), "незадовільно")],
    "pink":     [(1, "дуже добре"), (3, "добре"), (6, "задовільно"), (float('inf'), "незадовільно")]
}
color_to_system = {
    "yellow":   "Травна система",
    "green":    "Шлунково-кишковий тракт",
    "cyan":     "Серцево-судинна система",
    "red":      "Нервова система",
    "gray":     "Імунна система",
    "purple":   "Дихальна система",
    "orange":   "Сечовидільна система",
    "magenta":  "Ендокринна система",
    "blue":     "Опорно-рухова система",
    "pink":     "Шкіра"
}
evaluation_icons = {
    "дуже добре":   "🟢",
    "добре":        "🟡",
    "задовільно":   "🟠",
    "незадовільно": "🔴"
}
MENUS = {
    1: "🍽️ Меню на День 1:\n1. Завтрак: Овсянка с фруктами\n2. Обед: Курица с рисом\n3. Ужин: Салат с тунцом",
    2: "🍽️ Меню на День 2:\n1. Завтрак: Яйца с тостом\n2. Обед: Рыба с овощами\n3. Ужин: Гречка с грибами",
    3: "🍽️ Меню на День 3:\n1. Завтрак: Творог с медом\n2. Обед: Говядина с картофелем\n3. Ужин: Овощной суп"
}
