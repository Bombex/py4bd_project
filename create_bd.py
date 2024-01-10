import os

import weaviate
from dotenv import load_dotenv

load_dotenv()

WEAVIATE_URL = os.environ.get("WEAVIATE_URL")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")

if __name__ == "__main__":
    client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
    )

    if client.schema.exists("Animals"):
        client.schema.delete_class("Animals")

    class_obj = {
        "class": "Animals",
        "description": "Images of different animals",
        "vectorizer": "none",
        "properties": [
            {
                "name": "label",
                "dataType": ["string"],
                "description": "name of animal",
            },
            {
                "name": "image",
                "dataType": ["blob"],
                "description": "image",
            },
            {
                "name": "filepath",
                "dataType": ["string"],
                "description": "filepath of the images",
            },
        ],
    }

    client.schema.create_class(class_obj)
    print(client.schema.get())
