import re
import json
import tempfile
import urllib.request
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import yt_dlp


# YouTube cookies for authentication
COOKIES_CONTENT = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	0	PREF	f4=4000000&f6=40000000&tz=UTC&hl=en
.youtube.com	TRUE	/	TRUE	1798200414	__Secure-1PSIDTS	sidts-CjQBflaCdWInKGJPCwFOs81jjkFZ-iI4uTzeTzRiq8SQ_ynhl77qGP685JRXko9hxusdKlfeEAA
.youtube.com	TRUE	/	TRUE	1798200414	__Secure-3PSIDTS	sidts-CjQBflaCdWInKGJPCwFOs81jjkFZ-iI4uTzeTzRiq8SQ_ynhl77qGP685JRXko9hxusdKlfeEAA
.youtube.com	TRUE	/	FALSE	1801224414	HSID	AHSEOdT80czAzt6Sm
.youtube.com	TRUE	/	TRUE	1801224414	SSID	AC381844lpl0oyiZj
.youtube.com	TRUE	/	FALSE	1801224414	APISID	qTL4s_lvYqF6dcv-/At1O3m2fsToBXZIhF
.youtube.com	TRUE	/	TRUE	1801224414	SAPISID	_dIAXHu53eS4v50e/AEh3kD8smMWFTcdfK
.youtube.com	TRUE	/	TRUE	1801224414	__Secure-1PAPISID	_dIAXHu53eS4v50e/AEh3kD8smMWFTcdfK
.youtube.com	TRUE	/	TRUE	1801224414	__Secure-3PAPISID	_dIAXHu53eS4v50e/AEh3kD8smMWFTcdfK
.youtube.com	TRUE	/	FALSE	1801224414	SID	g.a0004gjE20T6CMBLpTsD56xrVExYw-Ozj_o-_DnlM6CaUq0Q269aR50Nj6mXzXzngX2kwtKjFwACgYKAaMSARQSFQHGX2MidG090jjwhx3dcCxO598umRoVAUF8yKqyINh_q3gs89jznv5e7G-30076
.youtube.com	TRUE	/	TRUE	1801224414	__Secure-1PSID	g.a0004gjE20T6CMBLpTsD56xrVExYw-Ozj_o-_DnlM6CaUq0Q269aUf_ziMBW_lEb9iUBSQGNXwACgYKAYISARQSFQHGX2MiKv3k-wEyJMvDGeuvFEGvVhoVAUF8yKpBpsmmMAvQ0K_fsKCKNSsk0076
.youtube.com	TRUE	/	TRUE	1801224414	__Secure-3PSID	g.a0004gjE20T6CMBLpTsD56xrVExYw-Ozj_o-_DnlM6CaUq0Q269aPmqYeHTZyAFtqyu1BccdCQACgYKAXMSARQSFQHGX2MiQQH1Z36T_DMUm_Po8auqWBoVAUF8yKpTdLtN3DeWCkZaTbdalqbK0076
.youtube.com	TRUE	/	TRUE	1801224415	LOGIN_INFO	AFmmF2swRAIgAosOXvApy6Wt0_uHObTG8qN_AYQ1q-W1v1csTCI-HEUCIHpMW8ZXK6C7fMfowY8zafCvPIY1Myv9CopKMLinYBSz:QUQ3MjNmenpwYWZGellsLWhSSS0wYTJoMmtqX1JWV0hpVElidWoyQXZ2TkVRYW8wTU1IYzZEN2txQlhRRktaV3lHSXBreFBQVENRMGQ5cTlkNkNBdWRaeG5wbzd5MUhCUnoxWWxONjBqbnNfdUQwWlRYd3BWc1hZdmlBRFVLcGpCbGVyOGhsYWlRVVh3Q3BDSVJKeHI5aldOWHlPMk1zSVVR
.youtube.com	TRUE	/	FALSE	1798202207	SIDCC	AKEyXzVa5Tu82rFfoA2gYCM_frHRLSHNRH9WVAOy5G6ejXAJ-oUwezgWevJsY0qGQDkI4sRX
.youtube.com	TRUE	/	TRUE	1798202207	__Secure-1PSIDCC	AKEyXzXrNLt4oWaptaUwo_6iMMV1PzYHRK47qGRTLlcZHsHk8OxJ3GRB8qGyd_ybCfcCfg03Bg
.youtube.com	TRUE	/	TRUE	1798202207	__Secure-3PSIDCC	AKEyXzW3swXi75r-AqcbQRZIHfs1sL8IGdzAvk86WuHDMl4hdujeN0fTpMoaA1PBz-g6demq
.youtube.com	TRUE	/	TRUE	0	YSC	BiGJaBvvtTs
.youtube.com	TRUE	/	TRUE	1782218207	VISITOR_INFO1_LIVE	okT8cjC_XmA
.youtube.com	TRUE	/	TRUE	1782218207	VISITOR_PRIVACY_METADATA	CgJJThIEGgAgGw%3D%3D
.youtube.com	TRUE	/	TRUE	1782216386	__Secure-ROLLOUT_TOKEN	CLeI953S-_Ou9QEQ38-82NnYkQMYocOG2dnYkQM%3D
"""


def get_cookies_file():
    """Create a temporary cookies file and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(COOKIES_CONTENT)
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

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang, 'en'],
        'subtitlesformat': 'json3',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_file,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        subtitles = info.get('subtitles', {})
        automatic_captions = info.get('automatic_captions', {})

        for lang_code in [lang, 'en']:
            if lang_code in subtitles:
                for fmt in subtitles[lang_code]:
                    if fmt.get('ext') == 'json3':
                        return fmt.get('url'), lang_code, False
            if lang_code in automatic_captions:
                for fmt in automatic_captions[lang_code]:
                    if fmt.get('ext') == 'json3':
                        return fmt.get('url'), lang_code, True

        return None, None, None


def parse_json3_subtitles(subtitle_url: str):
    """Fetch and parse json3 subtitle format."""
    with urllib.request.urlopen(subtitle_url) as response:
        data = json.loads(response.read().decode())

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
        subtitle_url, actual_lang, is_auto = get_subtitles_with_ytdlp(extracted_id, lang)

        if not subtitle_url:
            raise HTTPException(status_code=404, detail="No transcript available for this video")

        transcript_data = parse_json3_subtitles(subtitle_url)
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
