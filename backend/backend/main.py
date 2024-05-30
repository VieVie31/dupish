import hashlib
import io

import numpy as np
import requests
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from PIL import Image

from .clients import get_s3_client
from .settings import s3_settings

app = FastAPI()

s3_client = get_s3_client(s3_settings)


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
async def upload_image(file: UploadFile = File(...)):
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

    # Upload the file to S3
    response = s3_client.put_object(
        Bucket=s3_settings.BUCKET_MEDIA, Key=s3_key, Body=content
    )

    return {"key": s3_key}
