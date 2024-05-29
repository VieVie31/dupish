import bentoml
import numpy as np
from bentoml.io import Image, NumpyNdarray
from PIL import Image as PIL_Image
from PIL import ImageOps

providers = [
    "TensorrtExecutionProvider",
    "CUDAExecutionProvider",
    "CPUExecutionProvider",
]
bento_model = bentoml.onnx.get("isc_ft_v107:latest")
runner = bento_model.with_options(providers=providers).to_runner()


svc = bentoml.Service("isc_ft_v107_duplicate_embeddings", runners=[runner])


@svc.api(input=Image(), output=NumpyNdarray())
async def isc_ft_v107_dup_ebd(img: PIL_Image) -> np.ndarray:
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
