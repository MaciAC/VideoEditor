import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from os.path import join, exists, isfile
from os import listdir
from math import ceil

from MultiTake import MultiTake


class VideoTrack:
    def __init__(self, canvas, video_path):
        self.canvas = canvas
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_rate = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_refresh_period = 1000 // self.frame_rate if self.frame_rate > 0 else 10
        self.paused = True
        self.current_frame = 0
        self.thumbnail_height = 50
        self.thumbnail_width = 100
        self.thumbnail_cap = cv2.VideoCapture(video_path)
        self.thumbnail_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.thumbnail_width)
        self.thumbnail_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.thumbnail_height)
        self.create_thumbnails()
        self.update()

    def create_thumbnails(self):
        self.thumbnails = []
        canvas_width_in_frames = ceil(self.canvas.winfo_width() / self.thumbnail_width)
        frame_interval = self.total_frames // canvas_width_in_frames
        while len(self.thumbnails) < self.total_frames:
            ret, frame = self.thumbnail_cap.read()
            if ret:
                frame_thumbnail = cv2.resize(frame, (self.thumbnail_width, self.thumbnail_height))
                photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame_thumbnail, cv2.COLOR_BGR2RGB)))
                self.thumbnails.append(photo)
                for _ in range(frame_interval - 1):
                    self.thumbnails.append(photo)
        return self.thumbnails

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        self.update(force=True)

    def update(self, force=False):
        breakpoint()
        if not self.paused and not force:
            self.current_frame = min(self.current_frame, self.total_frames - 1)

            timeline_width = self.canvas.winfo_width()
            timeline_position = self.current_frame * timeline_width // self.total_frames
            self.canvas.delete("timeline")
            self.canvas.create_rectangle(0, self.thumbnail_height, timeline_position, self.thumbnail_height + 5, fill="blue", tags="timeline")

            thumbnail_index = self.current_frame * len(self.thumbnails) // self.total_frames
            thumbnail = self.thumbnails[thumbnail_index]
            self.canvas.delete("thumbnail")
            self.canvas.create_image(0, 0, image=thumbnail, anchor=tk.NW, tags="thumbnail")

        self.canvas.after(self.frame_refresh_period, self.update)




class MultiTrackVideoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Track Video Editor")

        self.track_paths = []
        self.canvas_list = []
        self.playing = False
        self.timeline_slider = None
        self.timeline_position = 0

        self.thumbnail_height = 50
        self.thumbnail_width = 100

        add_track_button = tk.Button(root, text="Create MultiTake", command=self.create_multitake)
        add_track_button.pack()

        self.timeline_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.update_timeline_position)
        self.timeline_slider.pack(fill=tk.X)

        self.play_pause_button = tk.Button(root, text="Play/Pause All", command=self.toggle_play_pause)
        self.play_pause_button.pack()


    def create_multitake(self):
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
        self.multitake = MultiTake(folder_path)
        for video_path in self.multitake.sync_video_paths[:2]:
            canvas = tk.Canvas(self.root, width=self.thumbnail_width, height=self.thumbnail_height)
            canvas.pack()
            video_track = VideoTrack(canvas, video_path)
            self.canvas_list.append(video_track)


    def toggle_play_pause(self):
        self.playing = not self.playing
        play_state = "Pause All" if self.playing else "Play All"
        for video_track in self.canvas_list:
            if self.playing:
                video_track.play()
            else:
                video_track.pause()
        self.play_pause_button.config(text=play_state)


    def update_timeline_position(self, position):
        for video_track in self.canvas_list:
            timeline_position = int(position) * video_track.total_frames // 100
            video_track.set_current_frame(timeline_position)


    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = MultiTrackVideoEditor(root)
    app.run()
