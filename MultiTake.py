from soundfile import read
import cv2


class MultiTake:
    def __init__(self, audio_path, video_paths):
        self.audio_path = audio_path
        self.video_paths = video_paths

        self.audio_clip, self.sample_rate = read(self.audio_path, dtype="float64")
        self.video_clips = [
            cv2.VideoCapture(video_path) for video_path in self.video_paths
        ]


if __name__ == "__main__":
    pass
