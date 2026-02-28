import re
import json
import base64
import tempfile
import urllib.request
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import yt_dlp


# YouTube cookies for authentication (base64 encoded)
COOKIES_BASE64 = "IyBOZXRzY2FwZSBIVFRQIENvb2tpZSBGaWxlCiMgaHR0cHM6Ly9jdXJsLmhheHguc2UvcmZjL2Nvb2tpZV9zcGVjLmh0bWwKIyBUaGlzIGlzIGEgZ2VuZXJhdGVkIGZpbGUhIERvIG5vdCBlZGl0LgoKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE3NzIyNjMxNTMJR1BTCTEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDY4MjEzNzIJUFJFRglmND00MDAwMDAwJmY2PTQwMDAwMDAwJnR6PUFzaWEuQ2FsY3V0dGEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDM3OTczNzAJX19TZWN1cmUtMVBTSURUUwlzaWR0cy1DalFCQmoxQ1lyeVhmdHJnbkFsNml2RzBVeW5PNTlTdmp3QkVjWlhoZUVLTC1YRXVTaU5LSjhCWjdCdzItQkRIR3UwRzRxMndFQUEKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDM3OTczNzAJX19TZWN1cmUtM1BTSURUUwlzaWR0cy1DalFCQmoxQ1lyeVhmdHJnbkFsNml2RzBVeW5PNTlTdmp3QkVjWlhoZUVLTC1YRXVTaU5LSjhCWjdCdzItQkRIR3UwRzRxMndFQUEKLnlvdXR1YmUuY29tCVRSVUUJLwlGQUxTRQkxODA2ODIxMzcwCUhTSUQJQWNaQms1eWV3TzZEaHI0MTMKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDY4MjEzNzAJU1NJRAlBT3NQZDhHb0lGSDZIczBVWgoueW91dHViZS5jb20JVFJVRQkvCUZBTFNFCTE4MDY4MjEzNzAJQVBJU0lECWNzeEtrTjVXaWFkYkJSbmEvQXBHcHNiQ094dmNTaFl4cG8KLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDY4MjEzNzAJU0FQSVNJRAk1NnVqV3dRN0pDcDQwbHRaL0FpdHVyWURSc2JsNDNyVGJiCi55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxODA2ODIxMzcwCV9fU2VjdXJlLTFQQVBJU0lECTU2dWpXd1E3SkNwNDBsdFovQWl0dXJZRFJzYmw0M3JUYmIKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDY4MjEzNzAJX19TZWN1cmUtM1BBUElTSUQJNTZ1ald3UTdKQ3A0MGx0Wi9BaXR1cllEUnNibDQzclRiYgoueW91dHViZS5jb20JVFJVRQkvCUZBTFNFCTE4MDY4MjEzNzAJU0lECWcuYTAwMDdRakUyeHRSVlhvQXRRVkgwZHVpaHVrX28tVGN2RGgtRHIzdXJUZDFqU1hnTHV3UDY2bEtfMW1NTnlONHFJMUFSa1dtWHdBQ2dZS0FYb1NBUlFTRlFIR1gyTWkzOExNNUd1WG9zTE8zNEpxMDlDZ2l4b1ZBVUY4eUtvSXVZbzhsZ0loaG9uQVVVWXlEM1NqMDA3NgoueW91dHViZS5jb20JVFJVRQkvCVRSVUUJMTgwNjgyMTM3MAlfX1NlY3VyZS0xUFNJRAlnLmEwMDA3UWpFMnh0UlZYb0F0UVZIMGR1aWh1a19vLVRjdkRoLURyM3VyVGQxalNYZ0x1d1Bod2pWVHgyUWpxekxNemVsaXBKdEt3QUNnWUtBUWdTQVJRU0ZRSEdYMk1pRk80dzhlRldmMWgtT0xoSHhZU0FLeG9WQVVGOHlLclR0UDNTVWNla1JTY2RzYjNlYmdmQTAwNzYKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDY4MjEzNzAJX19TZWN1cmUtM1BTSUQJZy5hMDAwN1FqRTJ4dFJWWG9BdFFWSDBkdWlodWtfby1UY3ZEaC1EcjN1clRkMWpTWGdMdXdQY2VjbDdPUnEyRE9FRUlaYjNua0dQd0FDZ1lLQWI0U0FSUVNGUUhHWDJNaUh5MDB4SnVMUmN2aEpiTFFBd1hhUGhvVkFVRjh5S3BEVEtWZGxiN2pqVE5kOXJuNVVfajMwMDc2Ci55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxODA2ODIxMzcxCUxPR0lOX0lORk8JQUZtbUYyc3dSZ0loQUtFeTRHc3lKSFhqR1E2YjJxcHRRbkNscGhYTGlfQXYwcGpZd1hWUE1aUzdBaUVBbjR1eGZHaGNjQzMtZDBXOFBSSjZSWnVnTUNrNkZaYWROLU83RDhqaUZodzpRVVEzTWpObWVuUlVjMkpLZVhaTmNHbEpiWEZ3YUV0WWRVRjBURFpGZUdGbk1tSkdhMDFXVDBwTU5UWjFiR3gzZEdwcmJscHJaRzlOUTBoSmFUUTJSR3R6V0daTGRGVkpRVFpJV2tKMGVIRnZSRWxOTldWMVkwNXhhRU53VTJ4dE9WVlNhQzF1T1RWVFVqa3haRWhWWm5wcmNHVmFNRVk1VlV4SWExSXhlakZrVEd4MGJtd3lVemxaVXkwM1VEaFhkMUIyWlVwMlZXUXhaazVZVUVOWE5GbFIKLnlvdXR1YmUuY29tCVRSVUUJLwlGQUxTRQkxODAzNzk3MzgxCVNJRENDCUFLRXlYeldvV2Jsd1pqekctdU9qQlJiSnVUWERYVFc1dXdKZm9HWi1PU0ZIdVRFMHNCMEl2OE1hMkQ3cHRMUGhiZ0h4VnVuZ3Z3Ci55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxODAzNzk3MzgxCV9fU2VjdXJlLTFQU0lEQ0MJQUtFeVh6V1pwTjEzT3p1QW9LUHYzeU42N1RHOXU4aUk2TWFUbHlMU1N4QXItNmVLakpESFBoOHl0ejZLa3JCNTNnc3pWUlBKcmcKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE4MDM3OTczODEJX19TZWN1cmUtM1BTSURDQwlBS0V5WHpXM01kVWVMQzJObkVCWUtMeTVockM3dEZST1dUQl9IUmRUajh6TmZGOUhqQzA2b0xRak5IY1hVaHZfY21XSGI3bVYKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTAJWVNDCVVEV1J5SDVDb01vCi55b3V0dWJlLmNvbQlUUlVFCS8JVFJVRQkxNzg3ODEzMzc1CVZJU0lUT1JfSU5GTzFfTElWRQlMbkkybHBSTG9CcwoueW91dHViZS5jb20JVFJVRQkvCVRSVUUJMTc4NzgxMzM3NQlWSVNJVE9SX1BSSVZBQ1lfTUVUQURBVEEJQ2dKSlRoSUVHZ0FnQ2clM0QlM0QKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE3ODc4MTMzNTIJX19TZWN1cmUtWU5JRAkxNi5ZVD1BWlVwclFIWjducUY4RUE0Wm1TbFZFdTZ2cnpPcVJoR0F5TDhsOHR5VTNZcnk0TEJYUmJvR0hMTGFiMDhXQkxzcF9JaHE0b3N4SnFHSWd3V29MSzVCUTF4MEI0OUNCUE15Z3F0STdIRjZ3NXZUQVB6OUI3NEFQQTFodTRvOFN5LVRxT2sxTzYzNkRia0kzZTFxNnJRcTRHTDJ2cE11bnZMbWtnaGljbXkzMVYwYUh1Qlotb241Y0tSUFJQSDN6aFBqUVBzV2Y5Ui01bVpmMUdTRE1wa1RqT2d0aFUtWjY1Ym5ic2hNb1FCYjF0aXJuY2Y1Ulo5X0ZIZFNuakd0MllWbEN3RUkxeDJzeDNvbFV4SExHVEZRQVVHeWlyMkhmcXJsM1c3QmZTR3ltdy1pU0JlSEhDaEJrdzU4M1NjaTg4dm9hNlgwOW1PaWhSQ1Ytb080NGVIU1EKLnlvdXR1YmUuY29tCVRSVUUJLwlUUlVFCTE3ODc4MTMzNTQJX19TZWN1cmUtUk9MTE9VVF9UT0tFTglDUFdKMk15QmpiZmxwUUVRM3NfMmdzejdrZ01ZMC1IVGc4ejdrZ00lM0QK"
def get_cookies_content():
    """Decode and return the cookies content."""
    return base64.b64decode(COOKIES_BASE64).decode('utf-8')


def get_cookies_file():
    """Create a temporary cookies file from base64 encoded content and return its path."""
    cookies_content = get_cookies_content()
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
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_file,
        'ignore_no_formats_error': True,
        'extract_flat': False,
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
        cookies_content = get_cookies_content()
        return None, None, None, None, f"Error: {str(e)} | Cookie file: {cookies_file} | Cookies: {cookies_content}"


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
            'ignore_no_formats_error': True,
            'extract_flat': False,
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
        cookies_content = get_cookies_content()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)} | Cookie file: {cookies_file} | Cookies: {cookies_content}")


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
            'ignore_no_formats_error': True,
            'extract_flat': False,
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
        cookies_content = get_cookies_content()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)} | Cookie file: {cookies_file} | Cookies: {cookies_content}")
