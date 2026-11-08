#include <jni.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <string>
#include <vector>

#include "sherpa-onnx/c-api/c-api.h"

namespace {
void ThrowJava(JNIEnv *env, const std::string &message) {
  jclass cls = env->FindClass("java/lang/IllegalStateException");
  if (cls) env->ThrowNew(cls, message.c_str());
}

std::string FromJava(JNIEnv *env, jstring value) {
  if (!value) return {};
  const char *chars = env->GetStringUTFChars(value, nullptr);
  if (!chars) return {};
  std::string result(chars);
  env->ReleaseStringUTFChars(value, chars);
  return result;
}
}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_SourceSeparationBridge_separateWav(
    JNIEnv *env, jclass,
    jstring input_path, jstring vocals_path, jstring accompaniment_path,
    jstring vocals_model_path, jstring accompaniment_model_path,
    jint num_threads) {
  const std::string input = FromJava(env, input_path);
  const std::string vocals = FromJava(env, vocals_path);
  const std::string accompaniment = FromJava(env, accompaniment_path);
  const std::string vocals_model = FromJava(env, vocals_model_path);
  const std::string accompaniment_model = FromJava(env, accompaniment_model_path);
  if (input.empty() || vocals.empty() || accompaniment.empty() ||
      vocals_model.empty() || accompaniment_model.empty()) {
    ThrowJava(env, "Missing source-separation file path.");
    return nullptr;
  }

  SherpaOnnxOfflineSourceSeparationConfig config;
  std::memset(&config, 0, sizeof(config));
  config.model.spleeter.vocals = vocals_model.c_str();
  config.model.spleeter.accompaniment = accompaniment_model.c_str();
  config.model.num_threads = std::max(1, std::min(2, static_cast<int>(num_threads)));
  config.model.provider = "cpu";

  const auto *engine = SherpaOnnxCreateOfflineSourceSeparation(&config);
  if (!engine) {
    ThrowJava(env, "Could not load the offline vocal-separation models.");
    return nullptr;
  }

  const auto *wave = SherpaOnnxReadWaveMultiChannel(input.c_str());
  if (!wave || !wave->samples || wave->num_channels < 1 ||
      wave->num_channels > 2 || wave->num_samples <= 0 ||
      wave->sample_rate <= 0) {
    if (wave) SherpaOnnxFreeMultiChannelWave(wave);
    SherpaOnnxDestroyOfflineSourceSeparation(engine);
    ThrowJava(env, "Could not read a valid mono or stereo 16-bit PCM WAV.");
    return nullptr;
  }

  const auto *output = SherpaOnnxOfflineSourceSeparationProcess(
      engine, wave->samples, wave->num_channels, wave->num_samples,
      wave->sample_rate);
  if (!output || !output->stems || output->num_stems < 2 ||
      output->sample_rate <= 0) {
    if (output) SherpaOnnxDestroySourceSeparationOutput(output);
    SherpaOnnxFreeMultiChannelWave(wave);
    SherpaOnnxDestroyOfflineSourceSeparation(engine);
    ThrowJava(env, "Vocal separation did not produce both required stems.");
    return nullptr;
  }

  const auto &vocal_stem = output->stems[0];
  const auto &music_stem = output->stems[1];
  if (!vocal_stem.samples || !music_stem.samples ||
      vocal_stem.n <= 0 || music_stem.n <= 0 ||
      vocal_stem.num_channels < 1 || vocal_stem.num_channels > 2 ||
      music_stem.num_channels < 1 || music_stem.num_channels > 2) {
    SherpaOnnxDestroySourceSeparationOutput(output);
    SherpaOnnxFreeMultiChannelWave(wave);
    SherpaOnnxDestroyOfflineSourceSeparation(engine);
    ThrowJava(env, "Vocal separation returned invalid audio stems.");
    return nullptr;
  }

  std::vector<const float *> vocal_channels(vocal_stem.num_channels);
  std::vector<const float *> music_channels(music_stem.num_channels);
  for (int channel = 0; channel < vocal_stem.num_channels; ++channel) {
    vocal_channels[channel] = vocal_stem.samples[channel];
  }
  for (int channel = 0; channel < music_stem.num_channels; ++channel) {
    music_channels[channel] = music_stem.samples[channel];
  }
  const int vocal_ok = SherpaOnnxWriteWaveMultiChannel(
      vocal_channels.data(), vocal_stem.n, output->sample_rate,
      vocal_stem.num_channels, vocals.c_str());
  const int music_ok = SherpaOnnxWriteWaveMultiChannel(
      music_channels.data(), music_stem.n, output->sample_rate,
      music_stem.num_channels, accompaniment.c_str());

  SherpaOnnxDestroySourceSeparationOutput(output);
  SherpaOnnxFreeMultiChannelWave(wave);
  SherpaOnnxDestroyOfflineSourceSeparation(engine);

  if (!vocal_ok || !music_ok) {
    ThrowJava(env, "Could not save the separated WAV stems.");
    return nullptr;
  }
  return env->NewStringUTF("ok");
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_SourceSeparationBridge_mixWav(
    JNIEnv *env, jclass, jstring vocals_path, jstring accompaniment_path,
    jstring output_path, jfloat vocal_gain, jfloat accompaniment_gain) {
  const std::string vocals_file = FromJava(env, vocals_path);
  const std::string accompaniment_file = FromJava(env, accompaniment_path);
  const std::string output_file = FromJava(env, output_path);
  if (vocals_file.empty() || accompaniment_file.empty() || output_file.empty()) {
    ThrowJava(env, "Missing song-cover mix file path.");
    return nullptr;
  }

  const auto *vocals = SherpaOnnxReadWaveMultiChannel(vocals_file.c_str());
  const auto *music = SherpaOnnxReadWaveMultiChannel(accompaniment_file.c_str());
  if (!vocals || !music) {
    if (vocals) SherpaOnnxFreeMultiChannelWave(vocals);
    if (music) SherpaOnnxFreeMultiChannelWave(music);
    ThrowJava(env, "Could not read the converted vocals or accompaniment WAV.");
    return nullptr;
  }
  if (vocals->num_channels < 1 || vocals->num_channels > 2 ||
      music->num_channels < 1 || music->num_channels > 2 ||
      vocals->sample_rate <= 0 || music->sample_rate <= 0 ||
      vocals->num_samples <= 0 || music->num_samples <= 0) {
    SherpaOnnxFreeMultiChannelWave(vocals);
    SherpaOnnxFreeMultiChannelWave(music);
    ThrowJava(env, "Only non-empty mono or stereo WAV stems with valid sample rates are supported.");
    return nullptr;
  }

  // RVC models and Spleeter may produce different sample rates and channel
  // counts. Resample vocals to the accompaniment rate and preserve stereo.
  const int output_rate = music->sample_rate;
  const int output_channels = std::max(vocals->num_channels, music->num_channels);
  const int vocal_frames = static_cast<int>(std::ceil(
      static_cast<double>(vocals->num_samples) * output_rate / vocals->sample_rate));
  const int music_frames = music->num_samples;
  const int frames = std::max(vocal_frames, music_frames);
  std::vector<std::vector<float>> mixed(
      output_channels, std::vector<float>(frames, 0.0f));
  std::vector<const float *> channels(output_channels);

  auto resampled = [output_rate](const SherpaOnnxMultiChannelWave *wave,
                                 int channel, int frame) -> float {
    const int source_channel = wave->num_channels == 1 ? 0 : channel;
    const double position =
        static_cast<double>(frame) * wave->sample_rate / output_rate;
    if (position >= wave->num_samples) return 0.0f;
    const int left = static_cast<int>(position);
    const int right = std::min(left + 1, wave->num_samples - 1);
    const float fraction = static_cast<float>(position - left);
    const float a = wave->samples[source_channel][left];
    const float b = wave->samples[source_channel][right];
    return a + (b - a) * fraction;
  };

  for (int channel = 0; channel < output_channels; ++channel) {
    for (int frame = 0; frame < frames; ++frame) {
      const float v = frame < vocal_frames
          ? resampled(vocals, channel, frame) * vocal_gain : 0.0f;
      const float m = frame < music_frames
          ? resampled(music, channel, frame) * accompaniment_gain : 0.0f;
      mixed[channel][frame] = std::max(-1.0f, std::min(1.0f, v + m));
    }
    channels[channel] = mixed[channel].data();
  }

  const int written = SherpaOnnxWriteWaveMultiChannel(
      channels.data(), frames, output_rate, output_channels, output_file.c_str());
  SherpaOnnxFreeMultiChannelWave(vocals);
  SherpaOnnxFreeMultiChannelWave(music);
  if (!written) {
    ThrowJava(env, "Could not write the final song-cover WAV.");
    return nullptr;
  }
  return env->NewStringUTF(output_file.c_str());
}
