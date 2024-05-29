import bentoml
import onnx

onnx_model = onnx.load("model_zoo/isc_ft_v107.onnx")
onnx.checker.check_model(onnx_model)


signatures = {
    "run": {"batchable": True},
    # "batch_dim": (0, 0),
}
bento_model = bentoml.onnx.save_model("isc_ft_v107", onnx_model, signatures=signatures)
