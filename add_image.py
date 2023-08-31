import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-generate-file", type=str, required=True)
    parser.add_argument("--post-generate-file", type=str, required=True)
    parser.add_argument("--output-file", type=str, required=True)


    args = parser.parse_args()
    pre_generate = json.load(open(args.pre_generate_file, 'r'))
    post_generate = json.load(open(args.post_generate_file, 'r'))
    pre_prompts = pre_generate["prompts"]
    dict_pre = {t['id']: t for t in pre_prompts}
    dict_post = {t['id']: t for t in post_generate}
    for id, v in dict_pre.items():
        if id not in dict_post:
            pass
        else:
            for k in v:
                if k not in dict_post[id]:
                    dict_post[id][k] = v[k]
            x = v["conversations"]
            y = dict_post[id]["conversations"]
            print(len(x), len(y))
            for idx_x in range(len(x)):
                y[2 * idx_x]["image"] = x[idx_x]["image"]
    output = list(dict_post.values())
    json.dump(output, open(args.output_file, 'w'), indent=4)
