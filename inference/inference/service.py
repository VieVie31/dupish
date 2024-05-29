import bentoml
import numpy as np
from bentoml.io import Image, NumpyNdarray
from PIL import Image as PIL_Image

providers = [
    "TensorrtExecutionProvider",
    "CUDAExecutionProvider",
    "CPUExecutionProvider",
]
bento_model = bentoml.onnx.get("isc_ft_v107:latest")
runner = bento_model.with_options(
    providers=providers,
).to_runner(
    max_batch_size=10,
    # max_latency_ms=5000
)


svc = bentoml.Service("isc_ft_v107_duplicate_embeddings", runners=[runner])


@svc.api(input=Image(), output=NumpyNdarray())
async def encode_image(img: PIL_Image) -> np.ndarray:
    img = img.convert("RGB")

    # Resize the image
    img = img.resize((512, 512), PIL_Image.BILINEAR)

    # Convert image to numpy array
    img_np = np.array(img).astype(np.float32) / 255.0

    # Normalize
    mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
    std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
    img_np = (img_np - mean) / std
    img_np = img_np.transpose(2, 0, 1)
    img_np = np.expand_dims(img_np, 0)  # add batch_size

    sr_arr = await runner.run.async_run(img_np)
    sr_arr = np.squeeze(sr_arr)  # remove batch_size dims
    return sr_arr


if 0:
    import io
    import random
    import time
    from multiprocessing.dummy import Pool as ThreadPool

    import requests

    def get_pred(path):
        f = open(path, "rb")
        d = io.BytesIO(f.read())

        headers = {
            "accept": "application/json",
            "Content-Type": "image/xpm",
        }

        r = requests.post(
            "http://localhost:3000/encode_image", headers=headers, data=d.getvalue()
        )
        return time.time(), r.status_code

    pool = ThreadPool(10)
    results = list(
        pool.map(
            get_pred, ["a.jpg" if random.randint(0, 1) else "b.jpg" for _ in range(100)]
        )
    )

    results = np.array(results)

    results.T[1]

    plt.plot(results.T[0])
    plt.scatter(
        np.arange(100)[results.T[1] == 200],
        results.T[0][results.T[1] == 200],
        c="green",
    )
    plt.scatter(
        np.arange(100)[results.T[1] != 200],
        results.T[0][results.T[1] != 200],
        c="red",
        marker="x",
    )
    plt.show()

    plt.plot(list(zip(*results))[0])
    plt.show()

    plt.plot(list(zip(*results))[1])
    plt.show()
