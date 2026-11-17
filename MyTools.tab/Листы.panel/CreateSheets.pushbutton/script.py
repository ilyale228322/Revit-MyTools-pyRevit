# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms

doc = revit.doc

# 1. Собираем все загруженные основные надписи (рамки)
titleblocks = DB.FilteredElementCollector(doc) \
    .OfCategory(DB.BuiltInCategory.OST_TitleBlocks) \
    .WhereElementIsElementType() \
    .ToElements()

class TitleBlockOption(forms.TemplateListItem):
    @property
    def name(self):
        if self.item == "EMPTY":
            return "Без основной надписи (пустой лист)"
        type_name = revit.query.get_name(self.item)
        return "{} : {}".format(self.item.FamilyName, type_name)

options = [TitleBlockOption(tb) for tb in titleblocks]
options.append(TitleBlockOption("EMPTY"))

selected_tb = forms.SelectFromList.show(
    options,
    title="Шаг 1: Выберите основную надпись",
    button_name="Далее",
    multiselect=False
)

if not selected_tb:
    raise SystemExit

tb_id = DB.ElementId.InvalidElementId if selected_tb == "EMPTY" else selected_tb.Id

# 2. Запрашиваем параметры генерации
prefix = forms.ask_for_string(
    default="АР-",
    prompt="Введите префикс номера листа (можно оставить пустым):",
    title="Шаг 2: Префикс"
)
if prefix is None:
    raise SystemExit

start_str = forms.ask_for_string(
    default="1",
    prompt="С какого номера начать?",
    title="Шаг 3: Начальный номер"
)
if not start_str or not start_str.isdigit():
    forms.alert("Нужно ввести целое число!", title="Ошибка")
    raise SystemExit

count_str = forms.ask_for_string(
    default="5",
    prompt="Сколько листов создать?",
    title="Шаг 4: Количество"
)
if not count_str or not count_str.isdigit():
    forms.alert("Нужно ввести целое число!", title="Ошибка")
    raise SystemExit

base_name = forms.ask_for_string(
    default="План этажа",
    prompt="Базовое имя для листов:",
    title="Шаг 5: Имя листа"
)
if base_name is None:
    raise SystemExit

start_num = int(start_str)
count = int(count_str)

# 3. Собираем уже существующие номера листов, чтобы избежать ошибок
existing_numbers = set(
    s.SheetNumber for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements()
)

# 4. Создаём листы
created = 0
skipped = 0

with revit.Transaction("Пакетное создание листов"):
    for i in range(count):
        num = start_num + i
        sheet_num = "{}{:02d}".format(prefix, num)

        if sheet_num in existing_numbers:
            skipped += 1
            continue

        new_sheet = DB.ViewSheet.Create(doc, tb_id)
        new_sheet.SheetNumber = sheet_num
        new_sheet.Name = "{} {}".format(base_name, num)
        existing_numbers.add(sheet_num)
        created += 1

msg = "Готово! Создано листов: {}".format(created)
if skipped > 0:
    msg += "\nПропущено (номера уже заняты): {}".format(skipped)

forms.alert(msg, title="Пакетное создание листов")