prompt = """
a woman and a man drinking a cup of coffee in a cafe, chatting about the new restaurant around the block
"""

operation = client.models.generate_videos(
    model=video_model_fast,
    prompt=prompt,
    config=types.GenerateVideosConfig(
        reference_images=[
            types.VideoGenerationReferenceImage(
                image=types.Image.from_file(location=first_image),
                reference_type="asset",
            ),
            types.VideoGenerationReferenceImage(
                image=types.Image.from_file(location=second_image),
                reference_type="asset",
            ),
        ],
        aspect_ratio="16:9",
        number_of_videos=1,
        duration_seconds=8,
        resolution="1080p",
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.video_bytes)
#### Setting reference image

Now, you'll use a single scenery reference image and a text prompt to generate a video with different subjects and actions.
prompt = """
a Corgi walks around in a living room, then jumps on the couch and starts reading a book on the coffee table
"""

operation = client.models.generate_videos(
    model=video_model,
    prompt=prompt,
    config=types.GenerateVideosConfig(
        reference_images=[
            types.VideoGenerationReferenceImage(
                image=types.Image.from_file(location=first_image),
                reference_type="asset",
            ),
        ],
        aspect_ratio="9:16",
        number_of_videos=1,
        duration_seconds=8,
        resolution="720p",
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.video_bytes)
#### Product reference image

Next, you'll use a product reference image and a text prompt to generate a video. This will demonstrate how Veo maintains product consistency while in motion.
prompt = """
a person walks in carrying a vase full of flowers and places the vase on a kitchen table
"""

operation = client.models.generate_videos(
    model=video_model,
    prompt=prompt,
    config=types.GenerateVideosConfig(
        reference_images=[
            types.VideoGenerationReferenceImage(
                image=types.Image.from_file(location=first_image),
                reference_type="asset",
            ),
        ],
        aspect_ratio="9:16",
        number_of_videos=1,
        duration_seconds=8,
        resolution="720p",
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.video_bytes)
#### Three distinct reference images

In this example, you'll use three different reference images (a product, a subject, and a scene) from Google Cloud Storage. Instead of downloading them, you'll reference their Cloud Storage URIs directly. To use your own images, replace the gcs_uri variables below.
# fmt: off
prompt = "a wide shot of a woman wheeling a blue suitcase through a flower field"  # @param {type: 'string'}
# fmt: on
output_gcs = "gs://[your-bucket-path]"  # @param {type: 'string'}

operation = client.models.generate_videos(
    model=video_model,
    prompt=prompt,
    config=types.GenerateVideosConfig(
        reference_images=[
            types.VideoGenerationReferenceImage(
                image=types.Image(gcs_uri=first_image_gcs, mime_type="image/png"),
                reference_type="asset",
            ),
            types.VideoGenerationReferenceImage(
                image=types.Image(gcs_uri=second_image_gcs, mime_type="image/png"),
                reference_type="asset",
            ),
            types.VideoGenerationReferenceImage(
                image=types.Image(gcs_uri=third_image_gcs, mime_type="image/jpeg"),
                reference_type="asset",
            ),
        ],
        output_gcs_uri=output_gcs,
        aspect_ratio="16:9",
        number_of_videos=1,
        duration_seconds=8,
        resolution="1080p",
        person_generation="allow_adult",
        generate_audio=True,
    ),
)

while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)
    print(operation)

if operation.response:
    show_video(operation.result.generated_videos[0].video.uri)