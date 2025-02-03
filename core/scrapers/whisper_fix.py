from datetime import datetime
from pathlib import Path
import os
from whisper import Whisper

import sys

import os
sys.path.insert(0, os.path.abspath("./"))

from core.utils.db import create_connection, create_table, run_fetch, update_table
from core.utils.utils import get_whisper


def get_whisper_transcript(url, whsiper_model: Whisper) -> str:

    url = os.path.abspath(url)
    print(url)
    start = datetime.now()
    transcript = whsiper_model.transcribe(url)['text']
    duration = datetime.now() - start
    print(f'{duration} : {url} \n\n transcript')
    return transcript


def update_transcript(conn, id, transcript, upload_datatime) -> None:
    sql = """
        UPDATE content_downloads 
        set download_time = STRFTIME('%Y-%m-%d %H:%M:%S', ?)
        , transcript_text = ?
        where id = ?
    """
    update_table(conn, sql, (upload_datatime, transcript, id))


if __name__ == '__main__':
    conn = create_connection()
    whisper_model = get_whisper()

    sql = """select
        id,
        audio_file_path,
        transcript_file_path,
        STRFTIME('%Y-%m-%d %H:%M:%S',(json_extract(metadata, "$.timestamp") / 86400.0 + 2440587.5)) upload_time
    from
        content_downloads cd
    where
        channel_url = ? """
    rows = run_fetch(conn, sql, ("https://www.youtube.com/@MeiTouJun/videos",))

    for entry in rows:
        transcript = get_whisper_transcript(entry['audio_file_path'], whisper_model)

        with open(file=os.path.abspath(entry['transcript_file_path']), mode='w', encoding='utf-8') as file:
            file.write(transcript)
            file.close()

        update_transcript(conn, entry['id'], transcript, entry['upload_time'])

    """
    audios= [
        './download/hPl5ER1_ZS8.mp3',
        './download/gm2Pzbmflmk.mp3',
        './download/IBUQlnUSHQI.mp3'
    ]

    for v in audios:
        test_whisper_functionality(v)
    """
