import io

import numpy as np
import requests
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile

app = FastAPI()


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
    url = "http://192.168.1.17:3000/sr"
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
