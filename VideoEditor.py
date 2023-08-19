from argparse import ArgumentParser, ArgumentTypeError
from FileManager import FileManager
from MultiTake import MultiTake
from os.path import join
from cv2 import VideoWriter, VideoWriter_fourcc, CAP_PROP_FPS, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, CAP_PROP_POS_FRAMES, resize, destroyAllWindows
OUT_FOLDER = "Out"


class VideoEditor:
    def __init__(
        self,
        base_folder: str,
        start: int = 30,
        video_duration: int = 30,
        take_dur=3.0,
    ) -> None:
        self.base_folder = base_folder
        self.video_duration = video_duration
        self.take_dur = take_dur
        self.file_manager = FileManager(self.base_folder)
        self.file_manager.create_normalized_audiofiles()
        self.file_manager.cut_videos_based_on_offsets(
            start=start, duration=video_duration
        )
        self.file_manager.normalize_sync_videofiles()
        # self.file_manager.add_padding_based_on_offsets(start=start)

        self.multitake = MultiTake(
            self.file_manager.sync_audiopath, self.file_manager.normalized_videopaths
        )
        self.video_out_width = 1080
        self.video_out_heigth = 1920
        self.video_out_aspect_ratio = self.video_out_width / self.video_out_heigth

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.file_manager.remove_tmp_folder_and_contents()

    def calculate_largest_rect(self, max_width, max_height):
        # Calculate the width based on the height and aspect ratio
        width_with_aspect_ratio = int(max_height * self.video_out_aspect_ratio)
        if width_with_aspect_ratio <= max_width:
            # The calculated width is within the allowed max width
            return width_with_aspect_ratio, max_height
        else:
            # The calculated width exceeds the allowed max width
            # Calculate the height based on the width and aspect ratio
            height_with_aspect_ratio = int(max_width / self.video_out_aspect_ratio)
            return max_width, height_with_aspect_ratio

    def create_video(self):
        out_folder = self.file_manager.check_folder_in_path_and_create(OUT_FOLDER, self.base_folder)
        video_tmp_path = join(out_folder, "tmp.mp4")
        # Create an output video writer
        out = VideoWriter(
            video_tmp_path,
            VideoWriter_fourcc(*"mp4v"),
            30,
            (self.video_out_width, self.video_out_heigth),
        )

        idx = 0
        while idx < self.video_duration:
            print("Processing segment", idx)
            video_idx = int(idx // self.take_dur) % len(self.multitake.video_paths)
            cap = self.multitake.get_video_clip(video_idx)
            # get infor from current video in use
            frame_rate = int(cap.get(CAP_PROP_FPS))
            frame_width = int(cap.get(CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(CAP_PROP_FRAME_HEIGHT))
            # Calculate starting frame index for the current segment
            start_frame = int(frame_rate * idx)
            # Set the starting frame
            cap.set(CAP_PROP_POS_FRAMES, start_frame)

            # Extract and write frames for the segment
            for i in range(int(frame_rate * self.take_dur)):
                ret, frame = cap.read()
                if not ret:
                    break
                max_width, max_height = self.calculate_largest_rect(
                    frame_width, frame_height
                )
                crop_frame = frame[0:max_width, 0:max_height]
                resized_frame = resize(
                    frame, (self.video_out_width, self.video_out_heigth)
                )
                out.write(resized_frame)
            cap.release()
            idx += self.take_dur

        # Release output video writer
        out.release()
        destroyAllWindows()
        video_out_path = join(out_folder, "out.mp4")
        self.file_manager.video_audio_to_instavideo(
            self.multitake.audio_path, video_tmp_path, video_out_path
        )


def check_positive(value):
    ivalue = float(value)
    if ivalue < 0:
        raise ArgumentTypeError("Has to be 0 or positive" % value)
    return ivalue


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--folder",
        action="store",
        type=str,
        required=True,
        dest="folder",
        help="Folder containing 'Audio' folder with 1 audio file and 'Videos' folder with N videos",
    )
    parser.add_argument(
        "--start",
        action="store",
        type=check_positive,
        required=False,
        default=30.0,
        dest="start",
        help="Starting second in the reference audio in seconds",
    )
    parser.add_argument(
        "--duration",
        action="store",
        type=check_positive,
        required=False,
        default=30.0,
        dest="duration",
        help="Duration of the resulting video in seconds",
    )
    parser.add_argument(
        "--take_dur",
        action="store",
        type=check_positive,
        required=False,
        default=3.0,
        dest="take_dur",
        help="Take change period in seconds",
    )
    parser.add_argument("--test", action="store_true", help="Test execution won't delete temporary files")

    args = parser.parse_args()
    if args.test:
        video_editor = VideoEditor(
            args.folder, args.start, args.duration, args.take_dur
        )
        video_editor.create_video()
    else:
        with VideoEditor(
            args.folder, args.start, args.duration, args.take_dur
        ) as video_editor:
            video_editor.create_video()
