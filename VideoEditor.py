from argparse import ArgumentParser
from FileManager import FileManager
from MultiTake import MultiTake
from moviepy.editor import concatenate_videoclips, AudioClip
from os.path import join

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
        self.create_new_video_with_change(join(self.base_folder, 'test.mp4'))

    def create_new_video_with_change(self, output_path):
        combined_clips = []
        start_time = 0
        end_time = 20
        curr_time = start_time
        vid_idx = 0
        step=5
        while curr_time < end_time:
            video_clip = self.multitake.video_clips[vid_idx]
            video_part = video_clip.subclip(curr_time, curr_time + step)
            combined_clips.append(video_part.crossfadein(1))  # Add crossfade for smooth transition
            curr_time += step

        combined_video = concatenate_videoclips(combined_clips)
        audio_clip = AudioClip(make_frame=self.multitake.audio_clip.to_soundarray, duration=self.multitake.audio_clip.duration)
        final_video = combined_video.set_audio(audio_clip)
        final_video.write_videofile(output_path, codec="libx264")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--folder", action="store", type=str, required=True, dest="folder"
    )
    parser.add_argument("-f", action="store_true")
    args = parser.parse_args()
    synchronizer = VideoEditor(args.folder, args.f)