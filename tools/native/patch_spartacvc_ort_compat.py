#!/usr/bin/env python3
"""Apply narrow source-compatibility fixes to the pinned Spartacvc checkout.

The pinned source predates ONNX Runtime 1.28's const-correct C API. The
patches preserve tensor ownership and inference behavior while making the
pointer types correct for the newer API.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "spartacvc")
infer = root / "src/rvc_infer.c"
onnx = root / "src/onnx.c"

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one compatibility anchor in {path}: {old!r}; found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

# These inference routines only read model weights. Const-qualify the pointer
# slots, not the pointed-to floats, so mutable tensor tables pass safely.
replace_once(
    infer,
    "const float *w1[3], const float *b1[3], const float *g1[3],\n"
    "                      const float *w2[3], const float *b2[3], const float *g2[3],",
    "float *const w1[3], float *const b1[3], float *const g1[3],\n"
    "                      float *const w2[3], float *const b2[3], float *const g2[3],",
)
replace_once(
    infer,
    "const float *in_w[3], const float *in_b[3], const float *in_g[3],\n"
    "                    const float *rs_w[3], const float *rs_b[3], const float *rs_g[3],",
    "float *const in_w[3], float *const in_b[3], float *const in_g[3],\n"
    "                    float *const rs_w[3], float *const rs_b[3], float *const rs_g[3],",
)

# ORT 1.28 returns a const view from CastTypeInfoToTensorInfo.
replace_once(
    onnx,
    "    OrtTensorTypeAndShapeInfo *tsi = NULL;\n"
    "    s = api->CastTypeInfoToTensorInfo(ti, &tsi);",
    "    const OrtTensorTypeAndShapeInfo *tsi = NULL;\n"
    "    s = api->CastTypeInfoToTensorInfo(ti, &tsi);",
)

# Keep mutable handles for CreateTensor/ReleaseValue ownership, and provide a
# separate const view array to Run(), whose input signature is const-correct.
replace_once(
    onnx,
    "    OrtValue *ort_inputs[8] = {NULL};",
    "    OrtValue *ort_inputs[8] = {NULL};\n"
    "    const OrtValue *ort_input_values[8] = {NULL};",
)
replace_once(
    onnx,
    "        OrtStatus *s = api->CreateTensorWithDataAsOrtValue(\n"
    "            (OrtMemoryInfo *)sess->ort_meminfo,\n"
    "            (void *)in->data, byte_size,\n"
    "            in->dims, (size_t)in->ndim,\n"
    "            (ONNXTensorElementDataType)in->elem_type,\n"
    "            &ort_inputs[i]);",
    "        OrtStatus *s = api->CreateTensorWithDataAsOrtValue(\n"
    "            (OrtMemoryInfo *)sess->ort_meminfo,\n"
    "            (void *)in->data, byte_size,\n"
    "            in->dims, (size_t)in->ndim,\n"
    "            (ONNXTensorElementDataType)in->elem_type,\n"
    "            &ort_inputs[i]);\n"
    "        ort_input_values[i] = ort_inputs[i];",
)
replace_once(
    onnx,
    "        in_names,  ort_inputs,  (size_t)n_inputs,",
    "        in_names,  ort_input_values,  (size_t)n_inputs,",
)
print("Applied checked Spartacvc C and ONNX Runtime 1.28 compatibility patches.")
