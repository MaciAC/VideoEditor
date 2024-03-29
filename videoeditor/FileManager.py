from logging import info
from os import listdir, mkdir
from os.path import join
from shutil import rmtree

from constants import (
    AUDIO_FOLDER,
    NORM_AUDIO_FOLDER,
    NORM_SR,
    NORM_VIDEO_FOLDER,
    VIDEO_FOLDER,
    VIDEO_SYNC_FOLDER,
)
from cv2 import imwrite
from FfmpegWraper import FFmpegWrapper
from numpy import uint8, zeros
from Synchronizer import Synchronizer
from tempfile import mkdtemp


class FileManager:
    def __init__(
        self,
        base_folder,
    ) -> None:
        self.base_folder = base_folder
        self.temp_folder = mkdtemp(dir=self.base_folder)
        self.audio_filepath = self._get_filepaths(AUDIO_FOLDER)[0]
        self.video_filepaths = sorted(self._get_filepaths(VIDEO_FOLDER))
        self.ffmpeg_commands = FFmpegWrapper()
        self.videos_resolution = [
            self.ffmpeg_commands.get_width_height_framerate(p) for p in self.video_filepaths
        ]
        self.audio_duration = self.ffmpeg_commands.get_audio_duration(self.audio_filepath)

    def remove_tmp_folder_and_contents(
        self,
    ):
        try:
            rmtree(self.temp_folder)
            info(f"Folder '{self.temp_folder}' and its contents have been removed.")
        except Exception as e:
            info(f"An error occurred: {e}")

    def _get_filepaths(
        self,
        folder_name,
    ):
        return [
            join(
                self.base_folder,
                folder_name,
                filename,
            )
            for filename in listdir(
                join(
                    self.base_folder,
                    folder_name,
                )
            )
        ]

    def set_offsets(
        self,
        offsets: list[int],
    ) -> None:
        # convert from sample number to second.ms
        self.start_offsets = [o[0] / int(NORM_SR) for o in offsets]
        self.finish_offsets = [o[1] / int(NORM_SR) for o in offsets]

    def create_normalized_audiofiles(
        self,
    ) -> list[str]:
        """
        Convert reference audio and reate normalized audio files from video for synch purposes
        """
        out_folder = join(self.temp_folder, NORM_AUDIO_FOLDER)
        mkdir(out_folder)
        out_paths = []
        for input_video_path in self.video_filepaths + [self.audio_filepath]:
            out_path = join(
                out_folder,
                input_video_path.split("/")[-1].rsplit(
                    ".",
                    1,
                )[0]
                + ".wav",
            )
            self.ffmpeg_commands.to_wav(
                input_video_path,
                out_path,
            )
            out_paths.append(out_path)
        self.normalized_audiopaths = out_paths
        n_files = len(out_paths)
        info(f"Creating {n_files} normalized audiofiles...")
        self.ffmpeg_commands.run_current_batch(n_processes=n_files)

    def normalize_sync_videofiles(
        self,
    ) -> list[str]:
        """
        Create copies of all videos normalized
        """
        out_folder = join(self.temp_folder, NORM_VIDEO_FOLDER)
        mkdir(out_folder)
        out_paths = []
        for input_video_path in self.sync_videopaths:
            out_path = join(
                out_folder,
                input_video_path.split("/")[-1].rsplit(
                    ".",
                    1,
                )[0]
                + ".mp4",
            )
            self.ffmpeg_commands.to_mp4(
                input_video_path,
                out_path,
            )
            out_paths.append(out_path)
        self.normalized_videopaths = out_paths
        n_files = len(out_paths)
        info(f"Creating {n_files} normalized sync videofiles...")
        self.ffmpeg_commands.run_current_batch(n_processes=n_files)

    def cut_audio_based_on_offsets(
        self,
        out_folder,
        start: int,
        duration: int,
    ):
        # Manage audio crop and get final duration
        audio_out_path = join(
            out_folder,
            self.audio_filepath.split("/")[-1].rsplit(
                ".",
                1,
            )[0]
            + ".wav",
        )
        self.ffmpeg_commands.cut_audio(
            self.audio_filepath,
            audio_out_path,
            start,
            duration,
        )
        self.sync_audiopath = audio_out_path
        info(f"Cut sync audiofile...")
        self.ffmpeg_commands.run_current_batch(n_processes=1)
        self.audio_cut_duration = self.ffmpeg_commands.get_audio_duration(audio_out_path)

    def cut_videos_based_on_offsets(
        self,
        start: int,
        duration: int,
    ):
        """
        cut audio from start to start + duration
        compute seconds where each video is present in relation to video and cut

        """
        synchronizer = Synchronizer(self.normalized_audiopaths)
        self.set_offsets(synchronizer.run())
        out_folder = join(self.temp_folder, VIDEO_SYNC_FOLDER)
        mkdir(out_folder)
        self.cut_audio_based_on_offsets(
            out_folder,
            start,
            duration,
        )

        videos_out_path = []
        for (
            video_path,
            start_offset,
        ) in zip(
            self.video_filepaths,
            self.start_offsets,
        ):
            out_path = join(
                out_folder,
                video_path.split("/")[-1].rsplit(
                    ".",
                    1,
                )[0]
                + ".mp4",
            )
            start_cut = max(
                0.0,
                start_offset + start,
            )
            self.ffmpeg_commands.cut_video(
                video_path,
                out_path,
                start_cut,
                duration,
            )
            videos_out_path.append(out_path)
        n_files = len(videos_out_path)
        info(f"Cutting {n_files} videofiles...")
        self.ffmpeg_commands.run_current_batch(n_processes=n_files)
        self.sync_videopaths = videos_out_path
        return (
            self.start_offsets,
            self.finish_offsets,
        )

    def create_black_image(
        self,
        output_path,
        width,
        height,
    ):
        black_image = zeros(
            (
                height,
                width,
                3,
            ),
            dtype=uint8,
        )
        imwrite(
            output_path,
            black_image,
        )

    def video_audio_to_instavideo(
        self,
        input_audio_path,
        input_video_path,
        output_video_path,
    ):
        info("Joining video and audio...")
        self.ffmpeg_commands.join_video_and_audio(
            input_audio_path,
            input_video_path,
            output_video_path,
        )
        self.ffmpeg_commands.run_current_batch()


if __name__ == "__main__":
    pass
