import yt_dlp
import json

def download_apple_podcast(url, num_episodes=5, output_path='downloads'):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'playlistend': num_episodes,  # Limit the number of episodes to download
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            
            # Extract and print information about downloaded episodes
            if 'entries' in info:
                print(f"Downloaded episodes:")
                for entry in info['entries']:
                    print(f"- {entry['title']} ({entry['filepath']})")
            else:
                print(f"Downloaded: {info['title']} ({info['filepath']})")
            
            return info
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None

# Example usage
podcast_url = "https://podcasts.apple.com/us/podcast/the-daily/id1200361736"
result = download_apple_podcast(podcast_url, num_episodes=3)

if result:
    print("\nDownload completed successfully.")
    # Optionally, you can save the full info to a JSON file
    with open('podcast_info.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("Full podcast info saved to podcast_info.json")
else:
    print("Failed to download the podcast.")