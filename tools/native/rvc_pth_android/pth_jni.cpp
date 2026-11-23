#include <jni.h>
#include "pth_pipeline.h"
#include <stdint.h>
#include <string.h>

static const char *get_utf(JNIEnv *env, jstring value) {
    return value ? env->GetStringUTFChars(value, 0) : 0;
}
static void release_utf(JNIEnv *env, jstring value, const char *text) {
    if (value && text) env->ReleaseStringUTFChars(value, text);
}

typedef struct {
    JNIEnv *env;
    jobject index;
    jmethodID search_and_blend;
} faiss_blend_context;

static int blend_with_faiss(void *opaque, float *features, int frames, float rate) {
    faiss_blend_context *context = (faiss_blend_context *)opaque;
    if (!context || !context->env || !context->index || !context->search_and_blend ||
        !features || frames <= 0 || frames > 60000) return -1;

    JNIEnv *env = context->env;
    const jsize length = (jsize)(frames * 768);
    jfloatArray array = env->NewFloatArray(length);
    if (!array) return -1;
    env->SetFloatArrayRegion(array, 0, length, features);
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
        env->DeleteLocalRef(array);
        return -1;
    }

    env->CallVoidMethod(context->index, context->search_and_blend,
                        (jint)frames, array, (jint)8, (jfloat)rate);
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
        env->DeleteLocalRef(array);
        return -1;
    }
    env->GetFloatArrayRegion(array, 0, length, features);
    const int failed = env->ExceptionCheck() ? 1 : 0;
    if (failed) env->ExceptionClear();
    env->DeleteLocalRef(array);
    return failed ? -1 : 0;
}

JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_RvcPthNative_convertPth(
    JNIEnv *env, jobject instance, jstring input, jstring pth,
    jstring hubert, jstring rmvpe, jstring output, jint pitch_shift,
    jobject faiss_index, jfloat index_rate) {
    (void)instance;
    const char *input_path = get_utf(env, input);
    const char *pth_path = get_utf(env, pth);
    const char *hubert_path = get_utf(env, hubert);
    const char *rmvpe_path = get_utf(env, rmvpe);
    const char *output_path = get_utf(env, output);
    char error[512] = {0};
    int status = -1;

    faiss_blend_context blend = {0};
    if (faiss_index) {
        jclass index_class = env->GetObjectClass(faiss_index);
        if (index_class) {
            blend.env = env;
            blend.index = faiss_index;
            blend.search_and_blend = env->GetMethodID(index_class, "searchAndBlend", "(I[FIF)V");
            env->DeleteLocalRef(index_class);
        }
        if (!blend.search_and_blend || env->ExceptionCheck()) {
            if (env->ExceptionCheck()) env->ExceptionClear();
            strncpy(error, "The bundled FAISS retrieval engine is missing its RVC blending method.", sizeof(error)-1);
        }
    }

    if (input_path && pth_path && hubert_path && rmvpe_path && output_path &&
        (!faiss_index || blend.search_and_blend)) {
        status = red_rvc_pth_convert(input_path, pth_path, hubert_path,
                                     rmvpe_path, output_path,
                                     (int)pitch_shift, (float)index_rate,
                                     faiss_index ? blend_with_faiss : NULL,
                                     faiss_index ? &blend : NULL,
                                     error, sizeof(error));
    } else if (!error[0]) {
        strncpy(error, "Could not read the selected file paths.", sizeof(error)-1);
    }

    release_utf(env, input, input_path);
    release_utf(env, pth, pth_path);
    release_utf(env, hubert, hubert_path);
    release_utf(env, rmvpe, rmvpe_path);
    release_utf(env, output, output_path);
    return status == 0 ? NULL : env->NewStringUTF(error[0] ? error : "Native PTH conversion failed.");
}
