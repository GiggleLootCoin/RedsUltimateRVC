#!/usr/bin/env python3
"""Patch FAISS with local mobile-index export and native RVC retrieval blending."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / "android/java/com/developermindset/faiss/FAISS.java"
jni = root / "android/jni/faiss_jni.c"

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected one FAISS patch anchor in {path}: {old[:100]!r}; found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

replace_once(
    java,
    """        public void writeIndex(String path) {
            checkNotClosed();
            nativeWriteIndex(nativePtr, path);
        }""",
    """        public void writeIndex(String path) {
            checkNotClosed();
            nativeWriteIndex(nativePtr, path);
        }

        /**
         * Export 768-dimensional vectors to the offline RVC mobile index format.
         * IVF indexes get a direct map first; vectors are written one at a time.
         */
        public long exportMobileIndex(String path) {
            checkNotClosed();
            return nativeExportMobileIndex(nativePtr, path);
        }

        /** Prepare IVF indexes for stable vector reconstruction during RVC retrieval. */
        public void prepareForRvc() {
            checkNotClosed();
            nativePrepareForRvc(nativePtr);
        }

        /**
         * Apply FAISS retrieval blending directly to ContentVec phone features.
         * features is row-major [nq, 768] and is modified in place.
         */
        public void searchAndBlend(int nq, float[] features, int k, float indexRate) {
            checkNotClosed();
            nativeSearchAndBlend(nativePtr, nq, features, k, indexRate);
        }""",
)
replace_once(
    java,
    "    private static native long nativeReadIndex(String path);",
    "    private static native long nativeReadIndex(String path);\n"
    "    private static native long nativeExportMobileIndex(long indexPtr, String path);\n"
    "    private static native void nativePrepareForRvc(long indexPtr);\n"
    "    private static native void nativeSearchAndBlend(long indexPtr, int nq, float[] features, int k, float indexRate);",
)

replace_once(jni, "#include <stdlib.h>\n", "#include <stdlib.h>\n#include <stdint.h>\n#include <stdio.h>\n#include <limits.h>\n")
replace_once(jni, "#include <Index_c.h>\n", "#include <Index_c.h>\n#include <IndexIVF_c.h>\n")

exporter = r'''
JNI_METHOD(jlong, nativeExportMobileIndex)(JNIEnv *env, jclass cls, jlong indexPtr, jstring path) {
    FaissIndex *index = (FaissIndex *)(intptr_t)indexPtr;
    if (!index) {
        throw_java_exception(env, "The FAISS index is not open.");
        return 0;
    }

    const char *cpath = (*env)->GetStringUTFChars(env, path, NULL);
    if (!cpath) return 0;

    int dimension = faiss_Index_d(index);
    idx_t total = faiss_Index_ntotal(index);
    if (dimension != 768) {
        (*env)->ReleaseStringUTFChars(env, path, cpath);
        throw_java_exception(env, "This index is not 768-dimensional RVC v2 data.");
        return 0;
    }
    if (total <= 0 || total > INT32_MAX || !faiss_Index_is_trained(index)) {
        (*env)->ReleaseStringUTFChars(env, path, cpath);
        throw_java_exception(env, "The FAISS index is empty, untrained or too large.");
        return 0;
    }

    /* Standard RVC IVF indexes commonly omit a direct map. Build one so
       reconstruct() can retrieve each original vector by its sequential ID. */
    FaissIndexIVF *ivf = faiss_IndexIVF_cast(index);
    if (ivf && check_faiss_error(env, faiss_IndexIVF_make_direct_map(ivf, 1))) {
        (*env)->ReleaseStringUTFChars(env, path, cpath);
        return 0;
    }

    FILE *out = fopen(cpath, "wb");
    if (!out) {
        (*env)->ReleaseStringUTFChars(env, path, cpath);
        throw_java_exception(env, "Could not create the converted mobile index file.");
        return 0;
    }

    const unsigned char magic[8] = "URVCIDX1";
    const uint32_t count = (uint32_t)total;
    const unsigned char count_bytes[4] = {
        (unsigned char)(count & 0xff),
        (unsigned char)((count >> 8) & 0xff),
        (unsigned char)((count >> 16) & 0xff),
        (unsigned char)((count >> 24) & 0xff)
    };
    int ok = fwrite(magic, 1, sizeof(magic), out) == sizeof(magic) &&
             fwrite(count_bytes, 1, sizeof(count_bytes), out) == sizeof(count_bytes);

    float *vector = (float *)malloc(sizeof(float) * (size_t)dimension);
    if (!vector) {
        ok = 0;
        throw_java_exception(env, "Not enough memory to convert this FAISS index.");
    }

    for (idx_t row = 0; ok && row < total; ++row) {
        int rc = faiss_Index_reconstruct(index, row, vector);
        if (check_faiss_error(env, rc)) {
            ok = 0;
            break;
        }
        if (fwrite(vector, sizeof(float), (size_t)dimension, out) != (size_t)dimension) {
            throw_java_exception(env, "Could not write the converted mobile index.");
            ok = 0;
            break;
        }
    }

    free(vector);
    if (fflush(out) != 0) ok = 0;
    if (fclose(out) != 0) ok = 0;
    if (!ok) {
        remove(cpath);
        (*env)->ReleaseStringUTFChars(env, path, cpath);
        if (!(*env)->ExceptionCheck(env)) {
            throw_java_exception(env, "FAISS index conversion did not complete.");
        }
        return 0;
    }
    (*env)->ReleaseStringUTFChars(env, path, cpath);
    return (jlong)total;
}

'''
retrieval_methods = r'''
JNI_METHOD(void, nativePrepareForRvc)(JNIEnv *env, jclass cls, jlong indexPtr) {
    (void)cls;
    FaissIndex *index = (FaissIndex *)(intptr_t)indexPtr;
    if (!index || faiss_Index_d(index) != 768 || !faiss_Index_is_trained(index)) {
        throw_java_exception(env, "The RVC retrieval index must be a trained 768-dimensional FAISS index.");
        return;
    }
    FaissIndexIVF *ivf = faiss_IndexIVF_cast(index);
    if (ivf) check_faiss_error(env, faiss_IndexIVF_make_direct_map(ivf, 1));
}

JNI_METHOD(void, nativeSearchAndBlend)(JNIEnv *env, jclass cls, jlong indexPtr,
                                       jint nq, jfloatArray featureArray, jint k, jfloat indexRate) {
    (void)cls;
    FaissIndex *index = (FaissIndex *)(intptr_t)indexPtr;
    if (!index || !featureArray || nq <= 0 || k <= 0 || k > 16 ||
        faiss_Index_d(index) != 768 || (*env)->GetArrayLength(env, featureArray) != nq * 768) {
        throw_java_exception(env, "Invalid FAISS RVC retrieval request.");
        return;
    }
    if (indexRate <= 0.0f) return;
    if (indexRate > 1.0f) indexRate = 1.0f;

    jfloat *features = (*env)->GetFloatArrayElements(env, featureArray, NULL);
    if (!features) return;
    const size_t neighbor_count = (size_t)nq * (size_t)k;
    float *distances = (float *)malloc(neighbor_count * sizeof(float));
    idx_t *labels = (idx_t *)malloc(neighbor_count * sizeof(idx_t));
    float *retrieved = (float *)malloc(768u * sizeof(float));
    if (!distances || !labels || !retrieved) {
        free(distances); free(labels); free(retrieved);
        (*env)->ReleaseFloatArrayElements(env, featureArray, features, JNI_ABORT);
        throw_java_exception(env, "Not enough memory for FAISS retrieval blending.");
        return;
    }

    int rc = faiss_Index_search(index, (idx_t)nq, features, (idx_t)k, distances, labels);
    if (rc != 0) {
        free(distances); free(labels); free(retrieved);
        (*env)->ReleaseFloatArrayElements(env, featureArray, features, JNI_ABORT);
        check_faiss_error(env, rc);
        return;
    }

    for (int q = 0; q < nq; ++q) {
        double weight_sum = 0.0;
        double accum[768] = {0};
        for (int j = 0; j < k; ++j) {
            const size_t at = (size_t)q * (size_t)k + (size_t)j;
            const idx_t label = labels[at];
            if (label < 0) continue;
            rc = faiss_Index_reconstruct(index, label, retrieved);
            if (rc != 0) {
                free(distances); free(labels); free(retrieved);
                (*env)->ReleaseFloatArrayElements(env, featureArray, features, JNI_ABORT);
                check_faiss_error(env, rc);
                return;
            }
            double distance = distances[at];
            if (distance < 0.0) distance = 0.0;
            const double weight = 1.0 / ((distance + 1.0e-6) * (distance + 1.0e-6));
            weight_sum += weight;
            for (int d = 0; d < 768; ++d) accum[d] += (double)retrieved[d] * weight;
        }
        if (weight_sum > 0.0) {
            const size_t offset = (size_t)q * 768u;
            for (int d = 0; d < 768; ++d) {
                const float neighbor = (float)(accum[d] / weight_sum);
                features[offset + (size_t)d] =
                    features[offset + (size_t)d] * (1.0f - indexRate) + neighbor * indexRate;
            }
        }
    }

    free(distances); free(labels); free(retrieved);
    (*env)->ReleaseFloatArrayElements(env, featureArray, features, 0);
}

'''
replace_once(
    jni,
    "JNI_METHOD(jint, nativeMetricL2)(JNIEnv *env, jclass cls) {",
    exporter + retrieval_methods + "JNI_METHOD(jint, nativeMetricL2)(JNIEnv *env, jclass cls) {",
)
print("Patched FAISS with mobile-index export and native RVC retrieval blending.")
