package com.ultimatervc.mobile

/**
 * Local-only Spleeter bridge. The ONNX models and native libraries are packaged
 * in the APK; audio paths always point to app-private storage.
 */
object SourceSeparationBridge {
    init {
        System.loadLibrary("onnxruntime")
        System.loadLibrary("sherpa-onnx-c-api")
        System.loadLibrary("red_source_separation")
    }

    @JvmStatic external fun separateWav(
        inputPath: String,
        vocalsPath: String,
        accompanimentPath: String,
        vocalsModelPath: String,
        accompanimentModelPath: String,
        numThreads: Int,
    ): String

    @JvmStatic external fun mixWav(
        convertedVocalsPath: String,
        accompanimentPath: String,
        outputPath: String,
        vocalGain: Float,
        accompanimentGain: Float,
    ): String
}
