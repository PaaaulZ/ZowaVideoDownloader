import requests
import argparse
import sys
import re
import json
import ffmpeg

BASE_API_URL = "https://api.zowa.app/api/v2/videos/pwa/"
VIDEO_URL_REGEX = r"https://zowa.app/play/([0-9]{1,})"

def download_video(url):

    print(f"[+] URL: {url}")

    video_id = re.findall(VIDEO_URL_REGEX, url)
    if len(video_id) != 1:
        print("[-] Cannot get video id from URL (format must be https://zowa.app/play/[id])")
        sys.exit(1)

    video_id = video_id[0]
    final_url = f"{BASE_API_URL}{video_id}"
    print(f"\t[+] Fetching m3u8 link from: {final_url}")

    r = requests.get(final_url)
    if r.status_code == 200:
        json_data = json.loads(r.content)
        m3u8_url = json_data.get('video_url')
        if m3u8_url is not None:
            print(f"\t[+] Final m3u8 link: {m3u8_url}\n\n")

            process = (
                ffmpeg
                .input(m3u8_url)
                .filter('bsf', 'a aac_adtstoasc')
                .output(f"{video_id}.mp4", codec='copy', vcodec='copy', crf=50)
                .run()
            )
        else:
            print("\t[-] Unable to find .m3u8 link")
        
    else:
        print("[-] Error fetching data from Zowa API: Reported status code {r.status_code}")

    return


if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='Download videos from zowa.app')
    parser.add_argument('--url', '-u', action='store', type=str, help='URL of the video you want to download', required=True)
    args = parser.parse_args()

    download_video(args.url)