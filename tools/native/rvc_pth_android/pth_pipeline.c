#include "rvc.h"
#include "onnx.h"
#include "mel.h"
#include "f0.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { float *data; int64_t n; int sr; } red_wav;

static void set_error(char *dst, size_t cap, const char *message) {
    if (dst && cap) snprintf(dst, cap, "%s", message ? message : "Unknown native RVC error.");
}

static int read_wav(const char *path, red_wav *wav) {
    memset(wav, 0, sizeof(*wav));
    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    char riff[4], wave[4];
    uint32_t riff_size;
    if (fread(riff, 1, 4, f) != 4 || fread(&riff_size, 4, 1, f) != 1 ||
        fread(wave, 1, 4, f) != 4 || memcmp(riff, "RIFF", 4) || memcmp(wave, "WAVE", 4)) {
        fclose(f); return -1;
    }
    uint16_t format = 0, channels = 0, bits = 0;
    uint32_t sample_rate = 0;
    uint8_t *raw = NULL;
    uint32_t data_size = 0;
    while (!feof(f)) {
        char id[4]; uint32_t size;
        if (fread(id, 1, 4, f) != 4 || fread(&size, 4, 1, f) != 1) break;
        if (!memcmp(id, "fmt ", 4)) {
            uint8_t fmt[16];
            if (size < 16 || fread(fmt, 1, 16, f) != 16) { fclose(f); return -1; }
            format = (uint16_t)(fmt[0] | (fmt[1] << 8));
            channels = (uint16_t)(fmt[2] | (fmt[3] << 8));
            sample_rate = (uint32_t)fmt[4] | ((uint32_t)fmt[5] << 8) |
                          ((uint32_t)fmt[6] << 16) | ((uint32_t)fmt[7] << 24);
            bits = (uint16_t)(fmt[14] | (fmt[15] << 8));
            if (size > 16) fseek(f, (long)(size - 16), SEEK_CUR);
        } else if (!memcmp(id, "data", 4)) {
            if (size == 0 || size > (512u * 1024u * 1024u)) { fclose(f); return -1; }
            raw = (uint8_t *)malloc(size);
            if (!raw || fread(raw, 1, size, f) != size) { free(raw); fclose(f); return -1; }
            data_size = size;
            break;
        } else {
            fseek(f, (long)size, SEEK_CUR);
        }
    }
    fclose(f);
    if (!raw || !channels || !sample_rate || (format != 1 && format != 3) ||
        (bits != 16 && bits != 32) || (format == 3 && bits != 32)) {
        free(raw); return -1;
    }
    const size_t bytes_per_sample = bits / 8;
    const size_t frame_bytes = (size_t)channels * bytes_per_sample;
    if (!frame_bytes || data_size % frame_bytes) { free(raw); return -1; }
    const int64_t frames = data_size / frame_bytes;
    if (frames <= 0 || frames > (int64_t)sample_rate * 600) { free(raw); return -1; }
    wav->data = (float *)malloc((size_t)frames * sizeof(float));
    if (!wav->data) { free(raw); return -1; }
    wav->n = frames;
    wav->sr = (int)sample_rate;
    for (int64_t i = 0; i < frames; ++i) {
        if (bits == 16) {
            int16_t sample;
            memcpy(&sample, raw + (size_t)i * frame_bytes, sizeof(sample));
            wav->data[i] = (float)sample / 32768.0f;
        } else if (format == 3) {
            float sample;
            memcpy(&sample, raw + (size_t)i * frame_bytes, sizeof(sample));
            wav->data[i] = isfinite(sample) ? fmaxf(-1.0f, fminf(1.0f, sample)) : 0.0f;
        } else {
            free(raw); free(wav->data); memset(wav, 0, sizeof(*wav)); return -1;
        }
    }
    free(raw);
    return 0;
}

static int write_wav(const char *path, const float *data, int64_t n, int sr) {
    if (!path || !data || n <= 0 || n > (INT32_MAX - 36) / 2) return -1;
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    uint32_t data_size = (uint32_t)(n * 2);
    uint32_t riff_size = 36 + data_size;
    uint32_t fmt_size = 16, byte_rate = (uint32_t)sr * 2;
    uint16_t pcm = 1, channels = 1, align = 2, bits = 16;
    int ok = fwrite("RIFF",1,4,f)==4 && fwrite(&riff_size,4,1,f)==1 &&
        fwrite("WAVEfmt ",1,8,f)==8 && fwrite(&fmt_size,4,1,f)==1 &&
        fwrite(&pcm,2,1,f)==1 && fwrite(&channels,2,1,f)==1 &&
        fwrite(&sr,4,1,f)==1 && fwrite(&byte_rate,4,1,f)==1 &&
        fwrite(&align,2,1,f)==1 && fwrite(&bits,2,1,f)==1 &&
        fwrite("data",1,4,f)==4 && fwrite(&data_size,4,1,f)==1;
    for (int64_t i=0; ok && i<n; ++i) {
        float x = isfinite(data[i]) ? fmaxf(-1.0f, fminf(1.0f, data[i])) : 0.0f;
        int16_t sample = (int16_t)lrintf(x * 32767.0f);
        ok = fwrite(&sample, 2, 1, f) == 1;
    }
    if (fclose(f) != 0) ok = 0;
    return ok ? 0 : -1;
}

static float *resample_1d(const float *in, int64_t n_in, int64_t n_out) {
    if (!in || n_in <= 0 || n_out <= 0) return NULL;
    if (n_in == n_out) {
        float *copy = (float *)malloc((size_t)n_in * sizeof(float));
        if (copy) memcpy(copy, in, (size_t)n_in * sizeof(float));
        return copy;
    }
    float *out = (float *)malloc((size_t)n_out * sizeof(float));
    if (!out) return NULL;
    const double ratio = (double)n_in / (double)n_out;
    for (int64_t i=0; i<n_out; ++i) {
        double pos = (double)i * ratio;
        int64_t a = (int64_t)pos, b = a + 1;
        double frac = pos - (double)a;
        if (a >= n_in) a = n_in - 1;
        if (b >= n_in) b = n_in - 1;
        out[i] = (float)(in[a] * (1.0-frac) + in[b] * frac);
    }
    return out;
}

static float *resample_embed(const float *in, int64_t t_in, int64_t t_out, int dim) {
    if (!in || t_in <= 0 || t_out <= 0 || dim <= 0) return NULL;
    if ((uint64_t)t_out * (uint64_t)dim > SIZE_MAX / sizeof(float)) return NULL;
    float *out = (float *)malloc((size_t)t_out * (size_t)dim * sizeof(float));
    if (!out) return NULL;
    const double ratio = (double)t_in / (double)t_out;
    for (int64_t t=0; t<t_out; ++t) {
        double pos = (double)t * ratio;
        int64_t a = (int64_t)pos, b = a + 1;
        double frac = pos - (double)a;
        if (a >= t_in) a = t_in - 1;
        if (b >= t_in) b = t_in - 1;
        for (int d=0; d<dim; ++d)
            out[t*dim+d] = (float)(in[a*dim+d]*(1.0-frac) + in[b*dim+d]*frac);
    }
    return out;
}

int red_rvc_pth_convert(const char *input_wav, const char *pth_path,
                        const char *hubert_path, const char *rmvpe_path,
                        const char *output_wav, int pitch_shift,
                        char *error, size_t error_cap) {
    int result = -1, ort_ready = 0, model_ready = 0;
    rvc_model_t *model = NULL;
    spcv_onnx_session *hubert = NULL, *rmvpe = NULL;
    red_wav wav = {0};
    float *audio16 = NULL, *mel = NULL, *f0 = NULL, *f0_model = NULL;
    float *emb_model = NULL, *output = NULL;
    int64_t *pitch = NULL;
    spcv_onnx_output hubert_out = {0};

    if (!input_wav || !pth_path || !hubert_path || !rmvpe_path || !output_wav) {
        set_error(error,error_cap,"Missing input, PTH, HuBERT, RMVPE or output path."); goto cleanup;
    }
    if (spcv_onnx_init() != SPCV_ONNX_OK) {
        set_error(error,error_cap,"ONNX Runtime could not initialise."); goto cleanup;
    }
    ort_ready = 1;

    model = (rvc_model_t *)calloc(1, sizeof(rvc_model_t));
    if (!model) { set_error(error,error_cap,"Not enough memory to load the voice model."); goto cleanup; }
    if (rvc_load(model, pth_path) != 0) {
        set_error(error,error_cap,"This PTH checkpoint could not be read as a supported RVC v2 model."); goto cleanup;
    }
    model_ready = 1;
    if (model->cfg.ques != 768) {
        set_error(error,error_cap,"This build currently supports 768-dimensional RVC v2 PTH models. This checkpoint uses a different HuBERT dimension."); goto cleanup;
    }
    if (model->cfg.sr <= 0 || model->fps <= 0 || model->cfg.sr % model->fps != 0) {
        set_error(error,error_cap,"The PTH model contains unsupported sample-rate or frame-rate settings."); goto cleanup;
    }

    if (spcv_onnx_load(hubert_path, &hubert) != SPCV_ONNX_OK) {
        set_error(error,error_cap,"The bundled HuBERT model could not be loaded."); goto cleanup;
    }
    if (spcv_onnx_load(rmvpe_path, &rmvpe) != SPCV_ONNX_OK) {
        set_error(error,error_cap,"The bundled RMVPE model could not be loaded."); goto cleanup;
    }
    if (read_wav(input_wav, &wav) != 0) {
        set_error(error,error_cap,"Input audio must be a valid PCM WAV file."); goto cleanup;
    }
    const int64_t n16 = (int64_t)((double)wav.n * 16000.0 / (double)wav.sr);
    if (n16 <= 0 || n16 > 16000LL * 600LL) {
        set_error(error,error_cap,"Audio exceeds the 10-minute on-device processing limit."); goto cleanup;
    }
    audio16 = resample_1d(wav.data, wav.n, n16);
    if (!audio16) { set_error(error,error_cap,"Not enough memory to resample the audio."); goto cleanup; }

    spcv_onnx_input hubert_in = {
        .name = hubert->inputs[0].name, .data = audio16,
        .ndim = 3, .dims = {1,1,n16}, .elem_type = 1
    };
    hubert_out.name = hubert->outputs[0].name;
    if (spcv_onnx_run(hubert, &hubert_in, 1, &hubert_out, 1) != SPCV_ONNX_OK) {
        set_error(error,error_cap,"HuBERT feature extraction failed."); goto cleanup;
    }
    int hubert_ndim = 0; int64_t hubert_dims[8] = {0};
    spcv_onnx_output_shape(&hubert_out, &hubert_ndim, hubert_dims);
    const float *embedding = (const float *)spcv_onnx_output_data(&hubert_out);
    if (!embedding || hubert_ndim < 3 || hubert_dims[1] <= 0 || hubert_dims[2] != model->cfg.ques) {
        set_error(error,error_cap,"HuBERT output does not match this voice model's feature dimension."); goto cleanup;
    }
    const int64_t frames = (int64_t)((double)n16 * model->fps / 16000.0);
    if (frames <= 0 || frames > 60000) {
        set_error(error,error_cap,"Audio is too long for safe on-device RVC processing."); goto cleanup;
    }
    emb_model = resample_embed(embedding, hubert_dims[1], frames, model->cfg.ques);
    spcv_onnx_free_output(&hubert_out);
    if (!emb_model) { set_error(error,error_cap,"Not enough memory to prepare HuBERT features."); goto cleanup; }

    const int mel_frames = (int)spcv_mel_n_frames(n16);
    if (mel_frames <= 0 || (uint64_t)mel_frames * 128u > SIZE_MAX / sizeof(float)) {
        set_error(error,error_cap,"Could not allocate the pitch-analysis buffer."); goto cleanup;
    }
    mel = (float *)malloc((size_t)mel_frames * 128u * sizeof(float));
    f0 = (float *)malloc((size_t)mel_frames * sizeof(float));
    if (!mel || !f0) {
        set_error(error,error_cap,"Could not prepare the pitch-analysis model."); goto cleanup;
    }
    if (spcv_mel_compute(audio16, n16, mel, 128) < 0) {
        set_error(error,error_cap,"Mel spectrogram calculation failed."); goto cleanup;
    }
    free(audio16); audio16 = NULL;
    free(wav.data); wav.data = NULL;
    if (spcv_f0_extract(mel, mel_frames, rmvpe, f0) != 0) {
        set_error(error,error_cap,"RMVPE pitch extraction failed."); goto cleanup;
    }
    spcv_f0_shift(f0, mel_frames, pitch_shift);
    f0_model = resample_1d(f0, mel_frames, frames);
    pitch = (int64_t *)malloc((size_t)frames * sizeof(int64_t));
    if (!f0_model || !pitch) {
        set_error(error,error_cap,"Not enough memory to prepare pitch data."); goto cleanup;
    }
    spcv_f0_quantize(f0_model, (int)frames, pitch);

    const int64_t samples_per_frame = model->cfg.sr / model->fps;
    if ((uint64_t)frames * (uint64_t)samples_per_frame > SIZE_MAX / sizeof(float)) {
        set_error(error,error_cap,"The converted audio would exceed available memory."); goto cleanup;
    }
    const size_t max_samples = (size_t)frames * (size_t)samples_per_frame;
    output = (float *)malloc(max_samples * sizeof(float));
    if (!output) { set_error(error,error_cap,"Not enough memory for converted audio."); goto cleanup; }
    int output_length = 0;
    uint32_t seed = 0x524544u;
    if (rvc_infer(model, emb_model, (int)frames, pitch, f0_model,
                  NULL, output, &output_length, &seed) != 0 || output_length <= 0 ||
        (size_t)output_length > max_samples) {
        set_error(error,error_cap,"The native RVC voice-conversion engine failed."); goto cleanup;
    }
    if (write_wav(output_wav, output, output_length, model->cfg.sr) != 0) {
        set_error(error,error_cap,"Could not write the converted WAV file."); goto cleanup;
    }
    result = 0;

cleanup:
    if (hubert_out.ort_value) spcv_onnx_free_output(&hubert_out);
    free(wav.data); free(audio16); free(mel); free(f0); free(f0_model);
    free(emb_model); free(pitch); free(output);
    if (hubert) spcv_onnx_free(hubert);
    if (rmvpe) spcv_onnx_free(rmvpe);
    if (model_ready) rvc_free(model);
    free(model);
    if (ort_ready) spcv_onnx_shutdown();
    return result;
}
