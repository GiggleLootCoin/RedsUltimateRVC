package com.ultimatervc.mobile

import com.developermindset.faiss.FAISS

/** Native offline RVC v2 PTH conversion with optional real FAISS retrieval blending. */
class RvcPthNative {
    external fun convertPth(
        inputWavPath: String,
        pthModelPath: String,
        hubertModelPath: String,
        rmvpeModelPath: String,
        outputWavPath: String,
        pitchShift: Int,
        retrievalIndex: FAISS.Index?,
        indexRate: Float,
    ): String?

    companion object {
        init {
            System.loadLibrary("red_rvc_pth")
        }
    }
}
