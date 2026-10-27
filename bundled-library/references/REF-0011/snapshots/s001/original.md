# fmt: off
prompt = "a hand reaches in and places a glass of milk next to the plate of cookies"  # @param {type: 'string'}
# fmt: on

operation = client.models.generate_videos(
    model=video_model,
    prompt=prompt,
    image=types.Image.from_file(location=first_frame),
    config=types.GenerateVideosConfig(
        last_frame=types.Image.from_file(location=last_frame),
        aspect_ratio="9:16",
        resolution="1080p",
        number_of_videos=1,
        duration_seconds=8,
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.video_bytes)
# fmt: off
prompt = "the chipmunk climbs down the tree to sit next to the rabbit"  # @param {type: 'string'}
# fmt: on
output_gcs = "gs://[your-bucket-path]"  # @param {type: 'string'}

operation = client.models.generate_videos(
    model=video_model,
    prompt=prompt,
    image=types.Image(gcs_uri=first_frame_gcs, mime_type="image/png"),
    config=types.GenerateVideosConfig(
        last_frame=types.Image(gcs_uri=last_frame_gcs, mime_type="image/png"),
        output_gcs_uri=output_gcs,
        aspect_ratio="16:9",
        number_of_videos=1,
        duration_seconds=6,
        resolution="1080p",
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.uri)
### Video extend

In this next example, you'll use Veo to extend an existing video. You'll use the same parameters as before. However, the following are configured differently in this instance:
- **Input video:** Since you're starting with a video, specify a Cloud Storage video location in the `video_gcs` variable.
- **Output video:** As these videos will be bigger, you'll save your output video in Cloud Storage. Include the Cloud Storage bucket in the `output_gcs` field.
- **Video duration:** You can extend your video by 7 seconds.
prompt = "a butterfly flies in and lands on the flower"  # @param {type: 'string'}
# fmt: off
video_gcs = "gs://cloud-samples-data/generative-ai/video/red-flower.mp4"  # @param {type: 'string'}
# fmt: on
output_gcs = "gs://[your-bucket-path]"  # @param {type: 'string'}

operation = client.models.generate_videos(
    model=video_extension_model,
    prompt=prompt,
    video=types.Video(uri=video_gcs, mime_type="video/mp4"),
    config=types.GenerateVideosConfig(
        output_gcs_uri=output_gcs,
        number_of_videos=1,
        duration_seconds=7,
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(5)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.uri)