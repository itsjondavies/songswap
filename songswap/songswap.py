import logging
import os
import sys

import ffmpy
import librosa
import moviepy.editor as mpe
import pytube

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def download_video(
        url: str,
        output_path: str,
        audio_only: bool=False
) -> pytube.YouTube:
    video = pytube.YouTube(url=url)
    if audio_only:
        streams = video.streams.filter(only_audio=True)
    else:
        streams = (
            video.streams
            .filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
        )
    best_stream = streams.first()
    path_components = output_path.split("/")
    filename = path_components[-1]
    path = "/".join(path_components[:-1])
    best_stream.download(
        output_path=path,
        filename=filename
    )
    logging.info(f"Downloaded {video.title} to {output_path}/{filename}.")
    return video

def swap_songs(
        project_name: str,
        video_url: str,
        audio_url: str
) -> None:
    # set project filepaths
    project_dir = f"songswap_outputs/{project_name}"
    base_video_path = f"{project_dir}/base_video.mp4"
    new_audio_path = f"{project_dir}/new_audio.mp3"
    alt_base_video_path = f"{project_dir}/alt_base_video.mp4"
    alt_new_audio_path = f"{project_dir}/alt_new_audio.mp3"
    final_audio_path = f"{project_dir}/final_audio.wav"
    final_video_path = f"{project_dir}/{project_name}.mp4"
    # download base video
    base_yt = download_video(video_url, base_video_path)
    # download audio from new video
    new_yt = download_video(audio_url, new_audio_path, audio_only=True)
    # check the tempos are compatible
    old_audio_clip = AudioClip(base_video_path, base_yt.title)
    new_audio_clip = AudioClip(new_audio_path, new_yt.title)
    check_tempo_match(old_audio_clip, new_audio_clip)
    # change tempos of clips
    goal_tempo = (old_audio_clip.tempo + new_audio_clip.tempo) / 2
    new_vid_tempo_multi = goal_tempo / old_audio_clip.tempo
    new_audio_tempo_multi = goal_tempo / new_audio_clip.tempo
    alter_media_speed(
        input_path=base_video_path,
        output_path=alt_base_video_path,
        tempo_multi=new_vid_tempo_multi,
        is_audio=False
    )
    alter_media_speed(
        input_path=new_audio_path,
        output_path=alt_new_audio_path,
        tempo_multi=new_audio_tempo_multi,
        is_audio=True
    )
    # verify changed tempos
    alt_old_audio = AudioClip(alt_base_video_path, base_yt.title)
    alt_new_audio = AudioClip(alt_new_audio_path, new_yt.title)
    logging.info(
        f"Altered '{alt_old_audio.name}' tempo: {alt_old_audio.tempo}"
    )
    logging.info(
        f"Altered '{alt_new_audio.name}' tempo: {alt_new_audio.tempo}"
    )

    # work out final audio/video clippings
    alt_old_audio_mpe = alt_old_audio.get_mpe_object()
    alt_new_audio_mpe = alt_new_audio.get_mpe_object()
    new_start = alt_new_audio.beats[1] - alt_old_audio.beats[0]
    new_audio_duration = alt_new_audio_mpe.duration - new_start

    final_duration = min(alt_old_audio_mpe.duration, new_audio_duration)
    final_audio = alt_new_audio_mpe.subclip(
        start_time=new_start,
        end_time=new_start+final_duration
    )
    final_audio.write_audiofile(final_audio_path)

    # stitch audio and video together
    final_video_mpe = mpe.VideoFileClip(alt_base_video_path, audio=False)
    final_video_mpe = final_video_mpe.with_end(final_audio.duration)
    final_video_mpe = final_video_mpe.with_audio(final_audio)
    final_video_mpe.write_videofile(final_video_path, audio_codec="aac")

    # close all readers and cleanup
    alt_new_audio_mpe.close()
    alt_old_audio_mpe.close()
    final_audio.close()
    final_video_mpe.close()
    clean_up_files([
        base_video_path,
        new_audio_path,
        alt_base_video_path,
        alt_new_audio_path,
        final_audio_path,
    ])


class AudioClip:
    def __init__(self, file: str, name: str) -> None:
        self.filepath = file
        self.name = name
        self.audio_array, self.sampling_rate = librosa.load(file)
        self.tempo, self.beats = librosa.beat.beat_track(
            y=self.audio_array,
            sr=self.sampling_rate
        )

    def get_mpe_object(self) -> mpe.AudioFileClip:
        return mpe.AudioFileClip(self.filepath)


def check_tempo_match(
        audio1: AudioClip,
        audio2: AudioClip,
        tempo_tol: float=0.15
) -> None:
    logging.info(f"{audio1.name} tempo: {audio1.tempo}")
    logging.info(f"{audio2.name} tempo: {audio2.tempo}")
    tempo_diff = abs(audio1.tempo - audio2.tempo) / audio1.tempo
    if tempo_diff > tempo_tol:
        raise ValueError(
            f"Tempo difference of {tempo_diff:.3f} is greater than"
            f"allowed value of {tempo_tol}. Try increasing tempo_tol "
            f"parameter."
        )
    else:
        logging.info("Tempo's compatible.")


def alter_media_speed(
        input_path: str,
        output_path: str,
        tempo_multi: str,
        is_audio: bool=False
) -> None:
    if is_audio:
        output_arg = ["-filter", f"atempo={tempo_multi}"]
    else:
        output_arg = (
            f'-filter_complex "[0:v]setpts={1/tempo_multi}*PTS[v];[0:a]'
            f'atempo={tempo_multi}[a]" -map "[v]" -map "[a]"'
        )
    ff = ffmpy.FFmpeg(
        inputs={input_path: None},
        outputs={output_path: output_arg}
    )
    ff.run()


def clean_up_files(filepaths: list) -> None:
    for filepath in filepaths:
        os.remove(filepath)
