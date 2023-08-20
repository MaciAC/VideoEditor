from librosa import load, beat
from cv2 import (VideoCapture,
                 CAP_PROP_FPS,
                 CAP_PROP_FRAME_WIDTH,
                 CAP_PROP_FRAME_HEIGHT,)
from constants import NORM_FPS


class MultiTake:
    def __init__(self, audio_path, video_paths):
        self.audio_path = audio_path
        self.video_paths = video_paths

        self.audio_clip, self.sample_rate = load(self.audio_path, dtype="float64")
        self.audio_tempo, self.audio_beats = beat.beat_track(y=self.audio_clip, sr=self.sample_rate, units="time")
        self.audio_beats = [int(b*float(NORM_FPS)) for b in self.audio_beats]
        self.video_metadata = []
        for v_path in video_paths:
            cap = VideoCapture(v_path)
            # get info from current video in use
            frame_rate = int(cap.get(CAP_PROP_FPS))
            frame_width = int(cap.get(CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(CAP_PROP_FRAME_HEIGHT))
            self.video_metadata.append((frame_width, frame_height, frame_rate))



    def get_video_clip(self, video_idx):
        return VideoCapture(self.video_paths[video_idx])

    def get_video_metadata(self, video_idx):
        return self.video_metadata[video_idx]


if __name__ == "__main__":
    pass
