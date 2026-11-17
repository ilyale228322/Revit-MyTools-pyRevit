# -*- coding: utf-8 -*-
from pyrevit import revit, forms

# 1. Выбор видов через встроенное окно pyRevit
views = forms.select_views(
    title="Выберите виды для переименования",
    button_name="Выбрать"
)
if not views:
    forms.alert("Виды не выбраны.", exitscript=True)

# 2. Выбор режима работы
mode = forms.CommandSwitchWindow.show(
    ["Добавить префикс", "Найти и заменить"],
    message="Выберите действие:"
)
if not mode:
    forms.alert("Действие отменено.", exitscript=True)

# 3. Запрос параметров у пользователя
prefix = ""
find_text = ""
replace_text = ""

if mode == "Добавить префикс":
    prefix = forms.ask_for_string(
        default="АР_",
        prompt="Введите префикс для начала названия:",
        title="Добавить префикс"
    )
    if not prefix:
        forms.alert("Префикс не задан.", exitscript=True)
else:
    find_text = forms.ask_for_string(
        default="",
        prompt="Какой текст найти в названии?",
        title="Поиск"
    )
    if not find_text:
        forms.alert("Текст для поиска не задан.", exitscript=True)
    replace_text = forms.ask_for_string(
        default="",
        prompt="На что заменить? (оставьте пустым, чтобы удалить)",
        title="Замена"
    )
    if replace_text is None:
        forms.alert("Действие отменено.", exitscript=True)

# 4. Переименование внутри транзакции Revit
renamed_count = 0
errors = []

with revit.Transaction("Массовое переименование видов"):
    for view in views:
        old_name = view.Name
        if mode == "Добавить префикс":
            new_name = prefix + old_name
        else:
            if find_text not in old_name:
                continue
            new_name = old_name.replace(find_text, replace_text)

        if new_name != old_name:
            try:
                view.Name = new_name
                renamed_count += 1
            except Exception as e:
                errors.append("{} -> {}: {}".format(old_name, new_name, e))

# 5. Отчёт о результате
msg = "Готово! Переименовано видов: {}".format(renamed_count)
if errors:
    msg += "\n\nНе удалось переименовать (возможно, имя уже занято):\n" + "\n".join(errors)

forms.alert(msg, title="Результат")