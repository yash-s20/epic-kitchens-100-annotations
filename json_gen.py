import csv
import sys
import json
import time
import datetime
import random

random.seed(42)
def r():
    return random.randint(0,255)

def hex_r():
    return '#%02X%02X%02X' % (r(),r(),r())

rf = sys.argv[1]

video = sys.argv[2]
config_json = {}
annotation_json = {}

objects = {}
verbs = {}
obj_id = 1
verb_id = 1

action_data = []

config = {
    "objectLabelData": [],
    "actionLabelData": [],
    "skeletonTypeData": []
}
annotation = {
    "video": {},
    "keyframelist": [],
    "objectAnnotationListMap": {},
    "regionAnnotationListMap": {},
    "skeletonAnnotationListMap": {},
    "actionAnnotationList": [],
}

tot_data = []
with open(rf, 'r') as csvf:
    for row in csv.reader(csvf, delimiter=',', quotechar='"'):
        if video not in row[0]:
            continue
        print(row[9], row[11])
        obj = row[11].strip()
        v = row[9].strip()
        if obj in objects:
            pass
        else:
            objects[obj] = obj_id
            obj_id += 1
        if v in verbs:
            pass
        else:
            verbs[v] = verb_id
            verb_id += 1
        t = time.strptime(row[4].strip(), "%H:%M:%S.%f")
        st = datetime.timedelta(hours=t.tm_hour,minutes=t.tm_min,seconds=t.tm_sec).total_seconds()
        t = time.strptime(row[5].strip(), "%H:%M:%S.%f")
        et = datetime.timedelta(hours=t.tm_hour,minutes=t.tm_min,seconds=t.tm_sec).total_seconds()
        print(row[4], row[5])
        print(st, et)
        old_et = et
        tot_data.append((st, et, verbs[v], objects[obj], hex_r(), row[8].strip()))

old_et = 0
tot_data.sort()

for d in tot_data:
    if old_et < d[0]:
        action_data.append({
            "start": old_et,
            "end": d[0],
            "action": 0,
            "object": 0,
            "color": "#FFFF00",
            "description": "state predicates"
        })
    else:
        action_data.append({
            "start": d[0] - 1,
            "end": d[0],
            "action": 0,
            "object": 0,
            "color": "#FFFF00",
            "description": "state predicate placeholder"
        })
    old_et = d[1]
    action_data.append({
        "start": d[0],
        "end": d[1],
        "action": d[2],
        "object": d[3],
        "color": d[4],
        "description": d[5],
    })

obj_id_list = list(objects.values())
obj_data = [
    {
        "id": 0,
        "name": "default",
        "color": "#00FF00"
    }
]

verb_data = [
    {
        "id": 0,
        "name": "default",
        "color": "#0000FF",
        "objects": [
            0
        ]
    }
]

for obj, obj_id in objects.items():
    obj_data.append({
        "id": obj_id,
        "name": obj,
        "color": hex_r()
    })

for v, vid in verbs.items():
    verb_data.append({
        "id": vid,
        "name": v,
        "color": hex_r(),
        "objects": obj_id_list
    })
config["objectLabelData"] = obj_data
config["actionLabelData"] = verb_data

annotation["actionAnnotationList"] = action_data

json.dump(config, open('config.json', 'w'))
json.dump({"version": "2.0.3", "annotation": annotation, "config": config}, open('annotations.json', 'w'))
