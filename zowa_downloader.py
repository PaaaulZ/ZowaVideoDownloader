import requests
import argparse
import sys
import re
import json
import ffmpeg

BASE_API_URL = "https://api.zowa.app/api/v2/videos/pwa/"
VIDEO_URL_REGEX = r"https://zowa.app/play/([0-9]{1,})"
VIDEO_QUALITY_REGEX = r"-([0-9]{3,4})p.m3u8"

def video_id_from_url(video_url):

    # Extract video id from complete url

    video_id = re.findall(VIDEO_URL_REGEX, video_url)
    if len(video_id) != 1:
        print("[-] Cannot get video id from URL (format must be https://zowa.app/play/[id])")
        sys.exit(1)

    video_id = video_id[0]
    return video_id


def get_m3u8_link(video_url):

    # Gets the first m3u8 url (a list of m3u8 url for each resolution)

    write_log(f"[+] URL: {video_url}")

    video_id = video_id_from_url(video_url)

    write_log(f"\t[+] Video id: {video_id}")

    final_url = f"{BASE_API_URL}{video_id}"
    write_log(f"\t[+] Fetching m3u8 link from: {final_url}")

    r = requests.get(final_url)
    if r.status_code == 200:
        json_data = json.loads(r.content)
        m3u8_url = json_data.get('video_url')
        return m3u8_url
    else:
        print(f"\t[-] Error fetching video_url from api. Status code {r.status_code}")
        sys.exit(1)

def get_m3u8_info(m3u8_url, action, chosen_resolution = None):

    # Extracts required information from the m3u8 list

    # Available actions:
    #   list_resolutions => Returns a list of available resolutions (does not download)
    #   custom => Downloads the video with a specific resolution
    #   default|best => Downloads the video with the best resolution available

    if m3u8_url is None:
        print("\t[-] Missing video_url from api")
    else:
        write_log(f"\t[+] Found m3u8 link: {m3u8_url}\n")
        r = requests.get(m3u8_url)
        if r.status_code == 200:
            available_resolutions = re.findall(VIDEO_QUALITY_REGEX, str(r.content))
            if len(available_resolutions) >= 1:

                if action == "list_resolutions":
                    # Return available resolutions
                    return available_resolutions
                elif action == "custom":
                    # Return m3u8 of the required resolution
                    if chosen_resolution in available_resolutions:
                        best_resolution = chosen_resolution
                    else:
                        print(f"\t[-] Resolution {chosen_resolution}p is not available for this video")
                        sys.exit(1)
                else:
                    # Search for the best resolution
                    best_resolution = 0
                    for resolution in available_resolutions:
                        if int(resolution) > best_resolution:
                            best_resolution = int(resolution)
            m3u8_url = m3u8_url.replace('.m3u8', f'-{best_resolution}p.m3u8')
            return m3u8_url
        else:
            write_log(f"\t[-] Error fetching resolution info from m3u8. Status code: {r.status_code}")

def download_video(final_m3u8_url, output_path, video_id):

    # Launch ffmpeg to compose the final video file

    write_log(f"\t[+] Final m3u8 link: {final_m3u8_url}\n\n")
    (
        ffmpeg
        .input(final_m3u8_url)
        .output(f"{output_path}/{video_id}.mp4", codec='copy', vcodec='copy', crf=50)
        .run()
    )
    return


def write_log(text):
    if verbose:
        print(text)

if __name__ == '__main__':

    global verbose

    parser = argparse.ArgumentParser(description='Download videos from zowa.app')
    parser.add_argument('--url', '-u', action='store', type=str, help='URL of the video you want to download', required=True)
    parser.add_argument('--output', '-o', action='store', type=str, help='Output path')
    parser.add_argument('--resolution', '-r', action='store', type=str, help='Download with chosen resolution')
    parser.add_argument('--listresolutions', '-lr', action='store_true', help='List available resolutions (does not download)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Shows advanced logs')
    args = parser.parse_args()

    verbose = args.verbose
    video_url = args.url
    output_path = args.output
    resolution = args.resolution

    if args.listresolutions:
        action = "list_resolutions"
    elif resolution is not None:
        action = "custom"
    else:
        action = "best"

    write_log("[+] Downloading {video_url} with action {action}")

    if action != "list_resolutions" and output_path is None:
        print(f"\t[-] Output path is required")
        sys.exit(1)
    
    m3u8_list_url = get_m3u8_link(video_url)
    m3u8_info = get_m3u8_info(m3u8_list_url, action, resolution)
    if action == "list_resolutions":
        print(f"\t[+] Available resolutions: {m3u8_info}")
        sys.exit(0)
    else:
        download_video(m3u8_info, output_path, video_id_from_url(video_url))
