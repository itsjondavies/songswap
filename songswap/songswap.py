from __future__ import annotations

import logging
import os
import sys
from enum import Enum

import librosa
import moviepy.editor as mpe
import pydub
import pytube
from moviepy.video.fx.multiply_speed import multiply_speed

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

_TEMPO_TOL = 0.15

class FileExtension(Enum):
    WAV = 1
    MP3 = 2
    MP4 = 3

    @staticmethod
    def from_filepath(filepath: str):
        file_split = filepath.split(".")
        file_ext = f".{file_split[-1]}"
        if ".mp4" == file_ext:
            return FileExtension.MP4
        elif ".mp3" == file_ext:
            return FileExtension.MP3
        elif ".wav" == file_ext:
            return FileExtension.WAV
        else:
            raise ValueError(f"Cannot infer file extension from: {file_ext}")

def download_video(
        url: str,
        output_dir: str,
        audio_only: bool=False
) -> pytube.YouTube:
    """
    Download a video from YouTube using the pytube package.

    Parameters
    ----------
    url : string
        The url of the YouTube video to download.
    output_dir : string
        The local file directory (not full path) where the video should be downloaded to.
    audio_only : bool
        Whether to download the video and audio, or audio only.

    Returns
    -------
    video : pytube.YouTube
        The pytube YouTube object for the YouTube video.
    download_path : str
        The local file path where the video has been downloaded to.

    Raises
    ------
    ValueError
        If cannot load pytube.YouTube object from given URL

    References
    ----------
    .. [1] pytube docs - https://pytube.io/en/latest/

    Examples
    --------
    >>> vid, filepath = download_video(
    >>>    url="https://www.youtube.com/watch?v=xmr8bEuyQjA",
    >>>    output_path=out_path,
    >>>    audio_only=True
    >>> )

    """
    try:
        video = pytube.YouTube(url=url)
    except Exception as e:
        raise ValueError("Could not load pytube.YouTube object from url") from e

    if audio_only:
        best_stream = video.streams.get_audio_only()
    else:
        streams = (
            video.streams
            .filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
        )
        best_stream = streams.first()

    download_path = best_stream.download(
        output_path=output_dir
    ).replace("\\","/")
    logger.info(f"Downloaded {video.title} to {download_path}.")
    return video, download_path

class WAVFile:
    def __init__(self, filepath: str) -> None:
        # get filepath info attributes
        self.filepath = filepath
        self.file_extension = FileExtension.from_filepath(filepath)
        self.filepath_root = ".".join(filepath.split(".")[:-1])
        self.filename = self.filepath_root.split("/")[-1]
        self._set_librosa_attributes()
        self.mpe_clip = mpe.AudioFileClip(self.filepath)

    @classmethod
    def from_any_file(cls, filepath: str, wav_filepath: str=None):
        file_extension = FileExtension.from_filepath(filepath)
        if file_extension is FileExtension.MP4:
            audio = pydub.AudioSegment.from_file(filepath, "mp4")
        elif file_extension is FileExtension.MP3:
            audio = pydub.AudioSegment.from_mp3(filepath)
        elif file_extension is FileExtension.WAV:
            if wav_filepath:
                audio = pydub.AudioSegment.from_wav(filepath)
            else:
                return cls(filepath)

        if not wav_filepath:
            wav_filepath = f"{'.'.join(filepath.split('.')[:-1])}.wav"
        audio.export(wav_filepath, format="wav")
        return cls(wav_filepath)

    def _set_librosa_attributes(self) -> None:
        audio_array, sampling_rate = librosa.load(self.filepath)
        self.tempo, self.beats = librosa.beat.beat_track(
            y=audio_array,
            sr=sampling_rate
        )
        self.duration = librosa.get_duration(y=audio_array, sr=sampling_rate)

    def compare_tempo(self, wav_file: WAVFile):
        tempo_diff = abs(self.tempo - wav_file.tempo) / self.tempo
        return tempo_diff

    def get_mean_tempo(self, wav_file: WAVFile):
        goal_tempo = (self.tempo + wav_file.tempo) / 2
        self_tempo_multi = goal_tempo / self.tempo
        comp_tempo_multi = goal_tempo / wav_file.tempo
        return goal_tempo, self_tempo_multi, comp_tempo_multi

    def change_tempo(self, tempo_multiplier: float) -> WAVFile:
        out_path = f"{self.filepath_root}_newtempo.wav"
        new_clip = self.mpe_clip.time_transform(
            lambda t: tempo_multiplier * t,
            apply_to=["audio"]
        )
        # make new clip with different name to avoid garbage collection closing connection
        # not sure why this happens with time transform function only
        # also not sure why this only happens with audio and not video
        new_clip2 = new_clip.with_duration(self.mpe_clip.duration / tempo_multiplier)
        new_clip2.write_audiofile(out_path)
        return WAVFile(out_path)

    def create_subclip(self, start_time, end_time) -> WAVFile:
        out_path = f"{self.filepath_root}_subclip.wav"
        new_mpe_clip = self.mpe_clip.subclip(start_time=start_time, end_time=end_time)
        new_mpe_clip.write_audiofile(out_path)
        return WAVFile(out_path)

    def close(self):
        self.mpe_clip.close()

    def delete(self):
        self.close()
        os.remove(self.filepath)

def clean_up_files(filepaths: list) -> None:
    for filepath in filepaths:
        os.remove(filepath)


def swap_songs(
        project_name: str,
        video_url: str,
        audio_url: str
) -> None:
    # set project filepaths
    project_dir = f"songswap_outputs/{project_name}"
    # alt_base_video_path = f"{project_dir}/alt_base_video.mp4"
    final_video_path = f"{project_dir}/{project_name}.mp4"
    # download base video
    _, base_video_path = download_video(video_url, project_dir)
    # download audio from new video
    _, new_audio_path = download_video(
        audio_url,
        project_dir,
        audio_only=True
    )
    # convert audio to WAV - make future work easier
    logger.info("Converting files to WAV format.")
    base_wav = WAVFile.from_any_file(base_video_path)
    new_wav = WAVFile.from_any_file(new_audio_path)
    logger.info("Checking tempo...")
    tempo_diff = base_wav.compare_tempo(new_wav)
    if tempo_diff > _TEMPO_TOL:
        raise ValueError(
            f"Tempo difference of {tempo_diff:.2f} is greater than"
            f"allowed value of {_TEMPO_TOL}."
        )
    else:
        logger.info("SUCCESS! Tempo's are compatible.")

    # change tempos of clips
    _, base_tempo_multi, new_tempo_multi = base_wav.get_mean_tempo(
        wav_file=new_wav
    )
    base_mpe = mpe.VideoFileClip(base_video_path, audio=False)
    base_new_tempo = multiply_speed(base_mpe, base_tempo_multi)

    base_wav_new_tempo = base_wav.change_tempo(base_tempo_multi)
    new_wav_new_tempo = new_wav.change_tempo(new_tempo_multi)
    # verify changed tempos
    logger.info(
        f"Altered '{base_wav_new_tempo.filename}' tempo: {base_wav_new_tempo.tempo:.2f}"
    )
    logger.info(
        f"Altered '{new_wav_new_tempo.filename}' tempo: {new_wav_new_tempo.tempo:.2f}"
    )

    # work out final audio/video clippings
    new_start = new_wav_new_tempo.beats[1] - base_wav_new_tempo.beats[0]
    new_audio_duration = new_wav_new_tempo.duration - new_start
    final_duration = min(base_wav_new_tempo.duration, new_audio_duration)
    final_wav = new_wav_new_tempo.create_subclip(
        start_time=new_start,
        end_time=new_start+final_duration
    )

    # stitch audio and video together
    final_video_mpe = base_new_tempo.with_end(final_wav.duration)
    final_video_mpe = final_video_mpe.with_audio(final_wav.mpe_clip)
    final_video_mpe.write_videofile(final_video_path, audio_codec="aac")

    # close all readers and cleanup
    base_wav.delete()
    new_wav.delete()
    base_wav_new_tempo.delete()
    new_wav_new_tempo.delete()
    final_wav.delete()
    base_mpe.close()
    base_new_tempo.close()
    final_video_mpe.close()
    clean_up_files([
        base_video_path,
        new_audio_path,
    ])
