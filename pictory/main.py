import os
import base64
from openai import OpenAI

# 1. Setup OpenAI client using your API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. List all image files in the images folder
def get_image_paths(folder="images"):
    files = []
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".avif")):
            files.append(os.path.join(folder, name))
    return files
# 3. Convert an image to base64 string (needed to send to the API)
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")

# 4. Ask GPT-4 to describe a single image
def describe_image(image_path):
    print(f"\nDescribing image: {image_path}")
    image_b64 = encode_image_to_base64(image_path)

    # Try to guess the image type from the extension
    ext = image_path.lower().split(".")[-1]
    if ext == "png":
        mime_type = "image/png"
    elif ext == "webp":
        mime_type = "image/webp"
    elif ext == "avif":
        mime_type = "image/avif"
    else:
        mime_type = "image/jpeg"

    prompt_text = (
        "Describe this image in 2–3 sentences. "
        "Focus on: who is in the scene, what they are doing, "
        "the mood or emotion, and the setting (place, time of day)."
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # vision-capable model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}"
                        },
                    },
                ],
            }
        ],
        max_tokens=200,
    )

    description = response.choices[0].message.content
    print("  ->", description)
    return description


# 5. Generate a story using all image descriptions
def generate_story(descriptions):
    caption_list = ""
    for i, desc in enumerate(descriptions, start=1):
        caption_list += f"{i}. {desc}\n"

    story_prompt = f"""
I have a sequence of images with these descriptions:

{caption_list}

Write a single coherent story that:
- Uses this order as beginning, middle, and end
- Introduces characters and setting in the first description
- Creates some problem or adventure in the middle
- Resolves it nicely in the end
- Includes some dialogue and emotions
- Feels like a short storybook

Target length: 500–800 words.
Tone: warm, imaginative, slightly cinematic.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # you can change to gpt-4.1 if you have access
        messages=[
            {"role": "system", "content": "You are a creative story writer."},
            {"role": "user", "content": story_prompt},
        ],
        max_tokens=1200,
    )

    story = response.choices[0].message.content
    return story

# 6. Main function to run everything
def main():
    # Get all images in the images folder
    image_paths = [
        "images/1_inv.jpg.webp",   # Jerry first
        "images/2_im.jpg.webp",    # Presentation guy second
    ]

    if not image_paths:
        print("No images found in ./images. Please add some JPG/PNG files.")
        return

    print("Found these images:")
    for p in image_paths:
        print(" -", p)

    # Step A: Get descriptions for each image
    descriptions = []
    for path in image_paths:
        desc = describe_image(path)
        descriptions.append(desc)

    # Step B: Generate a story from all descriptions
    print("\nGenerating story from image descriptions...")
    story = generate_story(descriptions)

    # Step C: Print and save story
    print("\n=== FINAL STORY ===\n")
    print(story)

    with open("story.txt", "w", encoding="utf-8") as f:
        f.write(story)

    print("\nStory saved to story.txt")

if __name__ == "__main__":
    main()
