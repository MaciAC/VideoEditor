from argparse import ArgumentParser, ArgumentTypeError
from logging import DEBUG, INFO, basicConfig, error, info
from os.path import join, exists
from os import mkdir
from random import choice

from constants import NORM_FPS, OUT_FOLDER, OUT_HEIGHT, OUT_WIDTH
from cv2 import (
    CAP_PROP_POS_FRAMES,
    VideoWriter,
    VideoWriter_fourcc,
    destroyAllWindows,
    resize,
)
from FileManager import FileManager
from MultiTake import MultiTake


class VideoEditor:
    def __init__(
        self,
        base_folder: str,
        start: int = 30,
        video_duration: int = 30,
    ) -> None:
        self.video_out_fps = int(NORM_FPS)
        self.video_out_width = OUT_WIDTH
        self.video_out_heigth = OUT_HEIGHT
        self.video_out_aspect_ratio = self.video_out_width / self.video_out_heigth

        self.start = start
        self.base_folder = base_folder
        self.video_duration = video_duration
        self.file_manager = FileManager(self.base_folder)
        self.file_manager.create_normalized_audiofiles()
        (
            self.start_offsets,
            self.finish_offsets,
        ) = self.file_manager.cut_videos_based_on_offsets(start=start, duration=video_duration)
        self.file_manager.normalize_sync_videofiles()
        self.multitake = MultiTake(
            self.file_manager.sync_audiopath, self.file_manager.normalized_videopaths
        )

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

    def get_candidate_video_idxs(self, curr_frame, finish_frame):
        idxs = []
        curr_time = curr_frame / self.video_out_fps
        curr_time += self.start
        audio_total_duration = self.file_manager.audio_duration
        for idx, (start_offset, finish_offset) in enumerate(
            zip(self.start_offsets, self.finish_offsets)
        ):
            if (
                curr_time + start_offset >= 0.0
                and audio_total_duration - finish_offset - curr_time + finish_frame >= 0.0
            ):
                idxs.append(idx)
        return idxs

    def get_candidate_change_frames(self):
        return self.multitake.audio_beats

    def create_video(self):
        out_folder = join(self.file_manager.base_folder, OUT_FOLDER)
        if not exists(out_folder):
            mkdir(out_folder)
        video_tmp_path = join(self.file_manager.temp_folder, "tmp.mp4")
        # Create an output video writer
        out = VideoWriter(
            video_tmp_path,
            VideoWriter_fourcc(*"mp4v"),
            30,
            (self.video_out_width, self.video_out_heigth),
        )
        change_frames = self.get_candidate_change_frames()
        cap = None
        for frame_idx in range(int(self.video_out_fps * self.video_duration)):
            if not cap or frame_idx in change_frames:
                if cap:
                    cap.release()
                info(f"Processing segment {frame_idx}")
                candidate_idxs = self.get_candidate_video_idxs(frame_idx, frame_idx + 10)
                info(candidate_idxs)
                video_idx = choice(candidate_idxs)
                cap = self.multitake.get_video_clip(video_idx)
                (
                    frame_width,
                    frame_height,
                    frame_rate,
                ) = self.multitake.get_video_metadata(video_idx)
                start_offset = self.start_offsets[video_idx]
                start_offset_corrected = (
                    start_offset
                    if (start_offset < 0.0 and -start_offset > self.start)
                    else 0.0
                )
                # compute starting frame index for the current segment based on start_offset
                start_frame = int(frame_rate * start_offset_corrected + frame_idx)
                # Set the starting frame
                info(f"start frame {start_frame}")
                cap.set(CAP_PROP_POS_FRAMES, start_frame)

            # Extract and write frames for the segment
            ret, frame = cap.read()
            if not ret:
                error(f"Frame idx {frame_idx} not read for video {video_idx}")
                continue
            max_width, max_height = self.calculate_largest_rect(frame_width, frame_height)
            crop_frame = frame[0:max_height, 0:max_width]
            resized_frame = resize(crop_frame, (self.video_out_width, self.video_out_heigth))
            out.write(resized_frame)
        # Release output video writer
        out.release()
        destroyAllWindows()
        final_video_out_path = join(out_folder, "out.mp4")
        self.file_manager.video_audio_to_instavideo(
            self.multitake.audio_path, video_tmp_path, final_video_out_path
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
        "--test",
        "-t",
        dest="test",
        action="store_true",
        help="Test execution won't delete temporary files",
    )
    parser.add_argument(
        "--debug",
        "-d",
        dest="debug",
        action="store_true",
        help="Show debug messages and ffmpeg commands",
    )
    args = parser.parse_args()
    logging_format = "[%(asctime)s] %(filename)s:%(lineno)d\t%(levelname)s - %(message)s"
    if args.debug:
        basicConfig(
            level=DEBUG,
            format=logging_format,
        )
    else:
        basicConfig(
            level=INFO,
            format=logging_format,
        )
    if args.test:
        video_editor = VideoEditor(args.folder, args.start, args.duration)
        video_editor.create_video()
    else:
        with VideoEditor(args.folder, args.start, args.duration) as video_editor:
            video_editor.create_video()
