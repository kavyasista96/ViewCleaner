# -*- coding: utf-8 -*-
from pyrevit import revit, DB

doc = revit.doc

# Step 1: Get all legends placed on sheets (through Viewports)
used_legend_ids = set(
    vp.ViewId
    for vp in DB.FilteredElementCollector(doc).OfClass(DB.Viewport).ToElements()
)

# Step 2: Collect all Legend views
all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
legends_to_delete = []

for view in all_views:
    if view.ViewType != DB.ViewType.Legend:
        continue
    if view.IsTemplate:
        continue
    if view.Id in used_legend_ids:
        continue
    if view.Name.strip().lower() in ["project browser", "***project homepage***", "system browser"]:
        continue
    legends_to_delete.append((view.Id, view.Name))

# Step 3: Delete unused legends
deleted = 0
undeletable = []

t = DB.Transaction(doc, "Delete Unused Legends")
try:
    t.Start()
    for lid, name in legends_to_delete:
        try:
            doc.Delete(lid)
            deleted += 1
        except Exception as e:
            undeletable.append((name, str(e)))
    t.Commit()
except Exception as e:
    print("Transaction failed: {}".format(e))
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
finally:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()

# Output
print("✅ Deleted {} unused legends.".format(deleted))
if undeletable:
    print("\n⚠️ Could not delete the following legends:")
    for name, reason in undeletable:
        print(" - {}: {}".format(name, reason))
