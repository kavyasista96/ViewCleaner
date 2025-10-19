# -*- coding: utf-8 -*-
from pyrevit import revit, DB

doc = revit.doc

# --- Protect views whose names contain any of these keywords (case-insensitive)
KEEP_KEYWORDS = ["wrk"]   # add more like: ["wrk", "[wip]", "temp"]

def get_views_on_sheets():
    view_ids = set()
    for vp in DB.FilteredElementCollector(doc).OfClass(DB.Viewport).ToElements():
        view_ids.add(vp.ViewId)
    return view_ids

views_on_sheets = get_views_on_sheets()

view_types_to_delete = [
    DB.ViewType.FloorPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.AreaPlan,
    DB.ViewType.EngineeringPlan,
    DB.ViewType.Section,
    DB.ViewType.Elevation,
    DB.ViewType.Detail,
    DB.ViewType.ThreeD,
    DB.ViewType.DraftingView
]

def get_dependent_view_map():
    view_map = {}
    for view in DB.FilteredElementCollector(doc).OfClass(DB.View):
        if view.IsTemplate or view.ViewType not in view_types_to_delete:
            continue
        parent_id = view.GetPrimaryViewId()
        if parent_id != DB.ElementId.InvalidElementId:
            if parent_id not in view_map:
                view_map[parent_id] = []
            view_map[parent_id].append(view.Id)
    return view_map

dependent_view_map = get_dependent_view_map()

def name_has_keep_keyword(name):
    n = (name or "").lower()
    for k in KEEP_KEYWORDS:
        if k.lower() in n:
            return True
    return False

views_to_delete = []

for view in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements():
    if view.IsTemplate:
        continue
    if view.ViewType not in view_types_to_delete:
        continue
    if view.Id in views_on_sheets:
        continue
    if name_has_keep_keyword(view.Name):
        continue
    if view.Name and view.Name.strip().lower() in ["project browser", "***project homepage***", "system browser"]:
        continue
    if view.Id in dependent_view_map:
        if any(dep_id in views_on_sheets for dep_id in dependent_view_map[view.Id]):
            continue
    views_to_delete.append((view.Id, view.Name))

deleted = 0
deleted_names = []
undeletable = []

t = DB.Transaction(doc, "Delete Unused Regular Views (Safe)")
try:
    t.Start()
    for view_id, name in views_to_delete:
        try:
            doc.Delete(view_id)
            deleted += 1
            deleted_names.append(name)
        except Exception as e:
            undeletable.append((name, str(e)))
    t.Commit()
except Exception as e:
    print("Transaction failed: {0}".format(e))
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
finally:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()

print("Deleted {0} unused regular views.".format(deleted))
if deleted_names:
    print("\nDeleted views:")
    for name in deleted_names:
        print(" - {0}".format(name))
if undeletable:
    print("\nCould not delete the following views:")
    for name, reason in undeletable:
        print(" - {0}: {1}".format(name, reason))
