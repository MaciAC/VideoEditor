# VideoEditor

Project to develop a automatic multitake video editor. Based on the [MultiCam entity](https://support.apple.com/guide/final-cut-pro/ver23c764f1/mac) from Apple's Final Cut Pro X video editor, I liked the synch video using audio functionality which is implemented in the Synchronizer.


## Installation
File transcoding and some file edition is done with ffmpeg, these commands are executed with xargs so you will need a Unix based OS.

[Install ffmpeg](https://ffmpeg.org/download.html)

I use [poetry](https://python-poetry.org/) to manage envs:
```
git clone git@github.com:MaciAC/VideoEditor.git
cd VideoEditor
poetry install
```
If you don't want to use poetry, install requirements.txt
```
git clone git@github.com:MaciAC/VideoEditor.git
cd VideoEditor
pip install -r requirements.txt
```

## Execution
The code assume you have a folder with this structure, videos must have an audio stream, it is used to synchronize:
```
    base_folder
     ├── Audio
     │   └── audio.mp3
     └── Videos
         └── video1.mp4
         └── video2.avi
         ...
         └── videoN.mov
```
You can use any video and audio encoding supported by the ffmpeg version you have installed, check it running this:
```
ffmpeg -formats
ffmpeg -codecs
```
### Usage
```
usage: VideoEditor.py [-h] --folder FOLDER [--start START] [--duration DURATION] [--test] [--debug]

options:
  -h, --help           show this help message and exit
  --folder FOLDER      Folder containing 'Audio' folder with 1 audio file and 'Videos' folder with N videos
  --start START        Starting second in the reference audio in seconds
  --duration DURATION  Duration of the resulting video in seconds
  --test, -t           Test execution won't delete temporary files
  --debug, -d          Show debug messages and ffmpeg commands
```

### Pipeline
![Screenshot](https://user-images.githubusercontent.com/25790382/263524482-a5715a9b-1b51-4ce9-8a0f-7595ac469e61.png)
## Roadmap

- ✅ Create new vertical video by changing takes among the multitake synched videos.
- ✅ Use multiprocessing in FileManager.
- ✅ Change takes at the rythm of the music.
- ✅ Crop frames
- ✅ Use logging
- ✅ Use poetry
- 🚧 Allow to execute command with various parameters.
    - Write usage section in README
- Use Object detection to choose vertical subtakes from videos.
- Video effects/transitions
- Dockerize
- Allow to use an extra folder with gifs...


## License

[MIT](https://choosealicense.com/licenses/mit/)
