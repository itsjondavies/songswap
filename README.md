# songswap
Python package to swap out the audio on a YouTube video with another song.

## Getting Started

Cannot currently upload to PyPi as using GitHub projects as dependencies. In future, can revert to PyPi
dependencies when dependency package issues have been fixed. For now can install directly 
from this repo as follows:

```
pip install git+https://github.com/itsjondavies/songswap
```

NOTE: You will also need to install ffmpeg for the package to work

### Running a songswap process

You can easily run a songswap process as follows:

```
from songswap import swap_songs

swap_songs(
    project_name="project_name",
    video_url="youtube_url_for_base_video",
    audio_url="youtube_url_for_new_audio"
)
```

## Required Improvements
* Allow upload to PyPi
* Needs to work for more file formats than .mp3 and .mp4
* Allow a user to specify a subclip on the base video
* Allow a user to specify a subclip on the new audio video
* Test if works for Python 3.7 & 3.8
* Implement pychorus chorus detection so users can option to auto-detect the chorus
* Edit the moviepy package so that it can load librosa beat detection automatically
* Switch the speed alteration to moviepy instead of ffmpeg for speed gain
* In general, make more user friendly
* Suppress moviepy warning about using alternate soundfile
* Improve logging in general - unify all package prints to stdout in more formalised manner
* Implement FastAPI to serve function as API

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
