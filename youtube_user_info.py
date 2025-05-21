import re
from googleapiclient.discovery import build

# Replace with your own API key
API_KEY = ''
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


def build_youtube_client():
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)


def extract_channel_id_from_url(url):
    """Extracts the channel ID, username, or custom URL from a given YouTube URL."""
    if '/channel/' in url:
        return {'type': 'id', 'value': url.split('/channel/')[1].split('/')[0]}
    elif '/user/' in url:
        return {'type': 'username', 'value': url.split('/user/')[1].split('/')[0]}
    elif '/c/' in url:
        # Note: Custom URLs need to be resolved manually
        return {'type': 'custom', 'value': url.split('/c/')[1].split('/')[0]}
    else:
        raise ValueError("Invalid or unsupported YouTube URL format.")


def get_channel_info(youtube, channel_identifier):
    """Fetch channel information by ID or username."""
    if channel_identifier['type'] == 'username':
        request = youtube.channels().list(
            forUsername=channel_identifier['value'],
            part='snippet,statistics,contentDetails'
        )
    elif channel_identifier['type'] == 'id':
        request = youtube.channels().list(
            id=channel_identifier['value'],
            part='snippet,statistics,contentDetails'
        )
    else:
        # Custom URL fallback: Search by name
        request = youtube.search().list(
            q=channel_identifier['value'],
            type='channel',
            part='snippet',
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            channel_id = response['items'][0]['snippet']['channelId']
            return get_channel_info(youtube, {'type': 'id', 'value': channel_id})
        else:
            print("No channel found for custom URL or search term.")
            return None

    response = request.execute()
    if not response['items']:
        print("No channel found.")
        return None

    channel = response['items'][0]
    info = {
        'Channel ID': channel['id'],
        'Title': channel['snippet']['title'],
        'Description': channel['snippet']['description'],
        'Published At': channel['snippet']['publishedAt'],
        'Subscribers': channel['statistics'].get('subscriberCount', 'Hidden'),
        'Views': channel['statistics'].get('viewCount', '0'),
        'Video Count': channel['statistics'].get('videoCount', '0'),
        'Uploads Playlist ID': channel['contentDetails']['relatedPlaylists']['uploads'],
    }
    return info


def get_latest_videos(youtube, uploads_playlist_id, max_results=5):
    """Fetch latest videos from a channel's uploads playlist."""
    request = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part='snippet',
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response['items']:
        video_info = {
            'Title': item['snippet']['title'],
            'Video ID': item['snippet']['resourceId']['videoId'],
            'Published At': item['snippet']['publishedAt'],
            'URL': f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}"
        }
        videos.append(video_info)

    return videos

# --- Example Usage ---


def main():
    youtube = build_youtube_client()

    # Examples: Use username, channel ID, or URL
    input_type = 'url'
    print("Paste the channel's url you want to get info from")
    input_value = input('>')

    if input_type == 'url':
        channel_identifier = extract_channel_id_from_url(input_value)
    else:
        channel_identifier = {'type': input_type, 'value': input_value}

    info = get_channel_info(youtube, channel_identifier)
    if info:
        print("\nChannel Information:")
        for key, value in info.items():
            print(f"{key}: {value}")

        print("\nLatest Videos:")
        videos = get_latest_videos(youtube, info['Uploads Playlist ID'])
        for vid in videos:
            print(f"- {vid['Title']} ({vid['Published At']})\n  {vid['URL']}")


if __name__ == '__main__':
    main()
