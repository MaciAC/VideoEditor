from argparse import ArgumentParser
from FileManager import FileManager
from MultiTake import MultiTake

import cv2


class VideoEditor:
    def __init__(self, base_folder: str, force_recreation=False) -> None:
        self.base_folder = base_folder
        self.file_manager = FileManager(self.base_folder, force_recreation)
        self.file_manager.create_normalized_audiofiles()
        self.file_manager.cut_videos_based_on_offsets(duration=10)
        self.file_manager.normalize_sync_videofiles()

        self.multitake = MultiTake(
            self.file_manager.sync_audiopath, self.file_manager.normalized_videopaths
        )
        self.video_out_width = 1080
        self.video_out_heigth = 1920
        self.video_out_aspect_ratio = self.video_out_width / self.video_out_heigth

    def create_video(self):
        # Duration of each segment in seconds
        segment_duration = 5

        # Output video dimensions
        output_width = 1080  # You can adjust this based on your preferences
        output_height = 1920  # Assuming each segment height is 1080 pixels

        # Create an output video writer
        out = cv2.VideoWriter(
            "vertical_output.mp4",
            cv2.VideoWriter_fourcc(*"mp4v"),
            30,
            (output_width, output_height),
        )
        # Loop through input videos
        idx = 0
        while idx < 50:
            print(idx)
            print((idx // segment_duration) % len(self.multitake.video_clips))
            cap = self.multitake.video_clips[
                (idx // segment_duration) % len(self.multitake.video_clips)
            ]
            frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
            print(frame_rate)
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Extract frames for the specified duration
            num_frames = int(frame_rate * segment_duration)
            curr_frame = int(frame_rate * idx)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx - 1)
            for _ in range(num_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                resized_frame = cv2.resize(frame, (output_width, output_height))
                out.write(resized_frame)
            cap.release()
            idx += segment_duration
        # Release output video writer
        out.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--folder", action="store", type=str, required=True, dest="folder"
    )
    parser.add_argument("-f", action="store_true")
    args = parser.parse_args()
    video_editor = VideoEditor(args.folder, args.f)
    video_editor.create_video()
