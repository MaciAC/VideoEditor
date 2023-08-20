# VideoEditor

Project to develop a automatic multitake video editor. Based on the [MultiCam entity](https://support.apple.com/guide/final-cut-pro/ver23c764f1/mac) from Apple's Final Cut Pro X video editor, I liked the synch video using audio functionality which is implemented in the Synchronizer.

## Installation

I use [poetry](https://python-poetry.org/) to manage envs:
```bash
git clone git@github.com:MaciAC/VideoEditor.git
cd VideoEditor
poetry install
```
If you don't want to use poetry, install requirements.txt


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
- Allow to use an extra folder with gifs...


## License

[MIT](https://choosealicense.com/licenses/mit/)
