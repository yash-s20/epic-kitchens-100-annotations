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
    parser.add_argument('--start-step', type=int, default=1, help="""
                        Steps of this pipeline:
                        1. Convert csv to json
                        2. Filter json to include dishwashing and clip at max_time
                        3. Extract screenshots from videos
                        """)
    parser.add_argument("--object-data-dir", required=True)
    parser.add_argument('--min-actions', type=int, default=1, help='minimum number of actions for a video to be considered')
    parser.add_argument('--max-actions', type=int, default=100, help='each episode is clipped at max-actions')
    parser.add_argument('--no-image', action='store_true', help='do not extract images, simply make prompts using action annotations')
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
    object_annotation_jsons = {}
    dropped_actions = 0
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
        video_id = row[2]
        if video_id not in object_annotation_jsons:
            object_file = os.path.join(args.object_data_dir, video_id + "-new.json")
            if not os.path.isfile(object_file):
                continue
            video_annotations = json.load(open(object_file, 'r'))['video_annotations']
            frame_to_objects = {}
            for frame in video_annotations:
                frame_no = int(frame['image']['name'].split('frame_')[1][:-4])
                frame_to_objects[frame_no] = [objct['name'] for objct in frame['annotations']]
            # print(frame_to_objects)
            object_annotation_jsons[video_id] = frame_to_objects
        possible_frames = list(filter(lambda x: int(row[5]) <= x <= int(row[6]), object_annotation_jsons[video_id].keys()))
        if not possible_frames:
            dropped_actions += 1
            continue
        picked_frame = random.choice(list(possible_frames))
        if video_id not in video_jsons:
            video_jsons[video_id] = []
        try:
            video_jsons[video_id].append({
                "narration_id": row[0],
                "participant_id": row[1],
                "timestamp": datetime.timedelta(hours=int(row[3][:2]), minutes=int(row[3][3:5]), seconds=float(row[3][6:])).total_seconds(),
                "picked_frame": picked_frame,
                "start_frame": int(row[5]),
                "end_frame": int(row[6]),
                "narration": row[7],
                "objects": object_annotation_jsons[video_id][picked_frame]
            })
        except:
            video_jsons[video_id].append({
                "narration_id": row[0],
                "participant_id": row[1],
                "timestamp": datetime.timedelta(hours=int(row[4][:2]), minutes=int(row[4][3:5]), seconds=float(row[4][6:])).total_seconds(),
                "picked_frame": picked_frame,
                "start_frame": int(row[5]),
                "end_frame": int(row[6]),
                "narration": row[7],
                "objects": object_annotation_jsons[video_id][picked_frame]
            })
    print(f"Dropped actions due to lack of object annotation: {dropped_actions}")
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
        x = []
        for vid_id in fil_video_jsons:
            vid = vid_id.split('__')[0]
            pid = vid_id.split('_')[0]
            x.extend([{
                "ep_id": vid_id,
                "id": nar["narration_id"],
                "tar_path": os.path.join(args.video_dir, pid, 'rgb_frames', vid + '.tar'),
                "image": "./frame_" + "0" * (10 - len(str(nar["picked_frame"]))) + str(nar["picked_frame"]) + ".jpg",
                "start_image": "./frame_" + "0" * (10 - len(str(nar["start_frame"]))) + str(nar["start_frame"]) + ".jpg",
                "end_image": "./frame_" + "0" * (10 - len(str(nar["end_frame"]))) + str(nar["end_frame"]) + ".jpg",
                "action": nar["narration"],
                "objects": nar["objects"]
                } for nar in fil_video_jsons[vid_id]])
        json.dump(x, open(args.out_json_file, 'w'), indent=4)
        print("done!")