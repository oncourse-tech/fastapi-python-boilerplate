import re
import json
import os
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import yt_dlp


# Optional proxy configuration via environment variable
PROXY_URL = os.environ.get("PROXY_URL", "")

# YouTube cookies embedded as string
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
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
)


@app.get("/api/data")
def get_sample_data():
    return {
        "data": [
            {"id": 1, "name": "Sample Item 1", "value": 100},
            {"id": 2, "name": "Sample Item 2", "value": 200},
            {"id": 3, "name": "Sample Item 3", "value": 300}
        ],
        "total": 3,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    return {
        "item": {
            "id": item_id,
            "name": "Sample Item " + str(item_id),
            "value": item_id * 100
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


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
    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        subtitles = info.get('subtitles', {})
        automatic_captions = info.get('automatic_captions', {})

        # Try requested language first, then fall back to English
        for lang_code in [lang, 'en']:
            # Check manual subtitles first
            if lang_code in subtitles:
                for fmt in subtitles[lang_code]:
                    if fmt.get('ext') == 'json3':
                        return fmt.get('url'), lang_code, False
            # Then check automatic captions
            if lang_code in automatic_captions:
                for fmt in automatic_captions[lang_code]:
                    if fmt.get('ext') == 'json3':
                        return fmt.get('url'), lang_code, True

        return None, None, None


def parse_json3_subtitles(subtitle_url: str):
    """Fetch and parse json3 subtitle format."""
    import urllib.request

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


@app.get("/api/transcript/{video_id:path}")
def get_transcript(video_id: str, lang: str = "en"):
    """
    Fetch transcript for a YouTube video.

    - video_id: YouTube video ID or full URL
    - lang: Language code for transcript (default: en)
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
    """Get available transcript languages for a YouTube video."""
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
        if PROXY_URL:
            ydl_opts['proxy'] = PROXY_URL

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            languages = []

            for lang_code in subtitles:
                languages.append({
                    "language_code": lang_code,
                    "is_generated": False
                })

            for lang_code in automatic_captions:
                if lang_code not in subtitles:
                    languages.append({
                        "language_code": lang_code,
                        "is_generated": True
                    })

            return {
                "video_id": extracted_id,
                "languages": languages
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vercel + FastAPI</title>
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                background-color: #000000;
                color: #ffffff;
                line-height: 1.6;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            header {
                border-bottom: 1px solid #333333;
                padding: 0;
            }
            
            nav {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                align-items: center;
                padding: 1rem 2rem;
                gap: 2rem;
            }
            
            .logo {
                font-size: 1.25rem;
                font-weight: 600;
                color: #ffffff;
                text-decoration: none;
            }
            
            .nav-links {
                display: flex;
                gap: 1.5rem;
                margin-left: auto;
            }
            
            .nav-links a {
                text-decoration: none;
                color: #888888;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                transition: all 0.2s ease;
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            .nav-links a:hover {
                color: #ffffff;
                background-color: #111111;
            }
            
            main {
                flex: 1;
                max-width: 1200px;
                margin: 0 auto;
                padding: 4rem 2rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            
            .hero {
                margin-bottom: 3rem;
            }
            
            .hero-code {
                margin-top: 2rem;
                width: 100%;
                max-width: 900px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            }
            
            .hero-code pre {
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                text-align: left;
                grid-column: 1 / -1;
            }
            
            h1 {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 1rem;
                background: linear-gradient(to right, #ffffff, #888888);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .subtitle {
                font-size: 1.25rem;
                color: #888888;
                margin-bottom: 2rem;
                max-width: 600px;
            }
            
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                width: 100%;
                max-width: 900px;
            }
            
            .card {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 1.5rem;
                transition: all 0.2s ease;
                text-align: left;
            }
            
            .card:hover {
                border-color: #555555;
                transform: translateY(-2px);
            }
            
            .card h3 {
                font-size: 1.125rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #ffffff;
            }
            
            .card p {
                color: #888888;
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }
            
            .card a {
                display: inline-flex;
                align-items: center;
                color: #ffffff;
                text-decoration: none;
                font-size: 0.875rem;
                font-weight: 500;
                padding: 0.5rem 1rem;
                background-color: #222222;
                border-radius: 6px;
                border: 1px solid #333333;
                transition: all 0.2s ease;
            }
            
            .card a:hover {
                background-color: #333333;
                border-color: #555555;
            }
            
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background-color: #0070f3;
                color: #ffffff;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-bottom: 2rem;
            }
            
            .status-dot {
                width: 6px;
                height: 6px;
                background-color: #00ff88;
                border-radius: 50%;
            }
            
            pre {
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 1rem;
                overflow-x: auto;
                margin: 0;
            }
            
            code {
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                font-size: 0.85rem;
                line-height: 1.5;
                color: #ffffff;
            }
            
            /* Syntax highlighting */
            .keyword {
                color: #ff79c6;
            }
            
            .string {
                color: #f1fa8c;
            }
            
            .function {
                color: #50fa7b;
            }
            
            .class {
                color: #8be9fd;
            }
            
            .module {
                color: #8be9fd;
            }
            
            .variable {
                color: #f8f8f2;
            }
            
            .decorator {
                color: #ffb86c;
            }
            
            @media (max-width: 768px) {
                nav {
                    padding: 1rem;
                    flex-direction: column;
                    gap: 1rem;
                }
                
                .nav-links {
                    margin-left: 0;
                }
                
                main {
                    padding: 2rem 1rem;
                }
                
                h1 {
                    font-size: 2rem;
                }
                
                .hero-code {
                    grid-template-columns: 1fr;
                }
                
                .cards {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header>
            <nav>
                <a href="/" class="logo">Vercel + FastAPI</a>
                <div class="nav-links">
                    <a href="/docs">API Docs</a>
                    <a href="/api/data">API</a>
                </div>
            </nav>
        </header>
        <main>
            <div class="hero">
                <h1>Vercel + FastAPI</h1>
                <div class="hero-code">
                    <pre><code><span class="keyword">from</span> <span class="module">fastapi</span> <span class="keyword">import</span> <span class="class">FastAPI</span>

<span class="variable">app</span> = <span class="class">FastAPI</span>()

<span class="decorator">@app.get</span>(<span class="string">"/"</span>)
<span class="keyword">def</span> <span class="function">read_root</span>():
    <span class="keyword">return</span> {<span class="string">"Python"</span>: <span class="string">"on Vercel"</span>}</code></pre>
                </div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <h3>Interactive API Docs</h3>
                    <p>Explore this API's endpoints with the interactive Swagger UI. Test requests and view response schemas in real-time.</p>
                    <a href="/docs">Open Swagger UI →</a>
                </div>
                
                <div class="card">
                    <h3>Sample Data</h3>
                    <p>Access sample JSON data through our REST API. Perfect for testing and development purposes.</p>
                    <a href="/api/data">Get Data →</a>
                </div>
                
            </div>
        </main>
    </body>
    </html>
    """
