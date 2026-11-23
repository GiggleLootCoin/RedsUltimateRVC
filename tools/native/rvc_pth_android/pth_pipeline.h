#ifndef RED_RVC_PTH_PIPELINE_H
#define RED_RVC_PTH_PIPELINE_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef int (*red_rvc_index_blend_fn)(void *context, float *phone_features,
                                      int frame_count, float index_rate);

int red_rvc_pth_convert(const char *input_wav, const char *pth_path,
                        const char *hubert_path, const char *rmvpe_path,
                        const char *output_wav, int pitch_shift,
                        float index_rate, red_rvc_index_blend_fn blend_index,
                        void *index_context, char *error, size_t error_cap);
#ifdef __cplusplus
}
#endif
#endif
