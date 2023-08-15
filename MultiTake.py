from soundfile import read
import cv2


class MultiTake:
    def __init__(self, audio_path, video_paths):
        self.audio_path = audio_path
        self.video_paths = video_paths

        self.audio_clip, self.sample_rate = read(self.audio_path, dtype="float64")

    def get_video_clip(self, idx):
        return cv2.VideoCapture(self.video_paths[idx])


if __name__ == "__main__":
    pass
