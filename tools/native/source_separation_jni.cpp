#include <jni.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <memory>
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

uint16_t ReadU16(const unsigned char *p) {
  return static_cast<uint16_t>(p[0] | (static_cast<uint16_t>(p[1]) << 8));
}
uint32_t ReadU32(const unsigned char *p) {
  return static_cast<uint32_t>(p[0]) |
         (static_cast<uint32_t>(p[1]) << 8) |
         (static_cast<uint32_t>(p[2]) << 16) |
         (static_cast<uint32_t>(p[3]) << 24);
}
void PutU16(unsigned char *p, uint16_t v) {
  p[0] = static_cast<unsigned char>(v & 0xff);
  p[1] = static_cast<unsigned char>((v >> 8) & 0xff);
}
void PutU32(unsigned char *p, uint32_t v) {
  p[0] = static_cast<unsigned char>(v & 0xff);
  p[1] = static_cast<unsigned char>((v >> 8) & 0xff);
  p[2] = static_cast<unsigned char>((v >> 16) & 0xff);
  p[3] = static_cast<unsigned char>((v >> 24) & 0xff);
}

// The app's decoder writes ordinary PCM16 WAV. Read it in bounded blocks so
// source separation never duplicates a whole song in native memory.
class Pcm16WaveReader {
 public:
  explicit Pcm16WaveReader(const std::string &path) : file_(path, std::ios::binary) {
    if (!file_) throw std::runtime_error("Could not open WAV: " + path);
    unsigned char header[12];
    ReadExact(header, sizeof(header));
    if (std::memcmp(header, "RIFF", 4) || std::memcmp(header + 8, "WAVE", 4))
      throw std::runtime_error("Only RIFF/WAVE PCM audio is supported.");

    bool have_format = false;
    bool have_data = false;
    while (file_ && !(have_format && have_data)) {
      unsigned char chunk[8];
      file_.read(reinterpret_cast<char *>(chunk), sizeof(chunk));
      if (file_.gcount() != static_cast<std::streamsize>(sizeof(chunk))) break;
      const uint32_t size = ReadU32(chunk + 4);
      if (!std::memcmp(chunk, "fmt ", 4)) {
        if (size < 16) throw std::runtime_error("Invalid WAV format chunk.");
        unsigned char fmt[16];
        ReadExact(fmt, sizeof(fmt));
        format_ = ReadU16(fmt);
        channels_ = ReadU16(fmt + 2);
        sample_rate_ = ReadU32(fmt + 4);
        block_align_ = ReadU16(fmt + 12);
        bits_ = ReadU16(fmt + 14);
        if (size > 16) file_.seekg(size - 16, std::ios::cur);
        if (size & 1) file_.seekg(1, std::ios::cur);
        have_format = true;
      } else if (!std::memcmp(chunk, "data", 4)) {
        data_offset_ = static_cast<uint64_t>(static_cast<std::streamoff>(file_.tellg()));
        data_bytes_ = size;
        file_.seekg(size + (size & 1), std::ios::cur);
        have_data = true;
      } else {
        file_.seekg(size + (size & 1), std::ios::cur);
      }
      if (!file_) throw std::runtime_error("Invalid or truncated WAV file.");
    }
    if (!have_format || !have_data || format_ != 1 || bits_ != 16 ||
        channels_ < 1 || channels_ > 2 || sample_rate_ == 0 ||
        block_align_ != channels_ * 2) {
      throw std::runtime_error("Song-cover processing requires mono or stereo 16-bit PCM WAV.");
    }
    frames_ = data_bytes_ / block_align_;
    if (frames_ == 0) throw std::runtime_error("The WAV file contains no audio samples.");
  }

  int channels() const { return channels_; }
  int sampleRate() const { return static_cast<int>(sample_rate_); }
  int64_t frames() const { return static_cast<int64_t>(frames_); }

  std::vector<std::vector<float>> ReadFrames(int64_t start, int count) {
    start = std::max<int64_t>(0, std::min<int64_t>(start, frames_));
    count = std::max(0, std::min<int64_t>(count, frames_ - start));
    std::vector<std::vector<float>> result(channels_, std::vector<float>(count));
    if (count == 0) return result;
    const size_t bytes = static_cast<size_t>(count) * block_align_;
    std::vector<unsigned char> raw(bytes);
    file_.clear();
    file_.seekg(static_cast<std::streamoff>(data_offset_ +
        static_cast<uint64_t>(start) * block_align_), std::ios::beg);
    ReadExact(raw.data(), raw.size());
    for (int frame = 0; frame < count; ++frame) {
      for (int channel = 0; channel < channels_; ++channel) {
        const uint16_t bits = ReadU16(raw.data() +
            static_cast<size_t>(frame) * block_align_ + channel * 2);
        const int16_t sample = static_cast<int16_t>(bits);
        result[channel][frame] = static_cast<float>(sample) / 32768.0f;
      }
    }
    return result;
  }

 private:
  void ReadExact(unsigned char *data, size_t size) {
    file_.read(reinterpret_cast<char *>(data), static_cast<std::streamsize>(size));
    if (file_.gcount() != static_cast<std::streamsize>(size))
      throw std::runtime_error("WAV file ended unexpectedly.");
  }

  std::ifstream file_;
  uint16_t format_ = 0, channels_ = 0, bits_ = 0, block_align_ = 0;
  uint32_t sample_rate_ = 0, data_bytes_ = 0;
  uint64_t data_offset_ = 0, frames_ = 0;
};

class Pcm16WaveWriter {
 public:
  Pcm16WaveWriter(const std::string &path, int sample_rate, int channels)
      : file_(path, std::ios::binary | std::ios::in | std::ios::out | std::ios::trunc),
        sample_rate_(sample_rate), channels_(channels) {
    if (!file_ || sample_rate_ <= 0 || channels_ < 1 || channels_ > 2)
      throw std::runtime_error("Could not create output WAV.");
    unsigned char empty[44] = {};
    file_.write(reinterpret_cast<const char *>(empty), sizeof(empty));
    if (!file_) throw std::runtime_error("Could not initialise output WAV.");
  }

  void Append(const float *const *samples, int source_channels,
              int source_frames, int start, int count) {
    if (count <= 0) return;
    if (source_channels < 1 || source_channels > 2 ||
        start < 0 || start + count > source_frames)
      throw std::runtime_error("Invalid separated audio segment.");
    std::vector<unsigned char> bytes(static_cast<size_t>(count) * channels_ * 2);
    for (int frame = 0; frame < count; ++frame) {
      for (int channel = 0; channel < channels_; ++channel) {
        const int source_channel = source_channels == 1 ? 0 : channel;
        const float value = std::max(-1.0f, std::min(1.0f,
            samples[source_channel][start + frame]));
        const int16_t pcm = static_cast<int16_t>(std::lrint(value * 32767.0f));
        PutU16(bytes.data() + (static_cast<size_t>(frame) * channels_ + channel) * 2,
               static_cast<uint16_t>(pcm));
      }
    }
    file_.write(reinterpret_cast<const char *>(bytes.data()),
                static_cast<std::streamsize>(bytes.size()));
    if (!file_) throw std::runtime_error("Could not write separated WAV audio.");
    frames_ += count;
    if (frames_ * channels_ * 2 > std::numeric_limits<uint32_t>::max() - 36)
      throw std::runtime_error("Output WAV exceeds the standard RIFF size limit.");
  }

  void AppendMixed(const std::vector<std::vector<float>> &samples, int count) {
    std::vector<const float *> ptrs(channels_);
    for (int c = 0; c < channels_; ++c) ptrs[c] = samples[c].data();
    Append(ptrs.data(), channels_, count, 0, count);
  }

  void Finish() {
    if (finished_) return;
    const uint32_t data_size = static_cast<uint32_t>(frames_ * channels_ * 2);
    unsigned char h[44] = {};
    std::memcpy(h, "RIFF", 4);
    PutU32(h + 4, 36 + data_size);
    std::memcpy(h + 8, "WAVEfmt ", 8);
    PutU32(h + 16, 16);
    PutU16(h + 20, 1);
    PutU16(h + 22, static_cast<uint16_t>(channels_));
    PutU32(h + 24, static_cast<uint32_t>(sample_rate_));
    PutU32(h + 28, static_cast<uint32_t>(sample_rate_ * channels_ * 2));
    PutU16(h + 32, static_cast<uint16_t>(channels_ * 2));
    PutU16(h + 34, 16);
    std::memcpy(h + 36, "data", 4);
    PutU32(h + 40, data_size);
    file_.seekp(0, std::ios::beg);
    file_.write(reinterpret_cast<const char *>(h), sizeof(h));
    file_.flush();
    if (!file_) throw std::runtime_error("Could not finalise output WAV.");
    file_.close();
    finished_ = true;
  }

  ~Pcm16WaveWriter() { try { Finish(); } catch (...) {} }

 private:
  std::fstream file_;
  int sample_rate_;
  int channels_;
  uint64_t frames_ = 0;
  bool finished_ = false;
};
}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_SourceSeparationBridge_separateWav(
    JNIEnv *env, jclass, jstring input_path, jstring vocals_path,
    jstring accompaniment_path, jstring vocals_model_path,
    jstring accompaniment_model_path, jint num_threads) {
  try {
    const std::string input = FromJava(env, input_path);
    const std::string vocals_file = FromJava(env, vocals_path);
    const std::string accompaniment_file = FromJava(env, accompaniment_path);
    const std::string vocals_model = FromJava(env, vocals_model_path);
    const std::string accompaniment_model = FromJava(env, accompaniment_model_path);
    if (input.empty() || vocals_file.empty() || accompaniment_file.empty() ||
        vocals_model.empty() || accompaniment_model.empty())
      throw std::runtime_error("Missing source-separation file path.");

    Pcm16WaveReader wave(input);
    SherpaOnnxOfflineSourceSeparationConfig config;
    std::memset(&config, 0, sizeof(config));
    config.model.spleeter.vocals = vocals_model.c_str();
    config.model.spleeter.accompaniment = accompaniment_model.c_str();
    config.model.num_threads = std::max(1, std::min(2, static_cast<int>(num_threads)));
    config.model.provider = "cpu";
    const auto *engine = SherpaOnnxCreateOfflineSourceSeparation(&config);
    if (!engine) throw std::runtime_error("Could not load the offline vocal-separation models.");

    std::unique_ptr<Pcm16WaveWriter> vocals_writer;
    std::unique_ptr<Pcm16WaveWriter> accompaniment_writer;
    const int input_rate = wave.sampleRate();
    const int64_t total_frames = wave.frames();
    const int64_t center_frames = static_cast<int64_t>(input_rate) * 10;
    const int64_t context_frames = static_cast<int64_t>(input_rate);
    bool success = false;
    try {
      for (int64_t center_start = 0; center_start < total_frames;
           center_start += center_frames) {
        const int64_t center_end = std::min(total_frames, center_start + center_frames);
        const int64_t window_start = std::max<int64_t>(0, center_start - context_frames);
        const int64_t window_end = std::min(total_frames, center_end + context_frames);
        const int window_count = static_cast<int>(window_end - window_start);
        auto input_chunk = wave.ReadFrames(window_start, window_count);
        std::vector<const float *> input_ptrs(input_chunk.size());
        for (size_t c = 0; c < input_chunk.size(); ++c) input_ptrs[c] = input_chunk[c].data();

        const auto *output = SherpaOnnxOfflineSourceSeparationProcess(
            engine, input_ptrs.data(), static_cast<int32_t>(input_chunk.size()),
            window_count, input_rate);
        if (!output || !output->stems || output->num_stems < 2 ||
            output->sample_rate <= 0) {
          if (output) SherpaOnnxDestroySourceSeparationOutput(output);
          throw std::runtime_error("Vocal separation failed on an audio segment.");
        }

        const auto &vocal = output->stems[0];
        const auto &music = output->stems[1];
        if (!vocal.samples || !music.samples || vocal.n <= 0 || music.n <= 0 ||
            vocal.num_channels < 1 || vocal.num_channels > 2 ||
            music.num_channels < 1 || music.num_channels > 2) {
          SherpaOnnxDestroySourceSeparationOutput(output);
          throw std::runtime_error("Vocal separation returned invalid audio stems.");
        }
        if (!vocals_writer) {
          vocals_writer = std::make_unique<Pcm16WaveWriter>(
              vocals_file, output->sample_rate, vocal.num_channels);
          accompaniment_writer = std::make_unique<Pcm16WaveWriter>(
              accompaniment_file, output->sample_rate, music.num_channels);
        }
        const int out_start = static_cast<int>(std::llround(
            static_cast<double>(center_start - window_start) *
            output->sample_rate / input_rate));
        const int out_count = static_cast<int>(std::llround(
            static_cast<double>(center_end - center_start) *
            output->sample_rate / input_rate));
        const int vocal_start = std::clamp(out_start, 0, vocal.n);
        const int music_start = std::clamp(out_start, 0, music.n);
        const int vocal_count = std::clamp(out_count, 0, vocal.n - vocal_start);
        const int music_count = std::clamp(out_count, 0, music.n - music_start);
        std::vector<const float *> vocal_ptrs(vocal.num_channels);
        std::vector<const float *> music_ptrs(music.num_channels);
        for (int c = 0; c < vocal.num_channels; ++c) vocal_ptrs[c] = vocal.samples[c];
        for (int c = 0; c < music.num_channels; ++c) music_ptrs[c] = music.samples[c];
        if (vocal_count <= 0 || music_count <= 0 || vocal_count != music_count) {
          SherpaOnnxDestroySourceSeparationOutput(output);
          throw std::runtime_error("The separation model returned inconsistent segment lengths.");
        }
        vocals_writer->Append(vocal_ptrs.data(), vocal.num_channels, vocal.n,
                              vocal_start, vocal_count);
        accompaniment_writer->Append(music_ptrs.data(), music.num_channels, music.n,
                                      music_start, music_count);
        SherpaOnnxDestroySourceSeparationOutput(output);
      }
      vocals_writer->Finish();
      accompaniment_writer->Finish();
      success = true;
    } catch (...) {
      SherpaOnnxDestroyOfflineSourceSeparation(engine);
      throw;
    }
    SherpaOnnxDestroyOfflineSourceSeparation(engine);
    if (!success) throw std::runtime_error("Vocal separation did not complete.");
    return env->NewStringUTF("ok");
  } catch (const std::exception &e) {
    ThrowJava(env, e.what());
    return nullptr;
  }
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_SourceSeparationBridge_mixWav(
    JNIEnv *env, jclass, jstring vocals_path, jstring accompaniment_path,
    jstring output_path, jfloat vocal_gain, jfloat accompaniment_gain) {
  try {
    const std::string vocals_file = FromJava(env, vocals_path);
    const std::string accompaniment_file = FromJava(env, accompaniment_path);
    const std::string output_file = FromJava(env, output_path);
    if (vocals_file.empty() || accompaniment_file.empty() || output_file.empty())
      throw std::runtime_error("Missing song-cover mix file path.");

    Pcm16WaveReader vocals(vocals_file);
    Pcm16WaveReader music(accompaniment_file);
    const int output_rate = music.sampleRate();
    const int output_channels = std::max(vocals.channels(), music.channels());
    const double ratio = static_cast<double>(vocals.sampleRate()) / output_rate;
    const int64_t vocal_output_frames = static_cast<int64_t>(std::ceil(
        static_cast<double>(vocals.frames()) / ratio));
    const int64_t total_frames = std::max<int64_t>(music.frames(), vocal_output_frames);
    Pcm16WaveWriter writer(output_file, output_rate, output_channels);

    constexpr int kBlockFrames = 8192;
    for (int64_t start = 0; start < total_frames; start += kBlockFrames) {
      const int count = static_cast<int>(std::min<int64_t>(kBlockFrames, total_frames - start));
      auto music_block = music.ReadFrames(start, count);
      const int64_t vocal_start = static_cast<int64_t>(std::floor(start * ratio));
      const int64_t vocal_end = static_cast<int64_t>(std::ceil((start + count) * ratio)) + 2;
      auto vocal_block = vocals.ReadFrames(vocal_start,
          static_cast<int>(std::max<int64_t>(0, vocal_end - vocal_start)));
      std::vector<std::vector<float>> mixed(output_channels, std::vector<float>(count, 0.0f));
      for (int frame = 0; frame < count; ++frame) {
        const int64_t output_frame = start + frame;
        const double source_pos = output_frame * ratio - vocal_start;
        const int left = static_cast<int>(std::floor(source_pos));
        const int right = left + 1;
        const float fraction = static_cast<float>(source_pos - left);
        for (int channel = 0; channel < output_channels; ++channel) {
          const int vc = vocals.channels() == 1 ? 0 : channel;
          const int mc = music.channels() == 1 ? 0 : channel;
          float v = 0.0f;
          if (left >= 0 && left < static_cast<int>(vocal_block[vc].size())) {
            const float a = vocal_block[vc][left];
            const float b = right < static_cast<int>(vocal_block[vc].size())
                ? vocal_block[vc][right] : a;
            v = (a + (b - a) * fraction) * vocal_gain;
          }
          const float m = frame < static_cast<int>(music_block[mc].size())
              ? music_block[mc][frame] * accompaniment_gain : 0.0f;
          mixed[channel][frame] = std::max(-1.0f, std::min(1.0f, v + m));
        }
      }
      writer.AppendMixed(mixed, count);
    }
    writer.Finish();
    return env->NewStringUTF(output_file.c_str());
  } catch (const std::exception &e) {
    ThrowJava(env, e.what());
    return nullptr;
  }
}
