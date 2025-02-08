from datetime import datetime
import sqlite3
from loguru import logger
import json


def create_connection():
    """Create a database connection to a SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect('db/downloads.db')
        logger.info(f"Successfully connected to database: db/downloads.db")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        if conn:
            conn.close()
        return None


"""
    #sqlite extract json
    SELECT id, json_extract(metadata, '$.title') as title
    FROM content_downloads cd
"""


def create_table(conn):
    """Create a table to store youtube download logs."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT,
                video_url TEXT,
                audio_file_path TEXT,
                transcript_file_path TEXT,
                transcript_text TEXT,
                metadata JSON,
                download_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        logger.info("Successfully created table: youtube_downloads")
    except sqlite3.Error as e:
        logger.error(f"Error creating table: {e}")


def save_download_log(conn, channel_url, video_url, audio_file_path, transcript_file_path, transcript_text, meta_data, original_time):
    """Save the youtube download log to the database.

    Args:
        conn (sqlite3.Connection): Database connection object.
        channel_url (str): YouTube channel URL.
        video_url (str): YouTube video URL.
        audio_file_path (str): Path to the downloaded audio file.
        transcript_file_path (str): Path to the transcript file.
        transcript_text (str): Transcript text content.
        meta_data (JSON): Video metadata in JSON format.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO content_downloads (channel_url, video_url, audio_file_path, transcript_file_path, transcript_text, metadata,
                    original_timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (channel_url, video_url, audio_file_path,
             transcript_file_path, transcript_text, meta_data, original_time),
        )
        conn.commit()
        logger.info(f"Successfully saved download log for video: {video_url}")
    except sqlite3.Error as e:
        logger.error(f"Error saving download log: {e}")


def run_fetch(conn: sqlite3.Connection, query: str, params: tuple):
    """Execute a fetch query and return the result.

    Args:
        conn (sqlite3.Connection): Database connection object.
        query (str): SQL query string.
        params (list): Parameters for the SQL query.

    Returns:
        list: List of rows fetched from the database, or None if an error occurs.
    """
    try:
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # conn.commit() # No commit needed for SELECT queries
        logger.debug(f"Successfully fetched data for query: {query}")
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error fetching data: {e}")
        return None

# update db


def update_table(conn: sqlite3.Connection, query: str, params: tuple):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        # conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"General error: {e}")


def extract_metadata(ydl, entry):
    # Download each video individually
    d_info = ydl.extract_info(
        entry['webpage_url'], download=True)
    # entry['title']
    logger.info(f"Downloaded Title: {entry['title']}")
    logger.info(f"Video Tags: {entry['tags']}")
    logger.info(f"Video Categories: {entry['categories']}")
    logger.info(
        f"Video Descriptions: {entry['description']}")
    logger.info(f"Video Channel ID: {entry['channel_id']}")
    logger.info(f"Video Original Timestamp: {entry['timestamp']}")

    # json_string = json.dumps(
    #                          ydl.sanitize_info(d_info), indent=3)
    # yt_metadata = json.loads(json_string)

    # yt_metadata is a dictionary
    yt_metadata = ydl.sanitize_info(d_info)
    if "formats" in yt_metadata:
        del yt_metadata["formats"]

    if "automatic_captions" in yt_metadata:
        del yt_metadata["automatic_captions"]

    if "thumbnails" in yt_metadata:
        del yt_metadata["thumbnails"]

    json_string = json.dumps(yt_metadata, indent=3)

    original_time = datetime.fromtimestamp(entry['timestamp'])

    return json_string, original_time
