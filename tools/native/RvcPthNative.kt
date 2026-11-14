package com.ultimatervc.mobile

/** Native offline RVC v2 .pth inference bridge. */
class RvcPthNative {
    external fun convertPth(
        inputWavPath: String,
        pthModelPath: String,
        hubertModelPath: String,
        rmvpeModelPath: String,
        outputWavPath: String,
        pitchShift: Int,
    ): String?

    companion object {
        init {
            System.loadLibrary("red_rvc_pth")
        }
    }
}
