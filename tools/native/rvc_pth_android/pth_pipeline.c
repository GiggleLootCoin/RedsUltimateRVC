#include "rvc.h"
#include "onnx.h"
#include "mel.h"
#include "f0.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

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

#define RED_HUBERT_DIM 768
#define RED_RMVPE_MEL_BINS 128
#define RED_RMVPE_FFT_SIZE 1024
#define RED_RMVPE_HOP_SIZE 160
#define RED_RMVPE_SPECTRUM_BINS 513
#define RED_RMVPE_ALIGNMENT 32
#define RED_RMVPE_CENTS_BASE 1997.3794084376191
#define RED_RMVPE_CENTS_PER_BIN 20.0
#define RED_RMVPE_VOICED_THRESHOLD 0.03f
#define RED_RMVPE_LOG_EPSILON 1e-6

static int hubert_frame_count(int length) {
    static const int kernels[7] = {10,3,3,3,3,2,2};
    static const int strides[7] = {5,2,2,2,2,2,2};
    int frames = length;
    for (int i=0; i<7; ++i) frames = (frames - kernels[i]) / strides[i] + 1;
    return frames;
}

static int align_hubert_length(int length) {
    int candidate = length > 801 ? length : 801;
    for (int attempts=0; attempts<100000; ++attempts,++candidate) {
        int frames = hubert_frame_count(candidate);
        if (frames > 0 && (frames % 2) == 0 && (candidate % frames) != 0) return candidate;
    }
    return 0;
}

static float *extract_hubert_phone(spcv_onnx_session *session,
                                   const float *audio, int64_t audio_frames,
                                   int target_frames, int *error_code) {
    int source_index = -1, mask_index = -1;
    for (int i=0; i<session->n_inputs; ++i) {
        if (!strcmp(session->inputs[i].name, "source")) source_index = i;
        if (!strcmp(session->inputs[i].name, "padding_mask")) mask_index = i;
    }
    if (source_index < 0 || mask_index < 0 || session->n_inputs < 2) {
        *error_code = 1; return NULL;
    }
    int padded = align_hubert_length((int)audio_frames);
    if (padded <= 0 || (uint64_t)padded > SIZE_MAX / sizeof(float)) {
        *error_code = 2; return NULL;
    }
    float *padded_audio = (float *)calloc((size_t)padded, sizeof(float));
    uint8_t *mask = (uint8_t *)calloc((size_t)padded, sizeof(uint8_t));
    if (!padded_audio || !mask) {
        free(padded_audio); free(mask); *error_code = 3; return NULL;
    }
    memcpy(padded_audio, audio, (size_t)audio_frames * sizeof(float));
    for (int i=(int)audio_frames; i<padded; ++i) mask[i] = 1;

    spcv_onnx_input inputs[2] = {
        {.name=session->inputs[source_index].name,.data=padded_audio,.ndim=2,.dims={1,padded},.elem_type=1},
        {.name=session->inputs[mask_index].name,.data=mask,.ndim=2,.dims={1,padded},.elem_type=9}
    };
    spcv_onnx_output output = {.name=session->outputs[0].name,.buf=NULL,.buf_size=0,.ort_value=NULL};
    int rc = spcv_onnx_run(session, inputs, 2, &output, 1);
    free(padded_audio); free(mask);
    if (rc != SPCV_ONNX_OK) { *error_code = 4; return NULL; }

    int ndim = 0; int64_t dims[8] = {0};
    spcv_onnx_output_shape(&output, &ndim, dims);
    const float *features = (const float *)spcv_onnx_output_data(&output);
    int64_t source_frames = 0;
    if (ndim >= 3 && dims[0] == 1 && dims[2] == RED_HUBERT_DIM) source_frames = dims[1];
    else if (ndim == 2 && dims[1] == RED_HUBERT_DIM) source_frames = dims[0];
    if (!features || source_frames <= 0 ||
        (uint64_t)target_frames * RED_HUBERT_DIM > SIZE_MAX / sizeof(float)) {
        spcv_onnx_free_output(&output); *error_code = 5; return NULL;
    }
    float *phone = (float *)malloc((size_t)target_frames * RED_HUBERT_DIM * sizeof(float));
    if (!phone) { spcv_onnx_free_output(&output); *error_code = 3; return NULL; }
    for (int t=0; t<target_frames; ++t) {
        int64_t source_frame = t / 2; /* ContentVec emits 50 Hz; RVC consumes 100 Hz. */
        if (source_frame >= source_frames) source_frame = source_frames - 1;
        memcpy(phone + (size_t)t * RED_HUBERT_DIM,
               features + (size_t)source_frame * RED_HUBERT_DIM,
               RED_HUBERT_DIM * sizeof(float));
    }
    spcv_onnx_free_output(&output);
    *error_code = 0;
    return phone;
}

static void fft_1024(double *real, double *imag) {
    const int n = RED_RMVPE_FFT_SIZE;
    for (int i=1,j=0; i<n; ++i) {
        int bit=n>>1;
        for (; j & bit; bit>>=1) j ^= bit;
        j ^= bit;
        if (i<j) {
            double tr=real[i]; real[i]=real[j]; real[j]=tr;
            double ti=imag[i]; imag[i]=imag[j]; imag[j]=ti;
        }
    }
    for (int len=2; len<=n; len<<=1) {
        double angle=-2.0*M_PI/len;
        double wlen_r=cos(angle), wlen_i=sin(angle);
        for (int i=0; i<n; i+=len) {
            double wr=1.0, wi=0.0;
            for (int j=0; j<len/2; ++j) {
                int a=i+j, b=i+j+len/2;
                double vr=real[b]*wr-imag[b]*wi;
                double vi=real[b]*wi+imag[b]*wr;
                double ur=real[a], ui=imag[a];
                real[a]=ur+vr; imag[a]=ui+vi;
                real[b]=ur-vr; imag[b]=ui-vi;
                double next_wr=wr*wlen_r-wi*wlen_i;
                wi=wr*wlen_i+wi*wlen_r; wr=next_wr;
            }
        }
    }
}

static double hz_to_mel(double hz) { return 2595.0 * log10(1.0 + hz/700.0); }
static double mel_to_hz(double mel) { return 700.0 * (pow(10.0,mel/2595.0)-1.0); }

static void build_rmvpe_filterbank(double *weights) {
    const double mel_min=hz_to_mel(30.0), mel_max=hz_to_mel(8000.0);
    int bins[RED_RMVPE_MEL_BINS+2];
    for (int i=0; i<RED_RMVPE_MEL_BINS+2; ++i) {
        double mel=mel_min+(mel_max-mel_min)*i/(RED_RMVPE_MEL_BINS+1);
        double hz=mel_to_hz(mel);
        bins[i]=(int)llround((RED_RMVPE_FFT_SIZE+1)*hz/16000.0);
        if (bins[i]<0) bins[i]=0;
        if (bins[i]>=RED_RMVPE_SPECTRUM_BINS) bins[i]=RED_RMVPE_SPECTRUM_BINS-1;
    }
    memset(weights,0,(size_t)RED_RMVPE_MEL_BINS*RED_RMVPE_SPECTRUM_BINS*sizeof(double));
    for (int m=0; m<RED_RMVPE_MEL_BINS; ++m) {
        int left=bins[m];
        int center=left+1>bins[m+1]?left+1:bins[m+1];
        int right=center+1>bins[m+2]?center+1:bins[m+2];
        size_t off=(size_t)m*RED_RMVPE_SPECTRUM_BINS;
        for (int k=left; k<center && k<RED_RMVPE_SPECTRUM_BINS; ++k)
            weights[off+k]=(double)(k-left)/(center-left);
        int limit=right<RED_RMVPE_SPECTRUM_BINS?right:RED_RMVPE_SPECTRUM_BINS;
        for (int k=center; k<limit; ++k)
            weights[off+k]=(double)(right-k)/(right-center);
    }
}

static int build_rmvpe_mel(const float *audio, int64_t samples,
                           int frame_count, float **mel_out) {
    if (!audio || samples<=0 || frame_count<=0) return -1;
    if ((uint64_t)frame_count*RED_RMVPE_MEL_BINS > SIZE_MAX/sizeof(float)) return -1;
    float *mel=(float *)malloc((size_t)frame_count*RED_RMVPE_MEL_BINS*sizeof(float));
    double *weights=(double *)malloc((size_t)RED_RMVPE_MEL_BINS*RED_RMVPE_SPECTRUM_BINS*sizeof(double));
    if (!mel || !weights) { free(mel); free(weights); return -1; }
    build_rmvpe_filterbank(weights);
    double window[RED_RMVPE_FFT_SIZE], real[RED_RMVPE_FFT_SIZE], imag[RED_RMVPE_FFT_SIZE];
    for (int i=0; i<RED_RMVPE_FFT_SIZE; ++i)
        window[i]=0.5-0.5*cos(2.0*M_PI*i/RED_RMVPE_FFT_SIZE);
    double power[RED_RMVPE_SPECTRUM_BINS];
    for (int frame=0; frame<frame_count; ++frame) {
        int64_t center=(int64_t)frame*RED_RMVPE_HOP_SIZE;
        int64_t start=center-RED_RMVPE_FFT_SIZE/2;
        for (int i=0; i<RED_RMVPE_FFT_SIZE; ++i) {
            int64_t index=start+i;
            real[i]=(index>=0 && index<samples ? audio[index] : 0.0)*window[i];
            imag[i]=0.0;
        }
        fft_1024(real,imag);
        for (int k=0; k<RED_RMVPE_SPECTRUM_BINS; ++k)
            power[k]=real[k]*real[k]+imag[k]*imag[k];
        for (int m=0; m<RED_RMVPE_MEL_BINS; ++m) {
            double energy=0.0;
            size_t off=(size_t)m*RED_RMVPE_SPECTRUM_BINS;
            for (int k=0; k<RED_RMVPE_SPECTRUM_BINS; ++k)
                energy+=power[k]*weights[off+k];
            mel[(size_t)m*frame_count+frame]=(float)log10(energy>RED_RMVPE_LOG_EPSILON?energy:RED_RMVPE_LOG_EPSILON);
        }
    }
    free(weights);
    *mel_out=mel;
    return 0;
}

static int extract_rmvpe_pitch(spcv_onnx_session *session,
                               const float *audio, int64_t samples,
                               int target_frames, int pitch_shift,
                               float **pitchf_out, int64_t **pitch_out) {
    int frame_count=((target_frames>32?target_frames:32)+RED_RMVPE_ALIGNMENT-1)/RED_RMVPE_ALIGNMENT*RED_RMVPE_ALIGNMENT;
    float *mel=NULL;
    if (build_rmvpe_mel(audio,samples,frame_count,&mel)!=0) return -1;
    const char *input_name=session->n_inputs>0?session->inputs[0].name:"input";
    spcv_onnx_input input={.name=input_name,.data=mel,.ndim=3,.dims={1,RED_RMVPE_MEL_BINS,frame_count},.elem_type=1};
    spcv_onnx_output output={.name=session->outputs[0].name,.buf=NULL,.buf_size=0,.ort_value=NULL};
    int rc=spcv_onnx_run(session,&input,1,&output,1);
    free(mel);
    if (rc!=SPCV_ONNX_OK) return -1;
    int ndim=0; int64_t dims[8]={0};
    spcv_onnx_output_shape(&output,&ndim,dims);
    const float *salience=(const float *)spcv_onnx_output_data(&output);
    if (!salience || ndim<3 || dims[1]<target_frames || dims[2]!=360) {
        spcv_onnx_free_output(&output); return -1;
    }
    float *pitchf=(float *)calloc((size_t)target_frames,sizeof(float));
    int64_t *pitch=(int64_t *)malloc((size_t)target_frames*sizeof(int64_t));
    if (!pitchf || !pitch) {
        free(pitchf); free(pitch); spcv_onnx_free_output(&output); return -1;
    }
    const float semitone=(float)pow(2.0,pitch_shift/12.0);
    const double mel_min=1127.0*log(1.0+50.0/700.0);
    const double mel_max=1127.0*log(1.0+1100.0/700.0);
    for (int frame=0; frame<target_frames; ++frame) {
        const float *row=salience+(size_t)frame*360;
        int best=0; float confidence=row[0];
        for (int bin=1; bin<360; ++bin) if (row[bin]>confidence) {confidence=row[bin];best=bin;}
        if (confidence>=RED_RMVPE_VOICED_THRESHOLD) {
            double cents=RED_RMVPE_CENTS_BASE+RED_RMVPE_CENTS_PER_BIN*best;
            pitchf[frame]=(float)(10.0*pow(2.0,cents/1200.0))*semitone;
        }
        if (pitchf[frame]<=0.0f) pitch[frame]=1;
        else {
            double mel_value=1127.0*log(1.0+pitchf[frame]/700.0);
            long coarse=lround((mel_value-mel_min)*254.0/(mel_max-mel_min)+1.0);
            if (coarse<1) coarse=1; if (coarse>255) coarse=255;
            pitch[frame]=(int64_t)coarse;
        }
    }
    spcv_onnx_free_output(&output);
    *pitchf_out=pitchf; *pitch_out=pitch;
    return 0;
}

int red_rvc_pth_convert(const char *input_wav, const char *pth_path,
                        const char *hubert_path, const char *rmvpe_path,
                        const char *output_wav, int pitch_shift,
                        char *error, size_t error_cap) {
    int result = -1, ort_ready = 0, model_ready = 0;
    rvc_model_t *model = NULL;
    spcv_onnx_session *hubert = NULL, *rmvpe = NULL;
    red_wav wav = {0};
    float *audio16 = NULL, *phone = NULL, *pitchf = NULL, *output = NULL;
    int64_t *pitch = NULL;

    if (!input_wav || !pth_path || !hubert_path || !rmvpe_path || !output_wav) {
        set_error(error,error_cap,"Missing input, PTH, HuBERT, RMVPE or output path."); goto cleanup;
    }
    if (spcv_onnx_init() != SPCV_ONNX_OK) {
        set_error(error,error_cap,"ONNX Runtime could not initialise."); goto cleanup;
    }
    ort_ready = 1;
    spcv_onnx_set_ep(SPCV_EP_CPU);

    model = (rvc_model_t *)calloc(1, sizeof(rvc_model_t));
    if (!model) { set_error(error,error_cap,"Not enough memory to load the voice model."); goto cleanup; }
    if (rvc_load(model, pth_path) != 0) {
        set_error(error,error_cap,"This PTH checkpoint could not be read as a supported RVC v2 model."); goto cleanup;
    }
    model_ready = 1;
    if (model->cfg.ques != RED_HUBERT_DIM || model->fps != 100) {
        set_error(error,error_cap,"This build supports standard 100-fps, 768-dimensional RVC v2 PTH checkpoints only."); goto cleanup;
    }
    if (model->cfg.sr != 32000 && model->cfg.sr != 40000 && model->cfg.sr != 48000) {
        set_error(error,error_cap,"This PTH checkpoint uses an unsupported output sample rate."); goto cleanup;
    }

    if (spcv_onnx_load(hubert_path, &hubert) != SPCV_ONNX_OK) {
        set_error(error,error_cap,"The bundled 768-dimensional ContentVec model could not be loaded."); goto cleanup;
    }
    if (spcv_onnx_load(rmvpe_path, &rmvpe) != SPCV_ONNX_OK) {
        set_error(error,error_cap,"The bundled RMVPE pitch model could not be loaded."); goto cleanup;
    }
    if (read_wav(input_wav, &wav) != 0) {
        set_error(error,error_cap,"Input audio must be a valid 16-bit PCM WAV file."); goto cleanup;
    }
    const int64_t n16 = (int64_t)((double)wav.n * 16000.0 / (double)wav.sr);
    if (n16 <= 0 || n16 > 16000LL * 600LL) {
        set_error(error,error_cap,"Audio exceeds the 10-minute on-device processing limit."); goto cleanup;
    }
    audio16 = resample_1d(wav.data, wav.n, n16);
    if (!audio16) { set_error(error,error_cap,"Not enough memory to resample the audio."); goto cleanup; }

    const int frames = (int)((double)n16 * model->fps / 16000.0);
    if (frames <= 0 || frames > 60000) {
        set_error(error,error_cap,"Audio is too long for safe on-device RVC processing."); goto cleanup;
    }
    int hubert_error = 0;
    phone = extract_hubert_phone(hubert, audio16, n16, frames, &hubert_error);
    if (!phone) {
        const char *why = hubert_error == 1 ? "ContentVec model inputs are not the expected source/padding_mask pair."
            : hubert_error == 5 ? "ContentVec output is not a 768-dimensional feature tensor."
            : "ContentVec feature extraction failed.";
        set_error(error,error_cap,why); goto cleanup;
    }
    if (extract_rmvpe_pitch(rmvpe, audio16, n16, frames, pitch_shift, &pitchf, &pitch) != 0) {
        set_error(error,error_cap,"RMVPE pitch extraction failed."); goto cleanup;
    }
    free(audio16); audio16 = NULL;
    free(wav.data); wav.data = NULL;

    const int64_t samples_per_frame = model->cfg.sr / model->fps;
    if ((uint64_t)frames * (uint64_t)samples_per_frame > SIZE_MAX / sizeof(float)) {
        set_error(error,error_cap,"The converted audio would exceed available memory."); goto cleanup;
    }
    const size_t max_samples = (size_t)frames * (size_t)samples_per_frame;
    output = (float *)malloc(max_samples * sizeof(float));
    if (!output) { set_error(error,error_cap,"Not enough memory for converted audio."); goto cleanup; }
    int output_length = 0;
    uint32_t seed = 0x524544u;
    if (rvc_infer(model, phone, frames, pitch, pitchf,
                  NULL, output, &output_length, &seed) != 0 || output_length <= 0 ||
        (size_t)output_length > max_samples) {
        set_error(error,error_cap,"The native RVC voice-conversion engine failed."); goto cleanup;
    }
    if (write_wav(output_wav, output, output_length, model->cfg.sr) != 0) {
        set_error(error,error_cap,"Could not write the converted WAV file."); goto cleanup;
    }
    result = 0;

cleanup:
    free(wav.data); free(audio16); free(phone); free(pitchf); free(pitch); free(output);
    if (hubert) spcv_onnx_free(hubert);
    if (rmvpe) spcv_onnx_free(rmvpe);
    if (model_ready) rvc_free(model);
    free(model);
    if (ort_ready) spcv_onnx_shutdown();
    return result;
}
