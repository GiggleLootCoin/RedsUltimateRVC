package com.ultimatervc.mobile

/**
 * Experimental direct GGUF RVC runtime bridge.
 *
 * The .pth checkpoint must first be exported to the supported GGUF model format.
 * This bridge performs inference locally on CPU and never uploads audio or models.
 */
object RvcGgmlNative {
    init {
        System.loadLibrary("red_rvc_ggml")
    }

    /**
     * Returns an empty string on success, otherwise a human-readable error.
     * Required model files: HuBERT GGUF, RMVPE GGUF and voice GGUF.
     * Pass an empty indexPath to disable retrieval.
     */
    external fun convert(
        hubertPath: String,
        rmvpePath: String,
        voicePath: String,
        indexPath: String,
        inputPath: String,
        outputPath: String,
        pitch: Int,
        speakerId: Int,
        indexRate: Float,
        protect: Float,
        rmsMixRate: Float
    ): String
}
