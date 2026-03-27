from flask import Flask, request, jsonify
import instaloader
import re
from urllib.parse import urlparse

app = Flask(__name__)

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    save_metadata=False
)

def extract_shortcode(input_str):
    if not input_str:
        return None

    input_str = input_str.strip()

    # Direct shortcode
    if re.fullmatch(r"[A-Za-z0-9_-]{5,}", input_str):
        return input_str

    try:
        parsed = urlparse(input_str)
        path = parsed.path.rstrip("/")

        match = re.search(r"/(reel|p|tv)/([A-Za-z0-9_-]+)", path)
        if match:
            return match.group(2)

    except Exception:
        return None

    return None


@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        data = request.get_json(silent=True) or {}
        url = data.get("url")

        if not url:
            return jsonify({"error": "URL is required"}), 400

        shortcode = extract_shortcode(url)
        if not shortcode:
            return jsonify({"error": "Invalid Instagram URL or shortcode"}), 400

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        result = {
            "id": post.shortcode,
            "likes": post.likes or 0,
            "comments": post.comments or 0,
            "views": getattr(post, "video_view_count", 0) or 0,
            "caption": post.caption or "",
            "owner": post.owner_username,
            "is_video": post.is_video
        }

        return jsonify({
            "success": True,
            "data": result
        })

    except instaloader.exceptions.QueryReturnedNotFoundException:
        return jsonify({"error": "Post not found"}), 404

    except instaloader.exceptions.PrivateProfileNotFollowedException:
        return jsonify({"error": "Private profile"}), 403

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "API running"