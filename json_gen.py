import csv
import sys
import json
import time
import datetime
import random
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
        action_data.append({
            "start": st,
            "end": et,
            "action": verbs[v],
            "object": objects[obj],
            "color": hex_r(),
            "description": row[8].strip()
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
