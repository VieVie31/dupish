import hashlib
import io
import json

import numpy as np
import requests
import weaviate
import weaviate.classes as wvc
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from PIL import Image
from weaviate.classes.config import Configure, DataType, Property, VectorDistances
from weaviate.classes.query import Filter, MetadataQuery

from .clients import (
    generate_presigned_url,
    get_redis_client,
    get_s3_client,
    get_weaviate_client,
)
from .settings import redis_settings, s3_settings, weaviate_settings

app = FastAPI()

s3_client = get_s3_client(s3_settings)
weaviate_client = get_weaviate_client(weaviate_settings)
redis_client = get_redis_client(redis_settings, decode_response=False)


# Create the weaviate collection if not exists
if not "UploadedImages" in list(weaviate_client.collections.list_all().keys()):
    weaviate_client.collections.create(
        "UploadedImages",
        properties=[
            Property(name="title", data_type=DataType.TEXT),
            Property(name="s3_key", data_type=DataType.TEXT),
        ],
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE
        ),
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
    )


@app.get("/")
def read_root():
    return {"Hello": "World"}


# check if two images are duplicate
@app.post("/check-are-duplicate")
def check_are_duplicate(im1: UploadFile = File(...), im2: UploadFile = File(...)):
    # get the image data
    im1_data = io.BytesIO(im1.file.read())
    im2_data = io.BytesIO(im2.file.read())

    # check if the images are duplicate
    url = "http://dupish:3000/encode_image"  # 192.168.1.17
    headers = {
        "accept": "application/json",
        "Content-Type": "image/xpm",
    }

    response_1 = requests.post(url, headers=headers, data=im1_data.getvalue())
    response_2 = requests.post(url, headers=headers, data=im2_data.getvalue())

    response_1 = np.array(response_1.json())
    response_2 = np.array(response_2.json())

    response_1 = response_1 / np.linalg.norm(response_1)
    response_2 = response_2 / np.linalg.norm(response_2)

    return {"are_duplicate": np.dot(response_1, response_2)}  # > 0.9


def is_image(content):
    try:
        Image.open(io.BytesIO(content))
        return True
    except Exception as e:
        return False


@app.post("/upload-image")
async def upload_image(img_title: str, file: UploadFile = File(...)):
    # Read the file content
    content = await file.read()

    # Check file size, must be less than 2MB
    # FIXME: add the limit in fastapi settings
    if len(content) > 2 * 1024 * 1024:  # 2MB limit
        raise HTTPException(status_code=413, detail="File size exceeds 2MB limit")

    # Check fot the size limit and if the file is an image
    if not is_image(content):
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Generate the S3 key (filename in the bucket) and the file's SHA1 hash
    sha1_hash = hashlib.sha1(content).hexdigest()
    s3_key = f"{sha1_hash[:2]}/{sha1_hash[2:4]}/{sha1_hash[4:6]}/{sha1_hash}"

    # Get the signature of the image
    url = "http://dupish:3000/encode_image"  # 192.168.1.17
    headers = {
        "accept": "application/json",
        "Content-Type": "image/xpm",
    }

    r = requests.post(url, headers=headers, data=content)
    assert r.status_code == 200, f"Failed to get the image signature: {r.text}"

    ebd = np.array(r.json())
    ebd = ebd / np.linalg.norm(ebd)

    # Get the nearest image on weaviate
    uploaded_images_collection = weaviate_client.collections.get("UploadedImages")

    retrieved_most_similar_image = uploaded_images_collection.query.near_vector(
        near_vector=ebd.astype(float).tolist(),
        limit=1,
        distance=0.15,  # max accepted distance
        return_metadata=MetadataQuery(distance=True, creation_time=True),
        include_vector=False,
    )

    # Similar image already exists: refuse to add duplicate
    if len(retrieved_most_similar_image.objects) > 0:
        url = generate_presigned_url(
            s3_client,
            s3_settings.BUCKET_MEDIA,
            retrieved_most_similar_image.objects[0].properties["s3_key"],
            200,
        )  # TODO: change the host to the public host name of the generated pre-signed url…
        raise HTTPException(
            status_code=409,  # conflict
            detail=json.dumps(
                {
                    "error": "Duplicate image",
                    "most_similar_image": url,
                }
            ),
        )

    # Add the image into weaviate
    inserted_uuid = uploaded_images_collection.data.insert(
        properties={"title": img_title, "s3_key": s3_key},
        vector=ebd.astype(float).tolist(),
    )

    # Upload the file to S3
    response = s3_client.put_object(
        Bucket=s3_settings.BUCKET_MEDIA, Key=s3_key, Body=content
    )

    return {"key": s3_key, "uuid": str(inserted_uuid)}
