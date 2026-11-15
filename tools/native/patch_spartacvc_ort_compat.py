#!/usr/bin/env python3
"""Apply narrow source-compatibility fixes to the pinned Spartacvc checkout.

The upstream inference source targets an older ONNX Runtime C API. These
changes preserve runtime behavior while matching ORT 1.28's const-correct
function signatures and C pointer qualification rules.
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

# The resblock reads model tensors but never changes them. The const qualifier
# belongs on the array's pointers, not on the pointed-to float type, so a
# float** model tensor table can be passed without an invalid nested qualifier.
replace_once(
    infer,
    "const float *w1[3], const float *b1[3], const float *g1[3],\n"
    "                      const float *w2[3], const float *b2[3], const float *g2[3],",
    "float *const w1[3], float *const b1[3], float *const g1[3],\n"
    "                      float *const w2[3], float *const b2[3], float *const g2[3],",
)

# ORT 1.28 returns a const view from CastTypeInfoToTensorInfo.
replace_once(
    onnx,
    "    OrtTensorTypeAndShapeInfo *tsi = NULL;\n"
    "    s = api->CastTypeInfoToTensorInfo(ti, &tsi);",
    "    const OrtTensorTypeAndShapeInfo *tsi = NULL;\n"
    "    s = api->CastTypeInfoToTensorInfo(ti, &tsi);",
)

# ORT 1.28 Run() takes const OrtValue inputs. Keep CreateTensor's mutable
# output in a local, then store it in the const input array.
replace_once(
    onnx,
    "    OrtValue *ort_inputs[8] = {NULL};",
    "    const OrtValue *ort_inputs[8] = {NULL};",
)
replace_once(
    onnx,
    "        OrtStatus *s = api->CreateTensorWithDataAsOrtValue(\n"
    "            (OrtMemoryInfo *)sess->ort_meminfo,\n"
    "            (void *)in->data, byte_size,\n"
    "            in->dims, (size_t)in->ndim,\n"
    "            (ONNXTensorElementDataType)in->elem_type,\n"
    "            &ort_inputs[i]);",
    "        OrtValue *created_input = NULL;\n"
    "        OrtStatus *s = api->CreateTensorWithDataAsOrtValue(\n"
    "            (OrtMemoryInfo *)sess->ort_meminfo,\n"
    "            (void *)in->data, byte_size,\n"
    "            in->dims, (size_t)in->ndim,\n"
    "            (ONNXTensorElementDataType)in->elem_type,\n"
    "            &created_input);\n"
    "        ort_inputs[i] = created_input;",
)
print("Applied checked Spartacvc C and ONNX Runtime 1.28 compatibility patches.")
