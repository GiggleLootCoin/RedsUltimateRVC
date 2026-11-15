#!/usr/bin/env python3
"""Patch faiss-mobile v1.14.1 with a streaming URVCIDX1 exporter."""
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
        }""",
)
replace_once(
    java,
    "    private static native long nativeReadIndex(String path);",
    "    private static native long nativeReadIndex(String path);\n"
    "    private static native long nativeExportMobileIndex(long indexPtr, String path);",
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
    FaissIndexIVF *ivf = faiss_IndexIVF_downcast(index);
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

    const unsigned char magic[8] = {'U','R','V','C','I','D','X','1'};
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
    (*env)->ReleaseStringUTFChars(env, path, cpath);

    if (!ok) {
        remove(cpath);
        if (!(*env)->ExceptionCheck(env)) {
            throw_java_exception(env, "FAISS index conversion did not complete.");
        }
        return 0;
    }
    return (jlong)total;
}

'''
replace_once(
    jni,
    "JNI_METHOD(jint, nativeMetricL2)(JNIEnv *env, jclass cls) {",
    exporter + "JNI_METHOD(jint, nativeMetricL2)(JNIEnv *env, jclass cls) {",
)
print("Patched faiss-mobile with 768-dimension streaming mobile-index export.")
