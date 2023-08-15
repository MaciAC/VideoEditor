import subprocess
import re
from time import sleep

NORM_SR = "8000"
NORM_AUDIO_CODEC = "pcm_s16le"
NORM_FPS = "30"
NORM_VIDEO_CODEC = "libx264"


class FFmpegWrapper:
    FFMPEG_COMMAND = (
        'ffmpeg -loglevel error -i "{i_path}" {parameters} "{o_path}" {force}'
    )
    FFMPEG_COMMAND_INSPECT = ["ffmpeg", "-i", ""]

    def __init__(self, force_recreation: bool):
        self.force_recreation = force_recreation

    def create_command(self, parameters: list[str] = [], force=False):
        return self.FFMPEG_COMMAND.format(
            i_path=self.i_path,
            parameters=" ".join(parameters),
            o_path=self.o_path,
            force="-y" if (self.force_recreation or force) else "-n",
        )

    def to_wav(self, i_path: str, o_path: str) -> str:
        self.i_path = i_path
        self.o_path = o_path
        parameters = [
            "-vn",  # Disable video processing
            "-acodec",
            NORM_AUDIO_CODEC,
            "-ar",
            NORM_SR,
            "-ac",
            "1",
        ]
        return self.create_command(parameters)

    def to_mp4(self, i_path: str, o_path: str) -> str:
        self.i_path = i_path
        self.o_path = o_path
        parameters = [
            "-an",  # Disable audio processing
            "-vcodec",
            NORM_VIDEO_CODEC,
            "-r",
            NORM_FPS,
        ]
        return self.create_command(parameters)

    def cut_audio(
        self, i_path: str, o_path: str, start_offset_seconds: int, duration: int
    ) -> str:
        self.i_path = i_path
        self.o_path = o_path
        parameters = [
            "-ss",
            str(start_offset_seconds),  # Set the start offset in seconds
            "-t",
            str(duration),
            "-acodec",
            NORM_AUDIO_CODEC,
            "-ar",
            "44100",  # Copy the audio codec
            "-ac",
            "2",
        ]
        return self.create_command(parameters)

    def cut_video(
        self, i_path: str, o_path: str, start_offset_seconds: int, duration: int
    ) -> str:
        self.i_path = i_path
        self.o_path = o_path
        parameters = [
            "-ss",
            str(start_offset_seconds),  # Set the start offset in seconds
            "-t",
            str(duration),
            "-c:v",
            "copy",  # Copy the video codec
            "-c:a",
            "copy",  # Copy the audio codec
        ]
        return self.create_command(parameters)

    def join_video_and_audio(self, i_a_path: str, i_v_path: str, o_path: str) -> str:
        self.i_path = i_v_path
        self.o_path = o_path
        parameters = [
            "-i",
            i_a_path,
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",  # Resize and crop
            "-c:v",
            "libx264",  # Video codec (H.264)
            "-preset",
            "slow",  # Encoding speed
            "-crf",
            "23",  # Constant Rate Factor (0-51, lower is higher quality, 23 is a good default)
            "-c:a",
            "aac",  # Audio codec (AAC)
            "-b:a",
            "128k",  # Audio bitrate
            "-ar",
            "44100",  # Sample rate
            "-ac",
            "2",  # Stereo
        ]
        return self.create_command(parameters, force=True)

    def get_audio_duration(self, i_path):
        retry = True
        while retry:
            try:
                self.FFMPEG_COMMAND_INSPECT[-1] = i_path
                result = subprocess.run(
                    self.FFMPEG_COMMAND_INSPECT, capture_output=True, text=True
                )
                # Extract the duration from FFmpeg output using regex
                duration_match = re.findall(
                    r"Duration: \d+:\d+:\d+\.\d+", result.stderr
                )
                duration_parts = duration_match[0].replace("Duration: ", "").split(":")
                audio_duration = (
                    int(duration_parts[0]) * 3600
                    + int(duration_parts[1]) * 60
                    + float(duration_parts[2])
                )
                return audio_duration
            except IndexError:
                sleep(0.01)
                continue


if __name__ == "__main__":
    pass