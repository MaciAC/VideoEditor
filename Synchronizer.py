import numpy as np
from soundfile import read
from scipy.signal import fftconvolve
from tqdm import tqdm


class Synchronizer:
    def __init__(self, audio_paths):
        self.audios_to_sync = [self.load_audio(p) for p in audio_paths[:-1]]
        self.audio_reference = self.load_audio(audio_paths[-1])

    def load_audio(self, audio_path):
        data, _ = read(audio_path)
        return data

    def find_audio_offset(self, reference_audio, target_audio):
        # Use fftconvolve over inverted reference audio to compute cross correlation efficiently
        cross_correlation = fftconvolve(
            target_audio, reference_audio[::-1], mode="full"
        )
        offset = np.argmax(abs(cross_correlation)) - (len(reference_audio) - 1)
        return offset

    def run(self):
        audio_offsets = []
        for audio in tqdm(self.audios_to_sync, total=(len(self.audios_to_sync))):
            offset = self.find_audio_offset(self.audio_reference, audio)
            audio_offsets.append(offset)
        return audio_offsets


if __name__ == "__main__":
    pass
