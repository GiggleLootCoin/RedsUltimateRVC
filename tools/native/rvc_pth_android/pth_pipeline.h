#ifndef RED_RVC_PTH_PIPELINE_H
#define RED_RVC_PTH_PIPELINE_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
int red_rvc_pth_convert(const char *input_wav, const char *pth_path,
                        const char *hubert_path, const char *rmvpe_path,
                        const char *output_wav, int pitch_shift,
                        char *error, size_t error_cap);
#ifdef __cplusplus
}
#endif
#endif
