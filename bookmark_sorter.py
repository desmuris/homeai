import os
import re
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import defaultdict

# Basic keyword sets for simple categorization
CONTENT_TYPES = {
    'video': ['youtube.com', 'vimeo.com', 'video'],
    'article': ['blog', 'news', 'article'],
    'tool': ['tool', 'software', 'app'],
    'service': ['service', 'platform']
}

DOMAIN_CATEGORIES = {
    'crypto': ['crypto', 'blockchain', 'bitcoin', 'ethereum'],
    'self-improvement': ['self improvement', 'self-help', 'mindfulness'],
    'education': ['education', 'tutorial', 'learn', 'course']
}

THEME_KEYWORDS = {
    'Python': ['python', 'django', 'flask', 'numpy'],
    "women's psychology": ['women', 'psychology', 'relationship'],
    'cryptocurrency projects': ['crypto', 'token', 'blockchain']
}

HEADERS = {
    'User-Agent': 'bookmark-sorter/1.0'
}


def parse_bookmarks(html_path):
    """Parse an exported bookmarks HTML file and return URLs."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    links = [(a.get_text(strip=True), a['href'])
             for a in soup.find_all('a') if a.has_attr('href')]
    return links


def fetch_page(url, timeout=10):
    """Fetch URL content with a timeout."""
    try:
        resp = requests.get(url, timeout=timeout, headers=HEADERS)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def categorize(url, text):
    """Return content_type, domain_category, theme based on heuristics."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    content_type = 'other'
    for ct, words in CONTENT_TYPES.items():
        if any(w in netloc for w in words) or (text and any(w in text.lower() for w in words)):
            content_type = ct
            break

    domain_cat = 'other'
    for cat, words in DOMAIN_CATEGORIES.items():
        if any(w in netloc for w in words) or (text and any(w in text.lower() for w in words)):
            domain_cat = cat
            break

    theme = 'general'
    for th, words in THEME_KEYWORDS.items():
        if text and any(re.search(r'\b' + re.escape(w) + r'\b', text, re.I) for w in words):
            theme = th
            break

    return content_type, domain_cat, theme


def main():
    parser = argparse.ArgumentParser(description='Sort bookmarks into categories.')
    parser.add_argument('html', help='Bookmarks HTML export file')
    parser.add_argument('--out', default='sorted_bookmarks', help='Output folder')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of bookmarks (for testing)')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    unreachable_path = os.path.join(args.out, 'unreachable.txt')
    unreachable = []

    links = parse_bookmarks(args.html)
    if args.limit:
        links = links[:args.limit]

    categories = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for title, url in links:
        text = fetch_page(url)
        if text is None:
            unreachable.append(url)
            continue
        ct, dc, th = categorize(url, text)
        categories[ct][dc][th].append(url)

    # write unreachable
    if unreachable:
        with open(unreachable_path, 'w', encoding='utf-8') as f:
            for url in unreachable:
                f.write(url + '\n')

    # create output tree and store URLs
    for ct, dcats in categories.items():
        for dc, themes in dcats.items():
            for th, urls in themes.items():
                dir_path = os.path.join(args.out, ct, dc)
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, f'{th}.txt')
                with open(file_path, 'w', encoding='utf-8') as f:
                    for url in urls:
                        f.write(url + '\n')


if __name__ == '__main__':
    main()
