import pandas as pd
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube"]

def get_youtube_client():
    flow = InstalledAppFlow.from_client_secrets_file(
        "/home/agustin/Descargas/script_playlist/client_secret.json",
        SCOPES,
    )
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

def create_playlist(youtube, title, description=""):
    response = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": "private"},
        },
    ).execute()
    return response["id"]

def search_video(youtube, query):
    response = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=1,
        type="video",
    ).execute()

    items = response.get("items", [])
    return items[0]["id"]["videoId"] if items else None

def add_to_playlist(youtube, playlist_id, video_id):
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
        ).execute()
        print(f"Added video {video_id} to playlist")
    except HttpError as e:
        print(f"Failed to add video {video_id}: {e}")
    except Exception as e:
        print(f"Unexpected error adding video {video_id}: {e}")

def load_songs(path):
    df = pd.read_csv(path, header=None, engine="python")

    songs = (
        df.stack()
        .dropna()
        .astype(str)
        .str.strip('"')
        .loc[lambda s: s.str.contains(" - ")]
        .drop_duplicates()
        .tolist()
    )
    return songs

def main():
    songs = load_songs("/home/agustin/Descargas/script_playlist/songs.csv")

    youtube = get_youtube_client()
    playlist_id = create_playlist(
        youtube,
        title="CSV Playlist",
        description="Generated from CSV",
    )

    for song in songs:
        video_id = search_video(youtube, song)
        if video_id:
            add_to_playlist(youtube, playlist_id, video_id)
            time.sleep(1)  # Rate limiting

if __name__ == "__main__":
    main()
