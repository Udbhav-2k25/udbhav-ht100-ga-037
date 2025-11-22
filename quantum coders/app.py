import os
import base64
from openai import OpenAI
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(
    page_title="Pictory – Photo to Story",
    page_icon="📖",
    layout="centered",
)
# ---- Animated Gradient Background ----
st.markdown("""
    <style>
    @keyframes gradientAnimation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stApp {
        background: 
            radial-gradient(circle at 20% 30%, rgba(255, 183, 77, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(255, 138, 101, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(255, 107, 107, 0.2) 0%, transparent 50%),
            repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(255, 255, 255, 0.03) 40px, rgba(255, 255, 255, 0.03) 80px),
            linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 25%, #f06595 50%, #ff8c42 75%, #ffa94d 100%);
        background-size: 400% 400%;
        animation: gradientAnimation 15s ease infinite;
        background-attachment: fixed;
    }
    </style>
    """, unsafe_allow_html=True)


# ---------- OpenAI Setup ----------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- Helper: encode image to base64 for vision ----------
def encode_image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

# ---------- Describe a single uploaded image ----------
def describe_uploaded_image(uploaded_file):
    image_bytes = uploaded_file.read()
    image_b64 = encode_image_bytes_to_base64(image_bytes)
    mime_type = uploaded_file.type or "image/jpeg"

    prompt_text = (
        "Describe this image in 2–3 sentences. "
        "Focus on: who is in the scene, what they are doing, "
        "the mood or emotion, and the setting (place, time of day)."
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
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

    return response.choices[0].message.content

# ---------- Story planner ----------
def plan_story_outline(descriptions, tone, length_choice, audience):
    caption_list = ""
    for i, desc in enumerate(descriptions, start=1):
        caption_list += f"{i}. {desc}\n"

    if "Short" in length_choice:
        length_instruction = "short and focused"
    elif "Long" in length_choice:
        length_instruction = "detailed and long"
    else:
        length_instruction = "medium length"

    prompt = f"""
You are a story planner (not the final writer).

The user has a sequence of images with these descriptions:

{caption_list}

The final story should be:
- Tone: {tone}
- Audience: {audience}
- Length: {length_instruction}

Your job is to plan a story outline, NOT to write the full story.
Return a structured outline in this JSON-like format:

characters: [list of main character names]
setting: a short description of time and place
plot_beats:
  - one sentence for what happens in image 1
  - one sentence for what happens in image 2
  - ...
theme: a short sentence about the main theme or message
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an expert story planner."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=600,
    )

    return response.choices[0].message.content

# ---------- Final story generator ----------
def generate_story(descriptions, tone, length_choice, audience):
    outline = plan_story_outline(descriptions, tone, length_choice, audience)

    caption_list = ""
    for i, desc in enumerate(descriptions, start=1):
        caption_list += f"{i}. {desc}\n"

    if "Short" in length_choice:
        length_instruction = "about 300–500 words"
    elif "Long" in length_choice:
        length_instruction = "about 800–1200 words"
    else:
        length_instruction = "about 500–800 words"

    story_prompt = f"""
You are a creative story writer.

You will be given:
1) A sequence of image descriptions
2) A story outline created by a planner model
3) Desired tone, audience, and length

IMAGE DESCRIPTIONS:
{caption_list}

OUTLINE (from planner model):
{outline}

Write a single coherent story that:
- Follows the OUTLINE closely
- Uses the images in order as beginning, middle, and end
- Introduces characters and setting clearly
- Creates a problem or adventure in the middle
- Resolves it nicely at the end
- Includes some dialogue and emotions
- Feels like a short storybook.

Tone: {tone}
Audience: {audience}
Target length: {length_instruction}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a creative story writer."},
            {"role": "user", "content": story_prompt},
        ],
        max_tokens=1600,
    )

    return response.choices[0].message.content

# ---------- Streamlit UI ----------
def main():
    st.title("Pictory – Photo to Story")
    st.write("Upload your images, choose style, and let AI turn them into a story.")

    uploaded_files = st.file_uploader(
        "Step 1 ▸ Upload 2–10 images (png / jpg / jpeg / webp):",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    tone = st.selectbox(
        "Step 2 ▸ Choose story tone:",
        ["Warm & Wholesome", "Funny", "Adventure", "Fantasy"],
    )

    length_choice = st.selectbox(
        "Step 2 ▸ Choose story length:",
        ["Short (300–500 words)", "Medium (500–800 words)", "Long (800–1200 words)"],
    )

    audience = st.selectbox(
        "Step 2 ▸ Target audience:",
        ["Kids", "Teens", "Adults", "General"],
    )

    if uploaded_files:
        st.info(f"You uploaded {len(uploaded_files)} image(s). They will be used in this order.")
        for i, f in enumerate(uploaded_files, start=1):
            st.write(f"{i}. **{f.name}**")

        if st.button("🚀 Generate Story"):
            descriptions = []
            with st.spinner("Analyzing images and writing your story..."):
                for f in uploaded_files:
                    desc = describe_uploaded_image(f)
                    descriptions.append(desc)

                story = generate_story(descriptions, tone, length_choice, audience)

            st.subheader("📚 Your Story")
            st.write(story)

            st.download_button(
                label="💾 Download Story as .txt",
                data=story,
                file_name="pictory_story.txt",
                mime="text/plain",
            )

            with st.expander("🔍 Show image descriptions used for the story"):
                for i, desc in enumerate(descriptions, start=1):
                    st.markdown(f"**Image {i}:** {desc}")
    else:
        st.warning("Please upload at least 2 images to enable story generation.")

if __name__ == "__main__":
    main()
