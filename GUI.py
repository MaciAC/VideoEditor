import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from os.path import join, exists, isfile
from os import listdir
from math import ceil
from time import sleep

from MultiTake import MultiTake


class VideoTrack:
    def __init__(self, canvas, video_path):
        self.canvas = canvas
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_rate = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_refresh_period = (
            1000 // self.frame_rate if self.frame_rate > 0 else 10
        )
        self.paused = True
        self.current_frame = 0
        self.thumbnail_height = 50
        self.thumbnail_width = 100
        self.thumbnail_cap = cv2.VideoCapture(video_path)
        self.thumbnail_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.thumbnail_width)
        self.thumbnail_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.thumbnail_height)
        self.window_width = self.canvas.winfo_width()
        self.widow_width_changed_n_times = 0
        self.num_thumbnails = ceil(self.canvas.winfo_width() / self.thumbnail_width)
        self.create_thumbnail()
        self.update()


    def create_thumbnail(self):
        thumbnails = []
        frame_indices = [
            int(self.total_frames * fraction)
            for fraction in [i / self.num_thumbnails for i in range(self.num_thumbnails)]
        ]

        for frame_index in frame_indices:
            self.thumbnail_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = self.thumbnail_cap.read()
            if ret:
                frame_thumbnail = cv2.resize(
                    frame, (self.thumbnail_width, self.thumbnail_height)
                )
                thumbnails.append(frame_thumbnail)

        concatenated_thumbnails = cv2.hconcat(thumbnails)
        self.thumbnail = ImageTk.PhotoImage(
            image=Image.fromarray(
                cv2.cvtColor(concatenated_thumbnails, cv2.COLOR_BGR2RGB)
            )
        )

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        self.update()

    def update(self):
        if self.window_width != self.canvas.winfo_width():
            if self.widow_width_changed_n_times > 100:
                self.window_width = self.canvas.winfo_width()
                self.num_thumbnails = ceil(self.canvas.winfo_width() / self.thumbnail_width)
                self.create_thumbnail()
                self.widow_width_changed_n_times = 0
            else:
                self.widow_width_changed_n_times += 1
        else:
            self.widow_width_changed_n_times = 0

        self.current_frame = min(self.current_frame, self.total_frames - 1)

        timeline_width = self.canvas.winfo_width()
        timeline_position = self.current_frame * timeline_width // self.total_frames
        self.canvas.delete("timeline")
        self.canvas.create_rectangle(
            0,
            self.thumbnail_height,
            timeline_position,
            self.thumbnail_height + 5,
            fill="blue",
            tags="timeline",
        )
        self.canvas.delete("thumbnail")
        self.canvas.create_image(
            0, 0, image=self.thumbnail, anchor=tk.NW, tags="thumbnail"
        )

        self.canvas.after(self.frame_refresh_period, self.update)


class VideoViewer:
    def __init__(self, canvas, video_path):
        self.canvas = canvas
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_refresh_period = 10  # Adjust as needed
        self.paused = True
        self.current_frame = 0
        self.width = canvas.winfo_width()
        self.height = canvas.winfo_height()

    def play(self):
        self.paused = False
        self.update()

    def pause(self):
        self.paused = True

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index

    def update(self):
        if not self.paused:
            self.current_frame = min(self.current_frame, self.total_frames - 1)

            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (self.width, self.height))
                photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                self.canvas.delete("video_frame")
                self.canvas.create_image(0, 0, image=photo, anchor=tk.NW, tags="video_frame")
                self.canvas.photo = photo  # Prevent PhotoImage from being garbage collected

        self.canvas.after(self.frame_refresh_period, self.update)


class MultiTrackVideoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Track Video Editor")

        self.track_paths = []
        self.canvas_list = []
        self.playing = False
        self.timeline_position = 0

        self.thumbnail_height = 50
        self.thumbnail_width = 100

        self.viewer_height = 200
        self.viewer_width = 400

        add_track_button = tk.Button(
            root, text="Create MultiTake", command=self.create_multitake
        )
        add_track_button.pack()


        self.play_pause_button = tk.Button(
            root, text="Play/Pause All", command=self.toggle_play_pause
        )
        self.play_pause_button.pack()

        # Create a canvas for video view
        self.video_view_canvas = tk.Canvas(root, width=self.viewer_width, height=self.viewer_height)
        self.video_view_canvas.pack()


        self.root.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        new_width = event.width
        for video_track in self.canvas_list:
            video_track.canvas.config(width=new_width)


    def create_multitake(self):
        """
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            audio_folder = join(folder_path, "Audio")
            videos_folder = join(folder_path, "Videos")

            if not exists(audio_folder) or not exists(videos_folder):
                messagebox.showerror("Error", "Both 'Audio' and 'Videos' folders are required in the selected folder.")
                return

            audio_files = [f for f in listdir(audio_folder) if isfile(join(audio_folder, f))]
            video_files = [f for f in listdir(videos_folder) if isfile(join(videos_folder, f))]
            # TODO: check mime-types
            if len(audio_files) != 1:
                messagebox.showerror("Error", "Exactly 1 audio file is required in the 'Audio' folder.")
                return
            if len(video_files) < 2:
                messagebox.showerror("Error", "At least 2 video files are required in the 'Videos' folder.")
                return
        """
        folder_path = "/Users/maciaac/Documents/moodmurri/videos/Iwish"
        self.multitake = MultiTake(folder_path)
        window_width = self.root.winfo_width()
        for video_path in self.multitake.sync_video_paths[:2]:
            canvas = tk.Canvas(
                self.root, width=window_width, height=self.thumbnail_height
            )
            canvas.pack()
            video_track = VideoTrack(canvas, video_path)
            self.canvas_list.append(video_track)

        # Create a VideoViewer instance for the selected video
        self.video_viewer = VideoViewer(self.video_view_canvas, self.multitake.sync_video_paths[0])
        self.video_viewer.play()
        # Add a slider to control the frame shown in the video viewer
        self.frame_slider = tk.Scale(root, from_=0, to=self.video_viewer.total_frames - 1, orient=tk.HORIZONTAL, command=self.update_video_view)
        self.frame_slider.pack()

    def toggle_play_pause(self):
        self.playing = not self.playing
        play_state = "Pause All" if self.playing else "Play All"
        if self.playing:
            self.video_viewer.pause()
        else:
            self.video_viewer.play()
        self.play_pause_button.config(text=play_state)

    def update_timeline_position(self, position):
        for video_track in self.canvas_list:
            timeline_position = int(position) * video_track.total_frames // 100
            video_track.set_current_frame(timeline_position)


    def update_video_view(self, selected_video):
        # Clear previous contents of the video view canvas
        self.video_view_canvas.delete("all")

        # Load the selected video
        video_track = VideoTrack(self.video_view_canvas, selected_video)
        video_track.play()


    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = MultiTrackVideoEditor(root)
    app.run()
