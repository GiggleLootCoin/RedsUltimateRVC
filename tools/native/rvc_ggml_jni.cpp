#include <jni.h>

#include "audio/audio_io.h"
#include "engine.h"
#include "gguf/gguf_model.h"
#include "rvc/pipeline.h"
#include "rvc/retrieval.h"

#include <exception>
#include <string>

namespace {
class UtfChars {
public:
    UtfChars(JNIEnv* env, jstring value) : env_(env), value_(value) {
        if (value_) chars_ = env_->GetStringUTFChars(value_, nullptr);
    }
    ~UtfChars() {
        if (chars_) env_->ReleaseStringUTFChars(value_, chars_);
    }
    std::string str() const { return chars_ ? std::string(chars_) : std::string(); }
private:
    JNIEnv* env_;
    jstring value_;
    const char* chars_ = nullptr;
};
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_ultimatervc_mobile_RvcGgmlNative_convert(
    JNIEnv* env, jobject,
    jstring hubert_path, jstring rmvpe_path, jstring voice_path, jstring index_path,
    jstring input_path, jstring output_path,
    jint pitch, jint sid, jfloat index_rate, jfloat protect, jfloat rms_mix_rate) {
    try {
        UtfChars hubert_s(env, hubert_path), rmvpe_s(env, rmvpe_path), voice_s(env, voice_path);
        UtfChars index_s(env, index_path), input_s(env, input_path), output_s(env, output_path);
        const std::string hubert_file = hubert_s.str();
        const std::string rmvpe_file = rmvpe_s.str();
        const std::string voice_file = voice_s.str();
        const std::string index_file = index_s.str();
        const std::string input_file = input_s.str();
        const std::string output_file = output_s.str();

        if (hubert_file.empty() || rmvpe_file.empty() || voice_file.empty() ||
            input_file.empty() || output_file.empty()) {
            throw std::runtime_error("Missing required model or audio path.");
        }
        if (index_rate < 0.0f || index_rate > 1.0f ||
            protect < 0.0f || protect > 0.5f ||
            rms_mix_rate < 0.0f || rms_mix_rate > 1.0f) {
            throw std::runtime_error("Conversion settings are outside their supported ranges.");
        }

        rvc::GgmlDevice device(99); // CPU-only first release; no Vulkan/NNAPI assumptions.
        GgufModel hubert, rmvpe, voice;
        hubert.load(hubert_file, device.backend());
        rmvpe.load(rmvpe_file, device.backend());
        voice.load(voice_file, device.backend());

        rvc::RetrievalIndex index;
        if (!index_file.empty()) index.load(index_file, device.backend());

        rvc::RvcPipeline pipeline(hubert, rmvpe, voice, device.backend());
        const AudioData source = load_wav(input_file);
        const std::vector<float> audio_16k = to_mono_16k(source, 16000);
        rvc::ConvertOptions options;
        options.f0_up_key = static_cast<int>(pitch);
        options.sid = static_cast<int>(sid);
        options.index_rate = static_cast<float>(index_rate);
        options.protect = static_cast<float>(protect);
        options.rms_mix_rate = static_cast<float>(rms_mix_rate);
        options.index = index.loaded() ? &index : nullptr;
        options.verbose = false;

        const rvc::ConvertResult converted = pipeline.convert(audio_16k, options);
        if (converted.pcm.empty() || converted.sample_rate < 16000) {
            throw std::runtime_error("The RVC engine returned no valid converted audio.");
        }
        if (!save_wav_i16(output_file, converted.pcm.data(), 1,
                          converted.sample_rate, converted.pcm.size())) {
            throw std::runtime_error("Could not write the converted WAV file.");
        }
        return env->NewStringUTF("");
    } catch (const std::exception& error) {
        return env->NewStringUTF(error.what());
    } catch (...) {
        return env->NewStringUTF("Unknown native RVC conversion error.");
    }
}
