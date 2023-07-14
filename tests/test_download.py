import os

from songswap.songswap import download_video


def test_download_video():
    output_dir = "tests/outputs"
    _, out_file = download_video(
        url="https://www.youtube.com/watch?v=WpmILPAcRQo",
        output_dir=output_dir,
        audio_only=False
    )
    assert os.path.isfile(out_file)
    os.remove(out_file)


def test_download_audio():
    output_dir = "tests/outputs"
    _, out_file = download_video(
        url="https://www.youtube.com/watch?v=xmr8bEuyQjA",
        output_dir=output_dir,
        audio_only=True
    )
    assert os.path.isfile(out_file)
    os.remove(out_file)
