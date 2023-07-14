# songswap
Python package to swap out the audio on a YouTube video with another song.

## Getting Started

Install directly from this repo as follows:

```
pip install git+https://github.com/itsjondavies/songswap
```

NOTE: Cannot currently upload to PyPi as using GitHub projects as dependencies. In future, can revert to PyPi
dependencies when dependency package issues have been fixed.

NOTE: You will also need to [install ffmpeg](https://adamtheautomator.com/install-ffmpeg/) for the package to work.

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
* Allow a user to specify a subclip on the base video
* Allow a user to specify a subclip on the new audio video
* Test if works for Python 3.7 & 3.8 and other OS to Windows
* Implement pychorus chorus detection so users can option to auto-detect the chorus
* Implement FastAPI to serve function as API

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
