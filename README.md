# VideoEditor

Project to develop a automatic multitake video editor. Based on the [MultiCam entity](https://support.apple.com/guide/final-cut-pro/ver23c764f1/mac) from Apple's Final Cut Pro X video editor, I liked the synch video using audio functionality which is implemented in the Synchronizer.

TODOS:
- ✅Create new vertical video by changing takes among the multitake synched videos.
- ✅ Use multiprocessing in FileManager.
- Refactor to Sync videos shorter than audio reference:
    - extra variable per video with the seconds where the video is present, or...
    - pad videos with black frames at begin and end
- Use Object detection to choose vertical subtakes from videos.
- Video effects/transitions
- Allow to use an extra folder with gifs...
- 🚧 Allow to execute command with various parameters.
- Change takes at the rythm of the music.
- Use logging
