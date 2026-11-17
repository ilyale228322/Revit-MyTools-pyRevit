# -*- coding: utf-8 -*-
import os
import re
import codecs
from pyrevit import revit, DB, forms

doc = revit.doc

# 1. Собираем все обычные спецификации (исключая шаблоны и системные таблицы изменений)
all_schedules = DB.FilteredElementCollector(doc) \
    .OfClass(DB.ViewSchedule) \
    .ToElements()

schedules = [
    s for s in all_schedules
    if not s.IsTemplate
    and not s.IsTitleblockRevisionSchedule
    and not s.IsInternalKeynoteSchedule
]

if not schedules:
    forms.alert("В проекте нет спецификаций для экспорта.", title="Экспорт в Excel")
    raise SystemExit

# 2. Показываем список на выбор
class ScheduleOption(forms.TemplateListItem):
    @property
    def name(self):
        return self.item.Name

options = [ScheduleOption(s) for s in sorted(schedules, key=lambda x: x.Name)]
selected = forms.SelectFromList.show(
    options,
    title="Шаг 1: Выберите спецификации для экспорта",
    button_name="Далее",
    multiselect=True
)

if not selected:
    raise SystemExit

# 3. Выбираем папку для сохранения
export_folder = forms.pick_folder(title="Шаг 2: Выберите папку для сохранения CSV")
if not export_folder:
    raise SystemExit

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def escape_csv(val):
    if val is None:
        return ""
    val = val.replace('"', '""')
    if ';' in val or '"' in val or '\n' in val:
        return '"{}"'.format(val)
    return val

# 4. Экспортируем выбранные спецификации
exported_count = 0
for sched in selected:
    table_data = sched.GetTableData()
    body = table_data.GetSectionData(DB.SectionType.Body)
    rows = body.NumberOfRows
    cols = body.NumberOfColumns

    safe_name = clean_filename(sched.Name)
    file_path = os.path.join(export_folder, "{}.csv".format(safe_name))

    with codecs.open(file_path, "w", encoding="utf-8-sig") as f:
        for r in range(rows):
            row_values = []
            for c in range(cols):
                cell_text = sched.GetCellText(DB.SectionType.Body, r, c)
                row_values.append(escape_csv(cell_text))
            f.write(";".join(row_values) + "\r\n")

    exported_count += 1

forms.alert(
    "Готово! Экспортировано спецификаций: {}\nПапка: {}".format(exported_count, export_folder),
    title="Экспорт в Excel"
)