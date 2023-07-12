import os

from songswap.songswap import download_video


def test_download_video():
    out_path = "tests/data/test_video.mp4"
    download_video(
        url="https://www.youtube.com/watch?v=WpmILPAcRQo",
        output_path="tests/data/test_video.mp4",
        audio_only=False
    )
    assert os.path.isfile(out_path)
    os.remove(out_path)


def test_download_audio():
    out_path = "tests/data/test_audio.mp3"
    download_video(
        url="https://www.youtube.com/watch?v=WpmILPAcRQo",
        output_path="tests/data/test_audio.mp3",
        audio_only=True
    )
    assert os.path.isfile(out_path)
    os.remove(out_path)
