#!/bin/bash

video_file="$1"  # Video file name provided as the first argument
timestamps_file="$2"  # Timestamps file name provided as the second argument

while IFS= read -r timestamp; do
    formatted_timestamp=$(date -d "$timestamp" +"%Y-%m-%d_%H-%M-%S")
    output_filename="frame_${formatted_timestamp}.jpg"
    ffmpeg -i "$video_file" -ss "$timestamp" -f image2 -s 512x384 -vframes 1 "$output_filename"
done < "$timestamps_file"

