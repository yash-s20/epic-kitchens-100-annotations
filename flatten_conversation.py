import json

with open('epic-kitchens.json') as json_file:
    data = json.load(json_file)
    conversations = data["example"]["conversations"][0]
    print(conversations)

    human_conv = {
        "from": "human",
        "value": ""
    }
    gpt_conv = {
        "from": "gpt",
        "value": ""
    }
    for conversation in conversations:
        if conversation["from"] == "human":
            human_conv["value"] += conversation["value"] + "\n"
        else:
            gpt_conv["value"] += conversation["value"] + "\n"
    data["example"]["conversations"] = [[human_conv, gpt_conv]]
    with open('epic-kitchens2.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)
