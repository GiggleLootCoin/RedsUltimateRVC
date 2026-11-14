#include <jni.h>
#include "pth_pipeline.h"
#include <string.h>

static const char *get_utf(JNIEnv *env, jstring value) {
    return value ? (*env)->GetStringUTFChars(env, value, 0) : 0;
}
static void release_utf(JNIEnv *env, jstring value, const char *text) {
    if (value && text) (*env)->ReleaseStringUTFChars(env, value, text);
}

JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_RvcPthNative_convertPth(
    JNIEnv *env, jobject instance, jstring input, jstring pth,
    jstring hubert, jstring rmvpe, jstring output, jint pitch_shift) {
    (void)instance;
    const char *input_path = get_utf(env, input);
    const char *pth_path = get_utf(env, pth);
    const char *hubert_path = get_utf(env, hubert);
    const char *rmvpe_path = get_utf(env, rmvpe);
    const char *output_path = get_utf(env, output);
    char error[512] = {0};
    int status = -1;
    if (input_path && pth_path && hubert_path && rmvpe_path && output_path) {
        status = red_rvc_pth_convert(input_path, pth_path, hubert_path,
                                     rmvpe_path, output_path,
                                     (int)pitch_shift, error, sizeof(error));
    } else {
        strncpy(error, "Could not read the selected file paths.", sizeof(error)-1);
    }
    release_utf(env, input, input_path);
    release_utf(env, pth, pth_path);
    release_utf(env, hubert, hubert_path);
    release_utf(env, rmvpe, rmvpe_path);
    release_utf(env, output, output_path);
    return status == 0 ? NULL : (*env)->NewStringUTF(env, error[0] ? error : "Native PTH conversion failed.");
}
