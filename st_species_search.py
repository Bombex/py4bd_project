import base64
import json
import numpy as np
import os
import streamlit as st
import cv2
import open_clip
from dotenv import load_dotenv
import weaviate
from preprocess_data import create_embeddings
from streamlit_extras.colored_header import colored_header
from streamlit_extras.app_logo import add_logo

load_dotenv()

use_streamlit_secrets = True
if use_streamlit_secrets:
    WEAVIATE_URL = st.secrets["WEAVIATE_URL"]
    WEAVIATE_API_KEY = st.secrets["WEAVIATE_API_KEY"]
    WEAVIATE_COLLECTION = st.secrets["WEAVIATE_COLLECTION"]
    WEAVIATE_FIELDS = json.loads(st.secrets["WEAVIATE_FIELDS"])
else:
    WEAVIATE_URL = os.environ.get("WEAVIATE_URL")
    WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
    WEAVIATE_COLLECTION = os.environ.get("WEAVIATE_COLLECTION")
    WEAVIATE_FIELDS = json.loads(os.environ.get("WEAVIATE_FIELDS"))

if WEAVIATE_API_KEY is None and WEAVIATE_API_KEY is None:
    st.error(
        "Incorrect .env file. WEAVIATE_API_KEY or WEAVIATE_API_KEY is None", icon="⚠️"
    )

client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
)

model, preprocess_train, preprocess_val = open_clip.create_model_and_transforms(
    "hf-hub:imageomics/bioclip"
)

tokenizer = open_clip.get_tokenizer("hf-hub:imageomics/bioclip")


def convert_b64_to_image(image_b64_string: str) -> np.ndarray:
    img_b64_enc = bytes(image_b64_string, "utf-8")
    img_b64_dec = base64.b64decode(img_b64_enc)
    img_arr = np.frombuffer(img_b64_dec, dtype=np.uint8)
    img = cv2.imdecode(img_arr, flags=cv2.IMREAD_COLOR)
    return img


# 'with st.spinner' for animated spinner during connection to database and finding similar images
def get_similar_images(uploaded_file, num_similar_images):
    with ((st.spinner("Searching similar images... (may take up to a minute)"))):
        embedding = create_embeddings(uploaded_file, model, preprocess_val)
        nearVector = {"vector": embedding}
        result = (
            client.query.get(WEAVIATE_COLLECTION, WEAVIATE_FIELDS)
            .with_near_vector(nearVector)
            .with_limit(num_similar_images)
            .with_additional(["certainty"])
            .do()
        )
        return json.loads(json.dumps(result))


# For displaying images in three columns
# Extract data from connection and convert it to images to display
def display_results(col1, col2, col3, loaded_data, num_similar_images):
    col1.subheader("Your image")
    col1.image(uploaded_file, use_column_width=True)
    col2.subheader("Result")
    col3.subheader("ㅤ")
    for i, data in enumerate(
        loaded_data["data"]["Get"][WEAVIATE_COLLECTION][:num_similar_images]
    ):
        image_to_convert = data["image"]
        label = data["label"]
        certainty = data["_additional"]["certainty"]
        percentage_string = "{:.2%}".format(certainty)
        image = convert_b64_to_image(image_to_convert)[:, :, ::-1]
        col = col2 if i % 2 == 0 else col3
        col.image(
            image,
            caption=label + ", similarity: " + percentage_string,
            use_column_width=True,
        )


add_logo(".streamlit/mandarin.png", height=250)

st.title("BigData Team Project")

colored_header(
    label="Identify the species by uploading the image 🔎",
    description="Just upload the image, select the number of similar animals and click to start the process",
    color_name="violet-70",
)

uploaded_file = st.file_uploader("Choose the file...", type="jpg")
num_similar_images = st.slider("Amount of similar image in results", 1, 10, 6)
click = st.button("Click to start processing", disabled=not uploaded_file)

col1, col2, col3 = st.columns([2, 1, 1])

if click and uploaded_file:
    result = get_similar_images(uploaded_file, num_similar_images)
    display_results(col1, col2, col3, result, num_similar_images)
