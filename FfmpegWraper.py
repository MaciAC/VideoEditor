import subprocess
import re
from time import sleep

from constants import (
    NORM_AUDIO_CODEC,
    NORM_SR,
    NORM_VIDEO_CODEC,
    NORM_FPS,
    CMD_LIST,
)


class FFmpegWrapper:
    FFMPEG_COMMAND = 'ffmpeg -loglevel error {input} {parameters} "{o_path}" -y'
    FFMPEG_COMMAND_INSPECT = ["ffmpeg", "-i", ""]

    def __init__(self):
        self.current_command_batch = []

    def create_command(self, parameters: list[str] = []):
        input = '-i "{}"'.format(self.i_path) if self.i_path != "" else ""
        self.current_command_batch.append(
            self.FFMPEG_COMMAND.format(
                input=input,
                parameters=" ".join(parameters),
                o_path=self.o_path,
            )
        )

    def run_current_batch(self, n_processes=1):
        MULTIPROCESS_COMMAND = f"cat {CMD_LIST} | xargs -n1 -P{n_processes} sh -c"
        cmds = "'\n'".join(self.current_command_batch)
        cmds_str = f"'{cmds}'\n"
        with open(CMD_LIST, "w") as f:
            f.write(cmds_str)
        process = subprocess.Popen(
            [MULTIPROCESS_COMMAND],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Wait for the subprocess to complete
        process.wait()

        # Check the return code to determine if the subprocess completed successfully
        return_code = process.returncode
        if return_code == 0:
            print("Completed!")
            self.current_command_batch = []
        else:
            print(f"Subprocess completed with an error (return code: {return_code})")

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
        self.create_command(parameters)

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
        self.create_command(parameters)

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
        self.create_command(parameters)

    def cut_video(
        self, i_path: str, o_path: str, start_offset_seconds: int, duration: int
    ) -> str:
        self.i_path = i_path
        self.o_path = o_path
        parameters = [
            "-ss",
            "{:.1f}".format(start_offset_seconds),  # Set the start offset in seconds
            "-t",
            "{:.1f}".format(duration),
            "-c:v",
            "copy",  # Copy the video codec
            "-c:a",
            "copy",  # Copy the audio codec
        ]
        self.create_command(parameters)

    # def pad_video(
    #     self, i_path: str, o_path: str, start_pad_seconds: int, duration: int, width, height, frame_rate,
    # ) -> str:
    #     """
    #         pad video assumes a black video is created.
    #         actually concats black video with i_path's video
    #         ffmpeg concat needs sequence of videos in a file
    #     """
    #     # create file with sequence command
    #     sequence = "\n".join([
    #         f"file {TMP_BLACK_VIDEO}", "outpoint {:.2f}".format(start_pad_seconds),
    #         f"file \"{i_path}\"", "outpoint {:.2f}".format(duration-start_pad_seconds),
    #     ])
    #     self.i_path = ""
    #     self.o_path = o_path
    #     parameters = [
    #         "-f", "concat",
    #         "-safe", "0",
    #         "-i", "txt.txt",
    #         "-c:v", "qtrle",
    #         "-c:a", "copy"
    #     ]
    #     return f"echo '{sequence}'> txt.txt && " + self.create_command(parameters)

    def generate_black_video(self, o_path: str, duration, width, height, frame_rate):
        self.i_path = ""
        self.o_path = o_path
        parameters = [
            "-f",
            "lavfi",
            "-i",
            f"color=black:s={width}x{height}:r={frame_rate}",
            "-f",
            "lavfi",
            "-i",
            "anullsrc",
            "-t",
            "{:.1f}".format(duration),
        ]
        self.create_command(parameters)

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
        self.create_command(parameters)

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

    def get_width_height_framerate(self, input_video):
        # Run ffprobe to get resolution and frame rate
        ffprobe_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-of",
            "csv=s=x:p=0",
            input_video,
        ]
        ffprobe_output = subprocess.check_output(ffprobe_cmd, text=True)
        try:
            width, height, frame_rate = ffprobe_output.strip().split("x")
        except ValueError:
            width, height, frame_rate, _ = ffprobe_output.strip().split("x")
            print(width, height, frame_rate, _)
        if "/" in frame_rate:
            num, den = frame_rate.split("/")
            frame_rate = float(num) / float(den)
        else:
            frame_rate = float(frame_rate)
        return int(width), int(height), frame_rate


if __name__ == "__main__":
    pass
