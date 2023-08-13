import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk

import numpy as np

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
        self.thumbnails = []
        self.update()

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def update(self):
        if not self.paused:
            self.current_frame += 1
            if self.current_frame >= self.total_frames:
                self.current_frame = 0

            ret, frame = self.cap.read()
            if ret:
                frame_thumbnail = cv2.resize(frame, (self.thumbnail_width, self.thumbnail_height))
                photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame_thumbnail, cv2.COLOR_BGR2RGB)))
                self.thumbnails.append(photo)
                if len(self.thumbnails) > self.canvas.winfo_width() // self.thumbnail_width:
                    self.thumbnails.pop(0)

                self.canvas.delete("thumbnail")
                x_position = 0
                for thumbnail in self.thumbnails:
                    self.canvas.create_image(x_position, 0, image=thumbnail, anchor=tk.NW, tags="thumbnail")
                    x_position += self.thumbnail_width

            timeline_width = self.canvas.winfo_width()
            timeline_position = self.current_frame * timeline_width // self.total_frames
            self.canvas.delete("timeline")
            self.canvas.create_rectangle(0, self.thumbnail_height, timeline_position, self.thumbnail_height + 5, fill="blue", tags="timeline")

        self.canvas.after(self.frame_refresh_period, self.update)



class MultiTrackVideoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Track Video Editor")

        self.track_paths = []  # List to store video track paths
        self.canvas_list = []

        add_track_button = tk.Button(root, text="Add Video Track", command=self.add_video_track)
        add_track_button.pack()


    def add_video_track(self):
        video_path = filedialog.askopenfilename(title="Select Video Track", filetypes=[("Video files", "*.mp4 *.avi")])
        if video_path:
            self.track_paths.append(video_path)

            canvas = tk.Canvas(self.root)
            canvas.pack()
            video_track = VideoTrack(canvas, video_path)
            self.canvas_list.append(video_track)

            play_button = tk.Button(self.root, text=f"Play Track {len(self.track_paths)}", command=video_track.play)
            play_button.pack()

            pause_button = tk.Button(self.root, text=f"Pause Track {len(self.track_paths)}", command=video_track.pause)
            pause_button.pack()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiTrackVideoEditor(root)
    app.run()
