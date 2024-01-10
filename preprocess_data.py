import argparse
import base64
import os
from glob import glob

import open_clip
import torch
import weaviate
from dotenv import load_dotenv
from PIL import Image
from tqdm import tqdm

load_dotenv()

WEAVIATE_URL = os.environ.get("WEAVIATE_URL")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=str,
        help="Absolute path to folder with data",
        required=True,
    )
    parser.add_argument(
        "-col_name",
        "--collection_name",
        type=str,
        help="Collection name in DB",
        required=False,
        default="Animals",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        help="Batch size to add to DB",
        required=False,
        default=100,
    )
    args = parser.parse_args()

    return args


def get_images_labels(path):
    labels = {}
    for folder in glob(os.path.join(path, "*")):
        label = os.path.basename(folder)
        img_paths = glob(os.path.join(folder, "*"))
        labels[label] = img_paths
    return labels


@torch.no_grad()
def create_embeddings(img_path, model, preprocess, device_type="cpu"):
    image = Image.open(img_path)
    preprocessed_image = preprocess(image).unsqueeze(0)

    with torch.autocast(device_type):
        image_features = model.encode_image(preprocessed_image)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    return image_features


def convert_image_to_b64(image_path):
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read())
    base64_string = base64_encoded_data.decode("utf-8")
    return base64_string


def connect_to_db(collection_name: str):
    client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
    )

    if client.schema.exists(collection_name):
        return client
    else:
        return "Collection isn't exists"


def add_data_to_db(
    data, client: weaviate.client.Client, collection_name: str, batch_size: int
):
    client.batch.configure(batch_size=batch_size, timeout_retries=5)
    with client.batch as batch:
        properties = {
            "label": data["label"],
            "img_name": data["filepath"],
        }

        batch.add_data_object(properties, collection_name, vector=data["vector"])


if __name__ == "__main__":
    args = parse_args()

    model, preprocess_train, preprocess_val = open_clip.create_model_and_transforms(
        "hf-hub:imageomics/bioclip"
    )
    tokenizer = open_clip.get_tokenizer("hf-hub:imageomics/bioclip")

    client = connect_to_db(args.collection_name)

    labels = get_images_labels(args.path)
    labels = dict(list(labels.items())[81:])

    for label, paths in tqdm(labels.items()):
        for i, img_path in enumerate(paths):
            img_name = os.path.basename(img_path)
            base64_encoding = convert_image_to_b64(img_path)

            print(f"importing image: {i+1}, image name: {img_name}")

            img_embedding = create_embeddings(img_path, model, preprocess_val)
            data = {
                "label": label,
                "image": base64_encoding,
                "filepath": img_name,
                "vector": img_embedding,
            }
            add_data_to_db(data, client, args.collection_name, args.batch_size)
