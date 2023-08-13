from moviepy.editor import VideoFileClip, AudioFileClip

class MultiTake:
    def __init__(self, audio_path, video_paths):
        self.audio_path = audio_path
        self.video_paths = video_paths

        self.audio_clip = AudioFileClip(self.audio_path)
        self.video_clips = [VideoFileClip(video_path, audio=False) for video_path in self.video_paths]


if __name__ == "__main__":
    pass
