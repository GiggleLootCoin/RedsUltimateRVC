#include "pth_pipeline.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static int write_test_wav(const char *path) {
    const int sample_rate = 16000;
    const int seconds = 2;
    const int samples = sample_rate * seconds;
    FILE *file = fopen(path, "wb");
    if (!file) return -1;

    const uint32_t data_bytes = (uint32_t)samples * 2u * 2u;
    const uint32_t riff_bytes = 36u + data_bytes;
    const uint16_t format = 1, channels = 2, bits = 16, block_align = 4;
    const uint32_t byte_rate = sample_rate * block_align;
    fwrite("RIFF", 1, 4, file);
    fwrite(&riff_bytes, 4, 1, file);
    fwrite("WAVEfmt ", 1, 8, file);
    const uint32_t fmt_size = 16;
    fwrite(&fmt_size, 4, 1, file);
    fwrite(&format, 2, 1, file);
    fwrite(&channels, 2, 1, file);
    fwrite(&sample_rate, 4, 1, file);
    fwrite(&byte_rate, 4, 1, file);
    fwrite(&block_align, 2, 1, file);
    fwrite(&bits, 2, 1, file);
    fwrite("data", 1, 4, file);
    fwrite(&data_bytes, 4, 1, file);

    for (int i = 0; i < samples; ++i) {
        const double t = (double)i / sample_rate;
        const double envelope = 0.35 + 0.25 * sin(2.0 * M_PI * 2.0 * t);
        const double left_tone = sin(2.0 * M_PI * 220.0 * t) * envelope;
        const double right_tone = sin(2.0 * M_PI * 330.0 * t) * envelope;
        const int16_t left_pcm = (int16_t)lrint(left_tone * 16000.0);
        const int16_t right_pcm = (int16_t)lrint(right_tone * 16000.0);
        if (fwrite(&left_pcm, sizeof(left_pcm), 1, file) != 1 ||
            fwrite(&right_pcm, sizeof(right_pcm), 1, file) != 1) {
            fclose(file);
            return -1;
        }
    }
    return fclose(file) == 0 ? 0 : -1;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s model.pth hubert.onnx rmvpe.onnx output-directory\n", argv[0]);
        return 2;
    }

    char input[4096], output[4096];
    if (snprintf(input, sizeof(input), "%s/probe-input.wav", argv[4]) >= (int)sizeof(input) ||
        snprintf(output, sizeof(output), "%s/probe-output.wav", argv[4]) >= (int)sizeof(output)) {
        fprintf(stderr, "Probe output path is too long.\n");
        return 2;
    }
    if (write_test_wav(input) != 0) {
        fprintf(stderr, "Could not create the synthetic PCM WAV input.\n");
        return 1;
    }

    char error[512] = {0};
    const int result = red_rvc_pth_convert(
        input, argv[1], argv[2], argv[3], output, 0, 0.0f, NULL, NULL, error, sizeof(error));
    if (result != 0) {
        fprintf(stderr, "End-to-end native PTH conversion failed: %s\n", error);
        return 1;
    }

    struct stat info;
    if (stat(output, &info) != 0 || info.st_size <= 44) {
        fprintf(stderr, "Native PTH conversion did not produce a non-empty WAV.\n");
        return 1;
    }
    FILE *file = fopen(output, "rb");
    if (!file) return 1;
    char header[12] = {0};
    const size_t read = fread(header, 1, sizeof(header), file);
    fclose(file);
    if (read != sizeof(header) || memcmp(header, "RIFF", 4) != 0 ||
        memcmp(header + 8, "WAVE", 4) != 0) {
        fprintf(stderr, "Native PTH output is not a valid RIFF/WAVE file.\n");
        return 1;
    }

    printf("PASS: real RVC v2 PTH + ContentVec + RMVPE produced a %lld-byte WAV.\n",
           (long long)info.st_size);
    remove(input);
    remove(output);
    return 0;
}
