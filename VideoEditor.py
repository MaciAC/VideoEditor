from argparse import ArgumentParser
from FileManager import FileManager
from MultiTake import MultiTake

from os.path import join
import cv2

OUT_FOLDER = 'Out'

class VideoEditor:
    def __init__(self, base_folder: str, force_recreation=False, video_duration:int=30) -> None:
        self.base_folder = base_folder
        self.video_duration = video_duration
        self.file_manager = FileManager(self.base_folder, force_recreation)
        self.file_manager.create_normalized_audiofiles()
        self.file_manager.cut_videos_based_on_offsets(duration=video_duration)
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
        output_width = 1080
        output_height = 1920

        out_folder = self.file_manager.check_in_basefolder_and_create(OUT_FOLDER)
        video_tmp_path = join(out_folder, "tmp.mp4")
        # Create an output video writer
        out = cv2.VideoWriter(
            video_tmp_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            30,
            (output_width, output_height),
        )

        idx = 0
        while idx < self.video_duration:
            print("Processing segment", idx)
            video_idx = (idx // segment_duration) % len(self.multitake.video_paths)
            cap = self.multitake.get_video_clip(video_idx)
            frame_rate = int(cap.get(cv2.CAP_PROP_FPS))

            # Calculate starting frame index for the current segment
            start_frame = int(frame_rate * idx)
            # Set the starting frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # Extract and write frames for the segment
            for i in range(frame_rate * segment_duration):
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
        video_out_path = join(out_folder, 'out.mp4')
        self.file_manager.video_audio_to_instavideo(self.multitake.audio_path, video_tmp_path, video_out_path)



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--folder", action="store", type=str, required=True, dest="folder",
        help="Folder containing 'Audio' folder with 1 audio file and 'Videos' folder with N videos"
    )
    parser.add_argument("-f", action="store_true", help="Force files recreation")
    parser.add_argument(
        "--duration", action="store", type=int, required=False, default=30, dest="duration",
        help="Duration of the resulting video"
    )

    args = parser.parse_args()
    video_editor = VideoEditor(args.folder, args.f, args.duration)
    video_editor.create_video(30)
