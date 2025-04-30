import openai
import os
import wave
import pyaudio
import webrtcvad
import numpy as np
import scipy.signal as signal
import whisper
from src.utils.constant import OpenAIConfig


class AudioTranscriber:
    def __init__(self):
        self.api_key = OpenAIConfig.OpenAI_API_KEY
        self.model = whisper.load_model("tiny")

    def audio_to_text(self, audio_file, target_language='en'):
        openai.api_key = self.api_key # Set the API key
        try:
            with open(audio_file, "rb") as file:
                response = openai.Audio.transcribe(
                    model='whisper-1',
                    file=file,
                    response_format='verbose_json',  # Use 'verbose_json' to get more details
                    language=target_language
                )

                audio = whisper.load_audio(audio_file)
                audio = whisper.pad_or_trim(audio)

                # make log-Mel spectrogram and move to the same device as the model
                mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

                # detect the spoken language
                _, probs = self.model.detect_language(mel)
            transcription_text = response.get("text")
            detected_language = response.get("language")
            return transcription_text, max(probs, key=probs.get)
        except Exception as e:
            print(f"An error occurred: {e}")
            return None, None


# noinspection PyTupleAssignmentBalance
class AudioRecorder:
    def __init__(self, chunk_duration_ms=10, format=pyaudio.paInt16, channels=1, rate=16000,
                 max_silence_duration_ms=1500, vad_mode=3):
        self.CHUNK_DURATION_MS = chunk_duration_ms  # 10ms per chunk
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate  # 16kHz sampling rate
        self.CHUNK_SIZE = int(self.RATE * self.CHUNK_DURATION_MS / 1000)
        self.MAX_SILENCE_DURATION_MS = max_silence_duration_ms  # Maximum silence duration to consider as end of speech
        self.vad_mode = vad_mode

        self.p = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(self.vad_mode)  # Set aggressiveness mode (0-3)
        self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS,
                                  rate=self.RATE, input=True,
                                  frames_per_buffer=self.CHUNK_SIZE)
        self.frames = []
        self.silence_duration = 0
        self.audio_transcriber = AudioTranscriber()

    def is_speech(self, chunk):
        return self.vad.is_speech(chunk, self.RATE)

    def reduce_noise(self, chunk):
        audio_data = np.frombuffer(chunk, dtype=np.int16)
        # Apply a simple high-pass filter to remove low-frequency noise
        b, a = signal.butter(1, 100 / (self.RATE / 2), btype='high')
        filtered_audio = signal.lfilter(b, a, audio_data)
        return filtered_audio.astype(np.int16).tobytes()

    def record(self):
        print("Listening...")

        while True:
            chunk = self.stream.read(self.CHUNK_SIZE)
            # Apply noise reduction
            chunk = self.reduce_noise(chunk)
            self.frames.append(chunk)

            # Detect if the chunk contains speech
            if self.is_speech(chunk):
                self.silence_duration = 0
            else:
                self.silence_duration += self.CHUNK_DURATION_MS

            # Stop recording if silence duration exceeds threshold
            if self.silence_duration > self.MAX_SILENCE_DURATION_MS:
                break

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        # Save the recorded audio
        file_path = "./user_question.wav"
        self.save_audio(file_path)
        print(f"Audio saved to {file_path}")
        text, language = self.audio_transcriber.audio_to_text(file_path)
        print('Language:- ', language)
        print('Transcribe text:- ', text)

    def save_audio(self, file_path):
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))


if __name__ == "__main__":
    # Example of creating an instance with custom parameters
    while True:
        recorder = AudioRecorder(chunk_duration_ms=10, format=pyaudio.paInt16, channels=1, rate=16000,
                                 max_silence_duration_ms=1500, vad_mode=3)

        recorder.record()