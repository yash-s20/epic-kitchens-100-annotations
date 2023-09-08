import argparse
import subprocess
import os
import csv
import random
import json
import pprint
import datetime
MAX_EPISODES = -1 # -1 for all


if __name__ == "__main__":
    # parse dish washing csv to extract screenshots from video using ffmpeg and save them in a unique folder for each video
    # only pick videos with atleast 5 (default) actions of cleaning, and atleast one "wash" in it (clip at 60 [default] seconds)
    # use argparse for getting file name etc
    # use subprocess for ffmpeg - call extract_screenshot.sh
    # use os for creating folders
    # use csv for reading csv
    parser = argparse.ArgumentParser(description='Extract screenshots from videos')
    parser.add_argument('--seed', type=int, default=42, help='random seed')
    parser.add_argument('--csv-file', type=str, help='csv file to read from')
    parser.add_argument('--video-dir', type=str, help='directory to read videos from')
    parser.add_argument('--out-image-dir', type=str, help='directory to save screenshots to')
    parser.add_argument('--start-step', type=int, default=1, help="""
                        Steps of this pipeline:
                        1. Convert csv to json
                        2. Filter json to include dishwashing and clip at max_time
                        3. Extract screenshots from videos
                        """)
    parser.add_argument('--min-actions', type=int, default=5, help='minimum number of actions for a video to be considered')
    parser.add_argument('--max-actions', type=int, default=100, help='each episode is clipped at max-actions')
    parser.add_argument('--no-image', action='store_true', help='do not extract images, simply make prompts using action annotations')
    parser.add_argument('--json-template-file', type=str, default='epic-kitchens.json', help='json template file to use for making prompts')
    parser.add_argument('--out-json-file', type=str, required=True, help='json file to save prompts to')
    args = parser.parse_args()
    random.seed(args.seed)
    pp = pprint.PrettyPrinter(indent=4)
    df = csv.reader(open(args.csv_file, 'r'))
    video_jsons = {}
    if args.start_step > 1:
        print("Skipping convert csv to json")
        video_jsons = json.load(open(f"{args.csv_file[:-4]}.json", 'r'))
    else:
        print("Converting csv to json", end="...")
    header = True
    for row in df:
        if args.start_step > 1:
            break
        row = row[:5] + row[6:9]
        row = [x.strip() for x in row]
        if header:
            header = False
            continue
        # print(row)
        """
        0 is narration_id
        1 is participant_id
        2 is video_id
        3 is narration_timestamp
        4 is start_timestamp
        5 is start_frame
        6 is stop_frame
        7 is narration
        """
        if row[2] not in video_jsons:
            video_jsons[row[2]] = []
        try:
            video_jsons[row[2]].append({
                "narration_id": row[0],
                "participant_id": row[1],
                "timestamp": datetime.timedelta(hours=int(row[3][:2]), minutes=int(row[3][3:5]), seconds=float(row[3][6:])).total_seconds(),
                "picked_frame": random.randint(int(row[5]), int(row[6])),
                "narration": row[7]
            })
        except:
            video_jsons[row[2]].append({
                "narration_id": row[0],
                "participant_id": row[1],
                "timestamp": datetime.timedelta(hours=int(row[4][:2]), minutes=int(row[4][3:5]), seconds=float(row[4][6:])).total_seconds(),
                "picked_frame": random.randint(int(row[5]), int(row[6])),
                "narration": row[7]
            })
    if args.start_step <= 1:
        json.dump(video_jsons, open(f"{args.csv_file[:-4]}.json", 'w'))
        print("done!")
    # pp.pprint(video_jsons)
    if args.start_step > 2:
        print("Skipping filter json")
        fil_video_jsons = json.load(open(f"{args.csv_file[:-4]}_filter.json", 'r'))
    else:
        print("Filtering json", end="...")
        x = 0
        fil_video_jsons = {}
        for episode, data in video_jsons.items():
            data.sort(key=lambda x: x["picked_frame"])
        for episode, data in video_jsons.items():
            # print(episode)
            start_timestamp = min([action["timestamp"] for action in data])
            end_timestamp = max([action["timestamp"] for action in data])
            # print(start_timestamp, end_timestamp)
            idx = 0
            for i in range(len(data)//args.max_actions + 1):
                filtered_data = data[i*args.max_actions:(i+1)*args.max_actions]
                if len(filtered_data) < args.min_actions:
                    continue
                _data = [action for action in filtered_data if "wash" in action["narration"].split() or "clean" in action["narration"]]
                if not _data:
                    continue
                fil_video_jsons[episode + f"__{idx}"] = filtered_data
                idx += 1
            # can use entire episode
            x += len(filtered_data)
        print(x)
    if args.start_step <= 2:
        json.dump(fil_video_jsons, open(f"{args.csv_file[:-4]}_filter.json", 'w'), indent=4)
        print("done!")
    print(f"Total episodes - {len(fil_video_jsons)}")
    print("Extracting screenshots", end="...")
    if args.start_step > 3:
        print("Skipping extract screenshots")
        print("Exiting!")
        exit()
    else:
        template = json.load(open(args.json_template_file, 'r'))
        # template already has examples
        # examples = template["examples"]
        # for video_id, episode in examples:
            
        conversations = template["prompts"]
        i = 0
        for video_id, episode in fil_video_jsons.items():
            if i == MAX_EPISODES:
                break
            i += 1
            conversation = {}
            conversation["id"] = video_id
            person_id, *_= video_id.split('_') 
            if not args.no_image:
                v_id, *_ = video_id.split('__')
                rgb_dir = 'rgb_frames'
                if 'val' in args.csv_file:
                    rgb_dir = 'rgb_frames_val'
                conversation["tar_path"] = os.path.join(args.video_dir, person_id, rgb_dir, v_id + '.tar')
            conversation["conversations"] = []
            for action in episode:
                conversation["conversations"].append({
                    "from": "human",
                    "value": action["narration"],
                    "image": "./frame_" + ("0" * (10 - len(str(action["picked_frame"])))) + str(action["picked_frame"]) + ".jpg"
                })
            # print(len(conversation["conversations"]))
            conversations.append(conversation)
        # print(template)
        json.dump(template, open(args.out_json_file, 'w'), indent=4)
        print("done!")
