from argparse import ArgumentParser
from FileManager import FileManager
from MultiTake import MultiTake
from os.path import join

import cv2
import numpy as np

class VideoEditor:

    def __init__(self, base_folder: str, force_recreation=False) -> None:
        self.base_folder = base_folder
        self.file_manager = FileManager(self.base_folder, force_recreation)
        self.file_manager.create_normalized_audiofiles()
        (
            self.sync_audio_path,
            self.sync_video_paths,
        ) = self.file_manager.cut_videos_based_on_offsets()
        self.multitake = MultiTake(self.sync_audio_path, self.sync_video_paths)
        self.video_out_width = 1080
        self.video_out_heigth = 1920
        self.video_out_aspect_ratio = self.video_out_width / self.video_out_heigth

    def create_new_video_with_scene_changes(self, output_path):
        # Cut video clips at scene changes
        cut_video_segments = [self.cut_video_at_scene_changes(video_clip) for video_clip in self.multitake.video_clips]

        # Combine video segments while handling audio synchronization
        combined_frames = []
        audio_frame_idx = 0
        for segments in zip(*cut_video_segments):
            for frame in segments:
                combined_frames.append(frame)
            audio_frame_idx += len(segments)
            #combined_frames[-1][:, :, 0] += self.multitake.audio_clip[audio_frame_idx - 1]

        # Save the final video
        self.save_final_video(output_path, combined_frames, self.multitake.sample_rate)


    def cut_video_at_scene_changes(self, video_capture):
        # Implement your logic here to cut the video at scene changes
        # Return a list of video segments

        # For demonstration purposes, let's split the video into 5 equal-length segments
        duration = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        segment_duration = duration // 5
        video_segments = []

        for i in range(5):
            start_frame = i * segment_duration
            end_frame = (i + 1) * segment_duration
            video_segment = self.extract_frames(video_capture, start_frame, end_frame)
            video_segments.append(video_segment)

        return video_segments

    def extract_frames(self, video_capture, start_frame, end_frame):
        # Extract frames between start_frame and end_frame
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ret, chunk = video_capture.read(end_frame-start_frame)
        return chunk

    def save_final_video(self, output_path, frames, sample_rate):
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'XVID'), sample_rate, (frames[0].shape[1], frames[0].shape[0]))
        for frame in frames:
            out.write(frame)
        out.release()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--folder", action="store", type=str, required=True, dest="folder"
    )
    parser.add_argument("-f", action="store_true")
    args = parser.parse_args()
    video_editor = VideoEditor(args.folder, args.f)
    video_editor.create_new_video_with_scene_changes("test.mp4")