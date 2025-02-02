from datetime import datetime
import torch
import whisper

import sys
PROJECT_ROOT = "/models/DevSpace/FinanceAssistant"
sys.path.insert(0, PROJECT_ROOT)

from core.utils.db import create_connection, create_table, run_fetch, update_table

# turbo is the bestter balance between speed and accuracy
device = torch.device(
    'cuda') if torch.cuda.is_available() else torch.device('cpu')
whsiper_model = whisper.load_model("turbo", device=device)
print("Whisper model loaded.")


def test_whisper_functionality(url):

    start = datetime.now()
    transcript = whsiper_model.transcribe(url)['text']
    duration = datetime.now() - start
    print(f'{duration} : {url} \n\n transcript')
    return transcript


def update_transcript(conn, id, transcript, upload_datatime):
    sql = """
        UPDATE content_downloads 
        set download_time = STRFTIME('%Y-%m-%d %H:%M:%S', ?)
        and transcript_text = ?
        where id = ?
    """
    update_table(conn, sql, (upload_datatime,transcript,id))




if __name__ == '__main__':
    conn = create_connection()

    sql = """select
        id,
        audio_file_path,
        transcript_file_path,
        STRFTIME('%Y-%m-%d %H:%M:%S',(json_extract(metadata, "$.timestamp") / 86400.0 + 2440587.5)) upload_time
    from
        content_downloads cd
    where
        channel_url = ? """
    rows = run_fetch(conn,sql , ("https://www.youtube.com/@MeiTouJun/videos",))

    for entry in rows:
        transcript = test_whisper_functionality(entry['audio_file_path'])

        with open(entry['transcript_file_path'],'w') as file:
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
