import numpy as np
from soundfile import read
from scipy.signal import fftconvolve


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

    def run(self) -> list[tuple[float, float]]:
        """
        return start and end offsets, both computed having as zero the start and end second of the audio reference.
        if both offset positive, audio starts and ends before reference
        reference     |-----------|
        audio       |------|
        if both offset negative, audio starts and ends after reference
        reference     |-----------|
        audio               |--------|
        start negative end positive
        reference     |-----------|
        audio           |------|
        start positive end negative
        reference     |-----------|
        audio      |-------------------|
        """
        audio_offsets = []
        for audio in self.audios_to_sync:
            start_offset = self.find_audio_offset(self.audio_reference, audio)
            end_offset = self.audio_reference.size - (audio.size + start_offset)
            audio_offsets.append((start_offset, end_offset))
        return audio_offsets


if __name__ == "__main__":
    pass
