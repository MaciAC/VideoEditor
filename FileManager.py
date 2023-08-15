from os.path import join, exists
from os import listdir, mkdir
import subprocess

from FfmpegWraper import FFmpegWrapper, NORM_SR
from Synchronizer import Synchronizer

AUDIO_FOLDER = "Audio"
VIDEO_FOLDER = "Videos"
NORM_AUDIO_FOLDER = "NormAudio"
NORM_VIDEO_FOLDER = "NormVideo"
VIDEO_SYNC_FOLDER = "VideoSync"


class FileManager:
    def __init__(self, base_folder, force_recreation=False) -> None:
        self.force_recreation = force_recreation
        self.base_folder = base_folder
        self.audio_filepath = self._get_filepaths(AUDIO_FOLDER)[0]
        self.video_filepaths = sorted(self._get_filepaths(VIDEO_FOLDER))
        self.ffmpeg_commands = FFmpegWrapper(self.force_recreation)

    def _get_filepaths(self, folder_name):
        return [
            join(self.base_folder, folder_name, filename)
            for filename in listdir(join(self.base_folder, folder_name))
        ]

    def set_offsets(self, offsets: list[int]) -> None:
        # convert from sample number to second.ms
        self.offsets = [o / int(NORM_SR) for o in offsets]

    def check_in_basefolder_and_create(self, folder):
        out_folder = join(self.base_folder, folder)
        if not exists(out_folder):
            mkdir(out_folder)
        return out_folder

    def run_commands_multiprocess(self, cmds: list[str], silent=False, n_processes=4):
        CMD_LIST = ".cmd.lst"
        MULTIPROCESS_COMMAND = f"cat {CMD_LIST} | xargs -n1 -P{n_processes} sh -c"
        cmds = "'\n'".join(cmds)
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
        else:
            print(f"Subprocess completed with an error (return code: {return_code})")

    def create_normalized_audiofiles(self) -> list[str]:
        """
        Convert reference audio and reate normalized audio files from video for synch purposes
        """
        out_folder = self.check_in_basefolder_and_create(NORM_AUDIO_FOLDER)
        out_paths = []
        ffmpeg_commands = []
        for input_video_path in self.video_filepaths + [self.audio_filepath]:
            out_path = join(
                out_folder,
                input_video_path.split("/")[-1].rsplit(".", 1)[0] + ".wav",
            )
            ffmpeg_commands.append(
                self.ffmpeg_commands.to_wav(input_video_path, out_path)
            )

            out_paths.append(out_path)
        print("Creating normalized audiofiles...")
        self.run_commands_multiprocess(ffmpeg_commands)
        self.normalized_audiopaths = out_paths

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
        print("Creating normalized sync videofiles...")
        self.run_commands_multiprocess(ffmpeg_commands)
        self.normalized_videopaths = out_paths

    def cut_videos_based_on_offsets(self, duration: int):
        synchronizer = Synchronizer(self.normalized_audiopaths)
        self.set_offsets(synchronizer.run())
        out_folder = self.check_in_basefolder_and_create(VIDEO_SYNC_FOLDER)
        # zero represents de reference_audio offset, if min offset is negative audio file is cut
        min_offset = min(self.offsets + [0])

        audio_out_path = join(
            out_folder,
            self.audio_filepath.split("/")[-1].rsplit(".", 1)[0] + ".wav",
        )
        ffmpeg_command = self.ffmpeg_commands.cut_audio(
            self.audio_filepath,
            audio_out_path,
            -min_offset if min_offset < 0 else 0.0,
            duration,
        )
        print("Cut audio...")
        self.run_commands_multiprocess([ffmpeg_command], n_processes=1)
        audio_duration = self.ffmpeg_commands.get_audio_duration(audio_out_path)
        videos_out_path = []
        ffmpeg_commands = []
        for video_path, offset in zip(self.video_filepaths, self.offsets):
            out_path = join(
                out_folder,
                video_path.split("/")[-1].rsplit(".", 1)[0] + ".mp4",
            )
            ffmpeg_commands.append(
                self.ffmpeg_commands.cut_video(
                    video_path, out_path, offset - min_offset, audio_duration
                )
            )
            videos_out_path.append(out_path)
        print("Cut Video...")
        self.run_commands_multiprocess(ffmpeg_commands)
        self.sync_audiopath = audio_out_path
        self.sync_videopaths = videos_out_path

    def video_audio_to_instavideo(
        self, input_audio_path, input_video_path, output_video_path
    ):
        print("Joining video and audio...")
        ffmpeg_command = self.ffmpeg_commands.join_video_and_audio(
            input_audio_path, input_video_path, output_video_path
        )
        self.run_commands_multiprocess([ffmpeg_command], 1)


if __name__ == "__main__":
    pass
