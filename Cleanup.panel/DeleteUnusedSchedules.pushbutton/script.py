# -*- coding: utf-8 -*-
from pyrevit import revit, DB

doc = revit.doc

# Step 1: Get all schedule views placed on sheets
used_schedule_ids = set(
    ssi.ScheduleId
    for ssi in DB.FilteredElementCollector(doc).OfClass(DB.ScheduleSheetInstance).ToElements()
)

# Step 2: Collect all schedule views (excluding revision schedule types)
all_schedules = DB.FilteredElementCollector(doc).OfClass(DB.ViewSchedule).ToElements()
schedules_to_delete = []

for sched in all_schedules:
    if sched.Id in used_schedule_ids:
        continue
    if sched.IsTitleblockRevisionSchedule:
        continue
    schedules_to_delete.append((sched.Id, sched.Name))

# Step 3: Delete unused schedules
deleted = 0
undeletable = []

t = DB.Transaction(doc, "Delete Unused Schedules")
try:
    t.Start()
    for sched_id, name in schedules_to_delete:
        try:
            doc.Delete(sched_id)
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
print("✅ Deleted {} unused schedules.".format(deleted))
if undeletable:
    print("\n⚠️ Could not delete the following schedules:")
    for name, reason in undeletable:
        print(" - {}: {}".format(name, reason))
