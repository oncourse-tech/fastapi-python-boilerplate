import re
import json
import base64
import tempfile
import urllib.request
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import yt_dlp


# YouTube cookies for authentication (base64 encoded)
COOKIES_BASE64 = "IyBOZXRzY2FwZSBIVFRQIENvb2tpZSBGaWxlCiMgaHR0cHM6Ly9jdXJsLmhheHguc2UvcmZjL2Nvb2tpZV9zcGVjLmh0bWwKIyBUaGlzIGlzIGEgZ2VuZXJhdGVkIGZpbGUhIERvIG5vdCBlZGl0LgoKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE3NzAzNjc4NzgJR1BTCTEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDQ5MjYxMDQJUFJFRglmND00MDAwMDAwJmY2PTQwMDAwMDAwJnR6PUFzaWEuQ2FsY3V0dGEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDE5MDIxMDMJX19TZWN1cmUtMVBTSURUUwlzaWR0cy1DalFCN0lfNjlBamlPRC1nQlVFMm4tNjVEVUdhLXRyd3RPRlZUZ0RjWUNUdWhvME9OQ3Y2eUdNN3JjY3FCRV9ySU9JbF9yLXdFQUEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDE5MDIxMDMJX19TZWN1cmUtM1BTSURUUwlzaWR0cy1DalFCN0lfNjlBamlPRC1nQlVFMm4tNjVEVUdhLXRyd3RPRlZUZ0RjWUNUdWhvME9OQ3Y2eUdNN3JjY3FCRV9ySU9JbF9yLXdFQUEKLnlvdXR1YmUuY29tCVRSVUUJLwlGQUxTRQkxODA0OTI2MTAzCUhTSUQJQV8xMzdGb2Q4NUdPZGhDbk4KLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDQ5MjYxMDMJU1NJRAlBb1Jndm1Gem5MNEtBVnZTTQoueW91dHViZS5jb20JVFJVRQkvCUZBTFNFCTE4MDQ5MjYxMDMJQVBJU0lECTVRVXZmVVAydkY4SXUzVWkvQThUX2s0NW5BcGtoclczVnIKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDQ5MjYxMDMJU0FQSVNJRAl4TzIteWJTS3h6RGFLdGhVL0FQangySXNlR0hZNUl6VGdHCi55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxODA0OTI2MTAzCV9fU2VjdXJlLTFQQVBJU0lECXhPMi15YlNLeHpEYUt0aFUvQVBqeDJJc2VHSFk1SXpUZ0cKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDQ5MjYxMDMJX19TZWN1cmUtM1BBUElTSUQJeE8yLXliU0t4ekRhS3RoVS9BUGp4MklzZUdIWTVJelRnRwoueW91dHViZS5jb20JVFJVRQkvCUZBTFNFCTE4MDQ5MjYxMDMJU0lECWcuYTAwMDZnakUyd09NOUtIRy1ILWlvTFBGQ09taVFOTFE3TURROGEzQUpIVk1OZm00SmowLXppQWl2c1pGbVMwbWNjLUJETWVGeUFBQ2dZS0FkUVNBUlFTRlFIR1gyTWlrdFkxbWk1NkhPaWY2X0Z6R0M3UUN4b1ZBVUY4eUtxVTE3ZXh2UkZEZWdqSUlJTjFHOWRIMDA3NgoueW91dHViZS5jb20JVFJVRQkvCVRSVUUJMTgwNDkyNjEwMwlfX1NlY3VyZS0xUFNJRAlnLmEwMDA2Z2pFMndPTTlLSEctSC1pb0xQRkNPbWlRTkxRN01EUThhM0FKSFZNTmZtNEpqMC14czQwS0lmYVkxLW9IOC1ZRnB1eVZRQUNnWUtBUThTQVJRU0ZRSEdYMk1pcEJmN3Qyc2JRaENPcmQ4UnZKQW5meG9WQVVGOHlLb2x5bnBFMVJTZ3lESXVTWVdqb1dINTAwNzYKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDQ5MjYxMDMJX19TZWN1cmUtM1BTSUQJZy5hMDAwNmdqRTJ3T005S0hHLUgtaW9MUEZDT21pUU5MUTdNRFE4YTNBSkhWTU5mbTRKajAtTGMzdUFma2dvdm14TURjNnNIT2NYQUFDZ1lLQVhrU0FSUVNGUUhHWDJNaUN4dVVHbE1qVGRRcTgzR2ZCRmdrZFJvVkFVRjh5S3JCVXo1YkR3bmpUZV84dWphaFFJQXMwMDc2Ci55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxODA0OTI2MTAzCUxPR0lOX0lORk8JQUZtbUYyc3dSZ0loQVA4anFNblV1TzJXa3UzWXgyNWRabThiMnVOZ1Y4aGFpZzZoV0Vnd1V4Zk1BaUVBcDRwUzBiVENrcklnY3dwWVI1azctaVpQeU56NWxTdDdXcEEzY3FjSkJ1STpRVVEzTWpObWVFNDJkWGxUWTI5SWExVlJPVGhrTFUxNkxWbEJVRXhLVWs5NWJGWTBRVWxvUzNaV1VXcGZkR2RNYzFCU05GWlZkV3cxVTA1c1ZUUkNaM0ZJVFRJNVVtVndTRkF6VVZaM2VXaFNWVUZzVVVoQmJYQTBVbmxPYWpKeVIyUTBTWEoxZFVoWFpreG9hMjg1TW1OaFkxVmlVM296ZDB4TVduVmFjM1pPU0ZKalIwUTBkbkJVUlV4dVFUUk1jRkZMVlhCNFlqSXlVRWx6V2pGcFJsUkIKLnlvdXR1YmUuY29tCVRSVUUJLwlGQUxTRQkxODAxOTAyMTEyCVNJRENDCUFLRXlYelhtVDZoUWNUc1hMd1cxMklNVHFPUnY2Tm44dWpSa0R3T2pUUnF3cV8tZkpjNzgtVFc2NmNZaXpaelA4MUdROUlLUGZ3Ci55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxODAxOTAyMTEyCV9fU2VjdXJlLTFQU0lEQ0MJQUtFeVh6WENOWVk4YzVtWFRIc3VYZzFyWGpsbnVUbk1OeGNkZVZPM3lGeU9zMnFEWVhIOXFLZW9JcHZ3SWNpeXlaV2hoZkEteUEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDE5MDIxMTIJX19TZWN1cmUtM1BTSURDQwlBS0V5WHpVamtSU0JiVGRORDZkRk1FSGZDQWRvN0Q1eWFjeElkRFcyaW1CVXA4Z0dmUHlHSDRVdnZmWGIyZFE0cjlnbHJXMVQKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTAJWVNDCVc4bWZCVzF6S1pFCi55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxNzg1OTE4MTA3CVZJU0lUT1JfSU5GTzFfTElWRQluRXV3ZmhJRWM4NAoueW91dHViZS5jb20JVFJVRQkvCVRSVUUJMTc4NTkxODEwNwlWSVNJVE9SX1BSSVZBQ1lfTUVUQURBVEEJQ2dKSlRoSUVHZ0FnVnclM0QlM0QKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE3ODU5MTgwNzcJX19TZWN1cmUtWU5JRAkxNS5ZVD1RRVlfbDhxMG9VSzNNaGNKQV9FcG5wbTgxRFcwWUVlZkFiVTl0UF9uVFUwaTV3YkxtenZmcE00Q0w3TjN3NVpYRkFweC1xMXJUODhCOElpYi02NXE3a0lMNzJFbVQxWjgydWFQVEVsQWpudWdqaDMyV1EwaG9uRFZHZDRheWtaZ3dMNDVGdnQ4VzN2aFVYZDAzcS1LN1dLZzlXWUt2ZzNKWGYtcURBeC01ampya3drdmNieC1tYzJxalVBRXBhTDliWU9yUlJwbEJ4TTAxandYb1hxd2lMYWNSa3UwT0Z0bEhLTTRaLXV6NTlEYVJnV1phOWg4OHVrRTNidV9iTnlsTElWeGZwanpyNjlYS2hPakgtcHR4SWlpd3R0ZUhzWHJ6a3J2SWpIRmxPU19YRW4wM2Y3MzlfOWpNN3ZsdXktWTRoSE8xT2RPckNDMWFoeDJPNDZSa1EKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE3ODU5MTgwNzkJX19TZWN1cmUtUk9MTE9VVF9UT0tFTglDSTNvb3JQVTlQYVpvUUVRanRqTnliZkVrZ01ZaE9lVnlyZkVrZ00lM0QK"
def get_cookies_file():
    """Create a temporary cookies file from base64 encoded content and return its path."""
    cookies_content = base64.b64decode(COOKIES_BASE64).decode('utf-8')
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name


app = FastAPI(
    title="YouTube Transcript API",
    description="API to fetch YouTube video transcripts",
    version="1.0.0",
)


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL or video ID")


def get_subtitles_with_ytdlp(video_id: str, lang: str = "en"):
    """Fetch subtitles using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cookies_file = get_cookies_file()

    print(cookies_file)
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang, 'en'],
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_file,
    }

    # Preferred formats in order
    preferred_formats = ['json3', 'srv3', 'vtt', 'ttml']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            for lang_code in [lang, 'en']:
                # Try subtitles first, then automatic captions
                for caption_source, is_auto in [(subtitles, False), (automatic_captions, True)]:
                    if lang_code in caption_source:
                        # Try preferred formats in order
                        for preferred_ext in preferred_formats:
                            for fmt in caption_source[lang_code]:
                                if fmt.get('ext') == preferred_ext:
                                    return fmt.get('url'), lang_code, is_auto, fmt.get('ext'), None
                        # Fallback: return first available format
                        if caption_source[lang_code]:
                            fmt = caption_source[lang_code][0]
                            return fmt.get('url'), lang_code, is_auto, fmt.get('ext'), None

            return None, None, None, None, None
    except Exception as e:
        return None, None, None, None, f"Error: {str(e)} | Cookie file: {cookies_file}"


def parse_subtitles(subtitle_url: str, fmt: str):
    """Fetch and parse subtitles based on format."""
    with urllib.request.urlopen(subtitle_url) as response:
        content = response.read().decode()

    if fmt == 'json3':
        return parse_json3(content)
    elif fmt == 'srv3':
        return parse_srv3(content)
    elif fmt == 'vtt':
        return parse_vtt(content)
    elif fmt == 'ttml':
        return parse_ttml(content)
    else:
        # Try json3 parsing as default
        return parse_json3(content)


def parse_json3(content: str):
    """Parse json3 subtitle format."""
    data = json.loads(content)
    transcript = []
    for event in data.get('events', []):
        if 'segs' in event:
            text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
            if text:
                transcript.append({
                    'text': text,
                    'start': event.get('tStartMs', 0) / 1000,
                    'duration': event.get('dDurationMs', 0) / 1000
                })
    return transcript


def parse_srv3(content: str):
    """Parse srv3 (YouTube XML) subtitle format."""
    transcript = []
    # Simple XML parsing for srv3 format
    pattern = r'<text start="([^"]+)" dur="([^"]+)"[^>]*>([^<]*)</text>'
    matches = re.findall(pattern, content)
    for start, dur, text in matches:
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'").replace('&quot;', '"')
        text = re.sub(r'<[^>]+>', '', text).strip()
        if text:
            transcript.append({
                'text': text,
                'start': float(start),
                'duration': float(dur)
            })
    return transcript


def parse_vtt(content: str):
    """Parse VTT subtitle format."""
    transcript = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for timestamp lines (00:00:00.000 --> 00:00:00.000)
        if '-->' in line:
            times = line.split('-->')
            start_time = parse_vtt_timestamp(times[0].strip())
            end_time = parse_vtt_timestamp(times[1].strip().split()[0])
            # Collect text lines
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text_lines.append(lines[i].strip())
                i += 1
            text = ' '.join(text_lines)
            text = re.sub(r'<[^>]+>', '', text).strip()
            if text:
                transcript.append({
                    'text': text,
                    'start': start_time,
                    'duration': end_time - start_time
                })
        i += 1
    return transcript


def parse_vtt_timestamp(ts: str) -> float:
    """Convert VTT timestamp to seconds."""
    parts = ts.replace(',', '.').split(':')
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return 0.0


def parse_ttml(content: str):
    """Parse TTML subtitle format."""
    transcript = []
    pattern = r'<p[^>]*begin="([^"]+)"[^>]*end="([^"]+)"[^>]*>([^<]*(?:<[^>]*>[^<]*)*)</p>'
    matches = re.findall(pattern, content)
    for begin, end, text in matches:
        start = parse_ttml_timestamp(begin)
        end_time = parse_ttml_timestamp(end)
        text = re.sub(r'<[^>]+>', '', text).strip()
        if text:
            transcript.append({
                'text': text,
                'start': start,
                'duration': end_time - start
            })
    return transcript


def parse_ttml_timestamp(ts: str) -> float:
    """Convert TTML timestamp to seconds."""
    # Handle formats like "00:00:00.000" or "00:00:00,000"
    ts = ts.replace(',', '.')
    parts = ts.split(':')
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0.0


@app.get("/")
def root():
    """Redirect to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/api/transcript/{video_id:path}")
def get_transcript(video_id: str, lang: str = "en"):
    """
    Fetch transcript for a YouTube video.

    - **video_id**: YouTube video ID or full URL
    - **lang**: Language code for transcript (default: en)
    """
    try:
        extracted_id = extract_video_id(video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        subtitle_url, actual_lang, is_auto, fmt, error_msg = get_subtitles_with_ytdlp(extracted_id, lang)

        if error_msg:
            raise HTTPException(status_code=500, detail=error_msg)

        if not subtitle_url:
            raise HTTPException(status_code=404, detail="No transcript available for this video")

        transcript_data = parse_subtitles(subtitle_url, fmt)
        full_text = " ".join([entry['text'] for entry in transcript_data])

        return {
            "video_id": extracted_id,
            "language": actual_lang,
            "is_auto_generated": is_auto,
            "transcript": transcript_data,
            "full_text": full_text
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transcript-languages/{video_id:path}")
def get_available_languages(video_id: str):
    """
    Get available transcript languages for a YouTube video.

    - **video_id**: YouTube video ID or full URL
    """
    try:
        extracted_id = extract_video_id(video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        url = f"https://www.youtube.com/watch?v={extracted_id}"
        cookies_file = get_cookies_file()

        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookies_file,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            languages = []
            for lang_code in subtitles:
                languages.append({"language_code": lang_code, "is_generated": False})
            for lang_code in automatic_captions:
                if lang_code not in subtitles:
                    languages.append({"language_code": lang_code, "is_generated": True})

            return {"video_id": extracted_id, "languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/list-formats/{video_id:path}")
def list_formats(video_id: str, lang: str = "en"):
    """
    List available subtitle formats for a YouTube video.
    Useful for debugging format availability issues.

    - **video_id**: YouTube video ID or full URL
    - **lang**: Language code to check formats for (default: en)
    """
    try:
        extracted_id = extract_video_id(video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        url = f"https://www.youtube.com/watch?v={extracted_id}"
        cookies_file = get_cookies_file()

        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookies_file,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            result = {
                "video_id": extracted_id,
                "cookie_file": cookies_file,
                "requested_lang": lang,
                "subtitles": {},
                "automatic_captions": {}
            }

            # Get formats for subtitles
            if lang in subtitles:
                result["subtitles"][lang] = [
                    {"ext": fmt.get('ext'), "url": fmt.get('url')[:100] + "..." if fmt.get('url') else None}
                    for fmt in subtitles[lang]
                ]

            # Get formats for automatic captions
            if lang in automatic_captions:
                result["automatic_captions"][lang] = [
                    {"ext": fmt.get('ext'), "url": fmt.get('url')[:100] + "..." if fmt.get('url') else None}
                    for fmt in automatic_captions[lang]
                ]

            # Also show 'en' if different from requested lang
            if lang != 'en':
                if 'en' in subtitles:
                    result["subtitles"]['en'] = [
                        {"ext": fmt.get('ext'), "url": fmt.get('url')[:100] + "..." if fmt.get('url') else None}
                        for fmt in subtitles['en']
                    ]
                if 'en' in automatic_captions:
                    result["automatic_captions"]['en'] = [
                        {"ext": fmt.get('ext'), "url": fmt.get('url')[:100] + "..." if fmt.get('url') else None}
                        for fmt in automatic_captions['en']
                    ]

            # Summary of all available languages
            result["all_subtitle_languages"] = list(subtitles.keys())[:20]  # Limit to first 20
            result["all_auto_caption_languages"] = list(automatic_captions.keys())[:20]

            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)} | Cookie file: {cookies_file}")
