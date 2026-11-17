# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms

doc = revit.doc
active_view = doc.ActiveView

# 1. Выбор категории
categories = {
    "Двери": (DB.BuiltInCategory.OST_Doors, "Д-"),
    "Окна": (DB.BuiltInCategory.OST_Windows, "ОК-"),
    "Колонны несущие": (DB.BuiltInCategory.OST_StructuralColumns, "К-"),
    "Помещения": (DB.BuiltInCategory.OST_Rooms, "П-")
}

selected_cat_name = forms.SelectFromList.show(
    sorted(categories.keys()),
    title="Шаг 1: Выберите категорию на текущем виде",
    button_name="Далее",
    multiselect=False
)

if not selected_cat_name:
    raise SystemExit

bic, default_prefix = categories[selected_cat_name]

# 2. Собираем элементы выбранной категории на активном виде
elements = DB.FilteredElementCollector(doc, active_view.Id) \
    .OfCategory(bic) \
    .WhereElementIsNotElementType() \
    .ToElements()

if not elements:
    forms.alert(
        "На текущем виде не найдено элементов категории «{}».".format(selected_cat_name),
        title="Автонумерация"
    )
    raise SystemExit

# 3. Запрашиваем префикс и начальный номер
prefix = forms.ask_for_string(
    default=default_prefix,
    prompt="Введите префикс для параметра «Марка»:",
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

start_num = int(start_str)

# 4. Функция получения координат для сортировки (сверху вниз, слева направо)
def get_sort_key(el):
    loc = el.Location
    if isinstance(loc, DB.LocationPoint):
        pt = loc.Point
        return (-round(pt.Y, 1), round(pt.X, 1))
    bbox = el.get_BoundingBox(active_view)
    if bbox:
        cx = (bbox.Min.X + bbox.Max.X) / 2.0
        cy = (bbox.Min.Y + bbox.Max.Y) / 2.0
        return (-round(cy, 1), round(cx, 1))
    return (0, 0)

sorted_elements = sorted(elements, key=get_sort_key)

# 5. Проставляем параметр «Марка»
count = 0
with revit.Transaction("Автонумерация элементов"):
    for i, el in enumerate(sorted_elements):
        param = el.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
        if param and not param.IsReadOnly:
            mark_value = "{}{:02d}".format(prefix, start_num + i)
            param.Set(mark_value)
            count += 1

forms.alert(
    "Готово! Пронумеровано элементов («{}»): {}".format(selected_cat_name, count),
    title="Автонумерация"
)