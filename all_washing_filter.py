import csv
import sys

noun_c_f = 'EPIC_100_noun_classes_v2.csv'
verb_c_f = 'EPIC_100_verb_classes.csv'

# train_f = 'EPIC_100_train.csv'

# val_f = 'EPIC_100_validation.csv'

class_to_wash = {"cutlery", "container", "crockery", "utensils", "cookware", "appliances"}

class_for_wash = {"clean", "access", "block", "retrieve", "leave"}

def get_instances(row):
    def strip(x):
        return x.strip("'")
    instances = list(map(strip, row[2].strip('][').split(', ')))
    return instances


with open(noun_c_f, 'r') as nof, open(verb_c_f, 'r') as vef, open(sys.argv[1], 'r') as tf:
    v_inst = set()
    for row in csv.reader(vef, delimiter=',', quotechar='"'):
        if row[-1] not in class_for_wash:
            continue
        # print(row[2], type(row[2]))
        v_inst.update(get_instances(row))
    n_inst = set()
    for row in csv.reader(nof, delimiter=',', quotechar='"'):
        if row[-1] not in class_to_wash:
            continue
        n_inst.update(get_instances(row))
    # print("Verbs:")
    # print(v_inst)
    # print("Nouns:")
    # print(n_inst)
    for row in csv.reader(tf, delimiter=',', quotechar='"'):
        if row[9] in v_inst and row[11] in n_inst:
            print(", ".join(row))