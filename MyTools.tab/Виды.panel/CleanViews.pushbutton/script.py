# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms

doc = revit.doc

# 1. Находим все виды, которые уже вынесены на листы
placed_view_ids = set()
viewports = DB.FilteredElementCollector(doc).OfClass(DB.Viewport).ToElements()
for vp in viewports:
    placed_view_ids.add(vp.ViewId)

# 2. Собираем неразмещённые виды (исключая шаблоны и текущий открытый вид)
allowed_types = [
    DB.ViewType.FloorPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.Elevation,
    DB.ViewType.Section,
    DB.ViewType.ThreeD,
    DB.ViewType.Detail,
    DB.ViewType.DraftingView
]

unused_views = []
all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()

for v in all_views:
    if v.IsTemplate or v.ViewType not in allowed_types:
        continue
    if v.Id in placed_view_ids or v.Id == doc.ActiveView.Id:
        continue
    unused_views.append(v)

if not unused_views:
    forms.alert("Лишних видов не найдено (все на листах или открыт единственный вид).", title="Чистка модели")
    raise SystemExit

# 3. Показываем список на выбор
class ViewOption(forms.TemplateListItem):
    @property
    def name(self):
        return "{} ({})".format(self.item.Name, self.item.ViewType)

options = [ViewOption(v) for v in sorted(unused_views, key=lambda x: x.Name)]
selected = forms.SelectFromList.show(
    options,
    title="Неразмещённые виды — выберите для удаления",
    button_name="Удалить выбранные",
    multiselect=True
)

if not selected:
    raise SystemExit

# 4. Удаляем выбранные виды
deleted_count = 0
with revit.Transaction("Удаление неразмещённых видов"):
    for v in selected:
        try:
            doc.Delete(v.Id)
            deleted_count += 1
        except Exception:
            pass

forms.alert("Готово! Удалено видов: {}".format(deleted_count), title="Чистка модели")