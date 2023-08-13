from Synchronizer import Synchronizer
from FileManager import FileManager
from argparse import ArgumentParser


class MultiTake:
    def __init__(self, base_folder: str, force_recreation=False):
        self.base_folder = base_folder
        self.file_manager = FileManager(self.base_folder, force_recreation)
        self.file_manager.create_normalized_audiofiles()
        (
            self.sync_audio_path,
            self.sync_video_paths,
        ) = self.file_manager.cut_videos_based_on_offsets()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--folder", action="store", type=str, required=True, dest="folder"
    )
    parser.add_argument("-f", action="store_true")
    args = parser.parse_args()
    synchronizer = MultiTake(args.folder, args.f)
