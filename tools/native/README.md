# Offline song-cover native component

This component is built against the official Sherpa-ONNX C API for Android
arm64-v8a. It separates a 16-bit PCM WAV into Spleeter vocals and accompaniment,
then mixes converted vocals with the accompaniment into a new WAV.

All audio paths are app-private local files. The Spleeter model files and
Sherpa-ONNX shared libraries are packaged into the APK by the build workflow.
No audio is uploaded and no remote inference is used.

The Galaxy A12 must still be tested for peak memory, processing time, thermal
behaviour and output quality before this feature is advertised as certified.
