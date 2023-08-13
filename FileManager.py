from os.path import join, exists
from os import listdir, mkdir
import subprocess
from tqdm import tqdm
import re

from Synchronizer import Synchronizer

AUDIO_FOLDER = "Audio"
VIDEO_FOLDER = "Videos"
NORM_AUDIO_FOLDER = "NormAudio"
VIDEO_SYNC_FOLDER = "VideoSync"
INPUT_FILE_IDX = 2
OUTPUT_FILE_IDX = 10
NORM_SR = "8000"
NORM_CODEC = "pcm_s16le"


class FileManager:
    def __init__(self, base_folder, force_recreation=False) -> None:
        self.force_recreation = force_recreation
        self.base_folder = base_folder
        self.audio_filepath = self._get_filepaths(AUDIO_FOLDER)[0]
        self.video_filepaths = sorted(self._get_filepaths(VIDEO_FOLDER))

    def _get_filepaths(self, folder_name):
        return [
            join(self.base_folder, folder_name, filename)
            for filename in listdir(join(self.base_folder, folder_name))
        ]

    def set_offsets(self, offsets: list[int]) -> None:
        # convert from sample number to second.ms
        self.offsets = [o / int(NORM_SR) for o in offsets]

    def convert_to_wav(self, input_video_path, output_video_path):
        ffmpeg_command = [
            "ffmpeg",
            "-i",
            input_video_path,
            "-vn",  # Disable video processing
            "-acodec",
            NORM_CODEC,
            "-ar",
            NORM_SR,
            "-ac",
            "1",
            output_video_path,
            "-y" if self.force_recreation else "-n",
        ]
        subprocess.run(ffmpeg_command, capture_output=True, text=True)

    def create_normalized_audiofiles(self) -> list[str]:
        out_folder = join(self.base_folder, NORM_AUDIO_FOLDER)
        if not exists(out_folder):
            mkdir(out_folder)
        out_paths = []
        for input_video_path in tqdm(
            self.video_filepaths + [self.audio_filepath],
            total=len(self.video_filepaths),
        ):
            out_path = join(
                self.base_folder,
                NORM_AUDIO_FOLDER,
                input_video_path.split("/")[-1].rsplit(".", 1)[0] + ".wav",
            )
            self.convert_to_wav(input_video_path, out_path)
            out_paths.append(out_path)
        self.normalized_audiopaths = out_paths

    def convert_video_for_instagram(self, input_video_path, output_video_path):
        ffmpeg_command = [
            "ffmpeg",
            "-i",
            input_video_path,
            "-vf",
            "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080",  # Resize and crop
            "-c:v",
            "libx264",  # Video codec (H.264)
            "-preset",
            "slow",  # Choose encoding speed (options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
            "-crf",
            "23",  # Constant Rate Factor (0-51, lower is higher quality, 23 is a good default)
            "-c:a",
            "aac",  # Audio codec (AAC)
            "-b:a",
            "128k",  # Audio bitrate
            "-ar",
            "44100",  # Sample rate
            "-ac",
            "2",  # Number of audio channels (stereo)
            output_video_path,
            "-y" if self.force_recreation else "-n",
        ]
        subprocess.run(ffmpeg_command, capture_output=True, text=True)

    def cut_video(
        self, input_video_path, output_video_path, start_offset_seconds, duration
    ):
        ffmpeg_command = [
            "ffmpeg",
            "-ss",
            str(start_offset_seconds),  # Set the start offset in seconds
            "-t",
            str(duration),
            "-i",
            input_video_path,
            "-c:v",
            "copy",  # Copy the video codec
            "-c:a",
            "copy",  # Copy the audio codec
            output_video_path,
            "-y" if self.force_recreation else "-n",
        ]
        subprocess.run(ffmpeg_command, capture_output=True, text=True)

    def cut_audio(self, input_audio_path, output_audio_path, start_offset_seconds):
        ffmpeg_command = [
            "ffmpeg",
            "-ss",
            str(start_offset_seconds),  # Set the start offset in seconds
            "-i",
            input_audio_path,
            "-acodec",
            NORM_CODEC,
            "-ar",
            "44100",  # Copy the audio codec
            "-ac",
            "2",
            output_audio_path,
            "-y" if self.force_recreation else "-n",
        ]
        if not self.force_recreation:
            return
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        # Extract the duration from FFmpeg output using regex
        duration_match = re.findall(r"time=\d+:\d+:\d+\.\d+", result.stderr)
        duration_parts = duration_match[1].replace("time=", "").split(":")
        audio_duration = (
            int(duration_parts[0]) * 3600
            + int(duration_parts[1]) * 60
            + float(duration_parts[2])
        )
        return audio_duration

    def cut_videos_based_on_offsets(self):
        synchronizer = Synchronizer(self.normalized_audiopaths)
        self.set_offsets(synchronizer.run())
        out_folder = join(self.base_folder, VIDEO_SYNC_FOLDER)
        if not exists(out_folder):
            mkdir(out_folder)
        # zero represents de reference_audio offset, if min offset is negative audio file is cut
        min_offset = min(self.offsets + [0])

        audio_out_path = join(
            self.base_folder,
            VIDEO_SYNC_FOLDER,
            self.audio_filepath.split("/")[-1].rsplit(".", 1)[0] + ".wav",
        )
        audio_duration = self.cut_audio(
            self.audio_filepath, audio_out_path, -min_offset if min_offset < 0 else 0.0
        )
        videos_out_path = []
        for video_path, offset in tqdm(
            zip(self.video_filepaths, self.offsets), total=len(self.offsets)
        ):
            out_path = join(
                self.base_folder,
                VIDEO_SYNC_FOLDER,
                video_path.split("/")[-1].rsplit(".", 1)[0] + ".mp4",
            )
            self.cut_video(video_path, out_path, offset - min_offset, audio_duration)
            videos_out_path.append(out_path)
        return audio_out_path, videos_out_path


if __name__ == "__main__":
    pass
