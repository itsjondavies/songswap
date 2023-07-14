import os

from songswap.songswap import WAVFile


def test_convert_from_mp4():
    wav = WAVFile.from_any_file(
        "tests/data/test_audio.mp4",
        "tests/outputs/test_convert_from_mp4.wav"
    )
    assert ".wav" in wav.filepath
    assert os.path.isfile(wav.filepath)
    wav.delete()

def test_change_tempo():
    wav = WAVFile.from_any_file(
        "tests/data/test_audio.wav",
        "tests/outputs/test_audio.wav"
    )
    new_wav = wav.change_tempo(tempo_multiplier=1.2)
    wav.delete()
    new_wav.delete()
