from os.path import join, exists
from os import listdir, mkdir
import subprocess

from FfmpegWraper import FFmpegWrapper
from Synchronizer import Synchronizer

from constants import (NORM_SR,
                       TMP_BLACK_VIDEO,
                       AUDIO_FOLDER,
                       VIDEO_FOLDER,
                       NORM_AUDIO_FOLDER,
                       NORM_VIDEO_FOLDER,
                       VIDEO_SYNC_FOLDER,)


def get_width_height_framerate(input_video):
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
        input_video
    ]
    ffprobe_output = subprocess.check_output(ffprobe_cmd, text=True)
    try:
        width, height, frame_rate = ffprobe_output.strip().split("x")
    except ValueError:
        width, height, frame_rate, _ = ffprobe_output.strip().split("x")
        print(width, height, frame_rate, _)
    if '/' in frame_rate:
        num, den = frame_rate.split('/')
        frame_rate = float(num)/float(den)
    else:
        frame_rate = float(frame_rate)
    return int(width), int(height), frame_rate

class FileManager:
    def __init__(self, base_folder, force_recreation=False) -> None:
        self.force_recreation = force_recreation
        self.base_folder = base_folder
        self.audio_filepath = self._get_filepaths(AUDIO_FOLDER)[0]
        self.video_filepaths = sorted(self._get_filepaths(VIDEO_FOLDER))
        self.video_resolution = [get_width_height_framerate(p) for p in self.video_filepaths]
        self.ffmpeg_commands = FFmpegWrapper(self.force_recreation)

    def _get_filepaths(self, folder_name):
        return [
            join(self.base_folder, folder_name, filename)
            for filename in listdir(join(self.base_folder, folder_name))
        ]

    def set_offsets(self, offsets: list[int]) -> None:
        # convert from sample number to second.ms
        self.start_offsets = [o[0] / int(NORM_SR) for o in offsets]
        self.finish_offsets = [o[1] / int(NORM_SR) for o in offsets]

    def check_in_basefolder_and_create(self, folder):
        out_folder = join(self.base_folder, folder)
        if not exists(out_folder):
            mkdir(out_folder)
        return out_folder

    def create_normalized_audiofiles(self) -> list[str]:
        """
        Convert reference audio and reate normalized audio files from video for synch purposes
        """
        out_folder = self.check_in_basefolder_and_create(NORM_AUDIO_FOLDER)
        out_paths = []
        for input_video_path in self.video_filepaths + [self.audio_filepath]:
            out_path = join(
                out_folder,
                input_video_path.split("/")[-1].rsplit(".", 1)[0] + ".wav",
            )
            self.ffmpeg_commands.to_wav(input_video_path, out_path)
            out_paths.append(out_path)
        self.normalized_audiopaths = out_paths
        n_files = len(out_paths)
        print(f"Creating {n_files} normalized audiofiles...")
        self.ffmpeg_commands.run_current_batch(n_processes=n_files)

    def normalize_sync_videofiles(self) -> list[str]:
        """
        Create copies of all videos normalized
        """
        out_folder = self.check_in_basefolder_and_create(NORM_VIDEO_FOLDER)
        out_paths = []
        ffmpeg_commands = []
        for input_video_path in self.sync_videopaths:
            out_path = join(
                out_folder,
                input_video_path.split("/")[-1].rsplit(".", 1)[0] + ".mp4",
            )
            ffmpeg_commands.append(
                self.ffmpeg_commands.to_mp4(input_video_path, out_path)
            )
            out_paths.append(out_path)
        self.normalized_videopaths = out_paths
        n_files = len(out_paths)
        print(f"Creating {n_files} normalized sync videofiles...")
        self.ffmpeg_commands.run_current_batch(n_processes=n_files)

    def cut_videos_based_on_offsets(self, start: int, duration: int):
        """
            cut audio from start to start + duration
            compute seconds where each video is present in relation to video and cut

        """
        synchronizer = Synchronizer(self.normalized_audiopaths)
        self.set_offsets(synchronizer.run())
        out_folder = self.check_in_basefolder_and_create(VIDEO_SYNC_FOLDER)
        # Manage audio crop and get final duration
        audio_out_path = join(
            out_folder,
            self.audio_filepath.split("/")[-1].rsplit(".", 1)[0] + ".wav",
        )
        self.ffmpeg_commands.cut_audio(
            self.audio_filepath,
            audio_out_path,
            start,
            duration,
        )
        self.sync_audiopath = audio_out_path
        print("Cut audio...")
        self.ffmpeg_commands.run_current_batch(n_processes=1)
        self.audio_duration = self.ffmpeg_commands.get_audio_duration(audio_out_path)

        # manage videos
        videos_out_path = []
        for video_path, start_offset in zip(self.video_filepaths, self.start_offsets):
            out_path = join(
                out_folder,
                video_path.split("/")[-1].rsplit(".", 1)[0] + ".mp4",
            )
            start_cut = max(0.0, start_offset + start)
            print("Cut", video_path)
            self.ffmpeg_commands.cut_video(
                video_path, out_path, start_cut, self.audio_duration
            )
            videos_out_path.append(out_path)
        n_files = len(videos_out_path)
        print(f"Cutting {n_files} videofiles...")
        self.ffmpeg_commands.run_current_batch(n_processes=n_files)
        self.sync_videopaths = videos_out_path

    # def add_padding_based_on_offsets(self, start: int):
    #     ffmpeg_commands = []
    #     for video_path, start_offset, resolution in zip(self.sync_videopaths, self.start_offsets, self.video_resolution):
    #         start_cut = start_offset + start
    #         if start_cut > -self.audio_duration:
    #             ffmpeg_commands.append(
    #                 self.ffmpeg_commands.generate_black_video(TMP_BLACK_VIDEO, self.audio_duration, *resolution)
    #             )
    #             print("Pad", video_path)
    #                 self.ffmpeg_commands.pad_video(
    #                     video_path, video_path, -start_cut, self.audio_duration, *resolution
    #                 )
    #     print("Pad Video...")
    #     self.ffmpeg_commands.run_current_batch(n_processes=1)
    #     # 1 process to ensure that black video is created before the pad command is run...
    #     # needs refactor, naybe move command run to ffmpegwrapper and run commands in batch, each batch a process: generate, cut, pad...

    def video_audio_to_instavideo(
        self, input_audio_path, input_video_path, output_video_path
    ):
        print("Joining video and audio...")
        self.ffmpeg_commands.join_video_and_audio(
            input_audio_path, input_video_path, output_video_path
        )
        self.ffmpeg_commands.run_current_batch()


if __name__ == "__main__":
    pass
