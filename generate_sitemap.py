import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from tqdm import tqdm
from urllib.parse import quote

# Correct hreflang values for languages
languages = {
    "af": "af",  # Afrikaans
    "zh": "zh",  # Chinese
    "es": "es",  # Spanish
    "fr": "fr",  # French
    "de": "de",  # German
    "el": "el",  # Greek
    "in": "in",  # Indian
    "it": "it",  # Italian
    "ja": "ja",  # Japanese
    "ko": "ko",  # Korean
    "pl": "pl",  # Polish
    "pt": "pt",  # Portuguese
    "sr": "sr",  # Serbian
    "sw": "sw",  # Swahili
    "tr": "tr",  # Turkish
    "uk": "uk",  # Ukrainian
}

# User agent for Googlebot
HEADERS = {
    #"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" # gitbook returns 403
}

def fetch_sitemap(url):
    """Fetch and return the contents of a sitemap."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text

# def check_url_exists(url):
#     """Check if a URL exists using a HEAD request."""
#     try:
#         r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=30)
#         return r.status_code == 200
#     except Exception:
#         return False

def prettify_xml(element):
    """Prettify and return a string representation of the XML."""
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def encode_url(url):
    """Encode the URL to make it XML-safe and RFC-compliant."""
    return quote(url, safe=":/?&=")  # Leave common URL-safe characters untouched

def add_static_urls(root, urls):
    """Add static URLs to the sitemap."""
    for url in urls:
        url_element = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')

        loc = ET.SubElement(url_element, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc.text = encode_url(url)

        # Add translations for each language
        for lang_code, hreflang in languages.items():
            translated_url = encode_url(f"{url}/{lang_code}")
            alt_link = ET.SubElement(url_element, '{http://www.w3.org/1999/xhtml}link')
            alt_link.set('rel', 'alternate')
            alt_link.set('hreflang', hreflang)
            alt_link.set('href', translated_url)

        root.append(url_element)

def main():
    # URLs of the sitemaps
    book_sitemap_url = "https://book.hacktricks.xyz/sitemap.xml"
    cloud_sitemap_url = "https://cloud.hacktricks.xyz/sitemap.xml"

    # Fetch both sitemaps
    book_sitemap_data = fetch_sitemap(book_sitemap_url)
    cloud_sitemap_data = fetch_sitemap(cloud_sitemap_url)

    # Parse XML
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    book_root = ET.fromstring(book_sitemap_data)
    cloud_root = ET.fromstring(cloud_sitemap_data)

    all_urls = book_root.findall('ns:url', ns) + cloud_root.findall('ns:url', ns)

    # Prepare the output sitemap
    ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace('xhtml', "http://www.w3.org/1999/xhtml")
    new_root = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')

    seen_locs = set()
    url_entries = []  # Store info for each main URL

    # Add static entry for https://www.hacktricks.xyz/
    static_url = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')
    loc = ET.SubElement(static_url, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    loc.text = encode_url("https://www.hacktricks.xyz/")
    new_root.append(static_url)

    # Add static URLs for training.hacktricks.xyz
    static_training_urls = [
        "https://training.hacktricks.xyz/",
        "https://training.hacktricks.xyz/courses/arte",
        "https://training.hacktricks.xyz/courses/arta",
        "https://training.hacktricks.xyz/courses/grte",
        "https://training.hacktricks.xyz/courses/grta",
        "https://training.hacktricks.xyz/bundles",
        "https://training.hacktricks.xyz/signin",
        "https://training.hacktricks.xyz/signup",
        "https://training.hacktricks.xyz/contact",
        "https://training.hacktricks.xyz/faqs",
        "https://training.hacktricks.xyz/terms",
        "https://training.hacktricks.xyz/privacy",
    ]
    add_static_urls(new_root, static_training_urls)

    # Process main URLs
    for url_element in tqdm(all_urls, desc="Processing URLs"):
        loc = url_element.find('ns:loc', ns)
        if loc is None:
            continue
        loc_text = loc.text.strip()

        if loc_text in seen_locs:
            continue
        seen_locs.add(loc_text)

        priority = url_element.find('ns:priority', ns)
        lastmod = url_element.find('ns:lastmod', ns)

        # Encode the base loc_text
        loc_text = encode_url(loc_text)

        # Determine base domain and path
        parts = loc_text.split("/")
        if len(parts) > 3:
            base_domain_parts = parts[:3]
            page_path = "/".join(parts[3:])
        else:
            base_domain_parts = parts[:3]
            page_path = ""

        base_domain = "/".join(base_domain_parts)

        # Construct all translation URLs for this loc
        translation_urls = {}
        for lang_code, hreflang in languages.items():
            if page_path:
                translated_url = f"{base_domain}/{lang_code}/{page_path}"
            else:
                # If original was just the root, translated is also root + /lang
                translated_url = f"{base_domain}/{lang_code}"
            translation_urls[hreflang] = encode_url(translated_url)

        url_entries.append((
            loc_text,
            priority.text if priority is not None else None,
            lastmod.text if lastmod is not None else None,
            translation_urls
        ))

    # Build the final sitemap
    for (loc_text, priority_val, lastmod_val, translation_urls) in url_entries:
        new_url = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')

        loc_el = ET.SubElement(new_url, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc_el.text = loc_text

        if priority_val:
            priority_el = ET.SubElement(new_url, '{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
            priority_el.text = priority_val

        if lastmod_val:
            lastmod_el = ET.SubElement(new_url, '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            lastmod_el.text = lastmod_val

        # Add all translations (assume all exist for now)
        for hreflang, t_url in translation_urls.items():
            alt_link = ET.SubElement(new_url, '{http://www.sitemaps.org/schemas/sitemap/0.9}link')
            alt_link.set('rel', 'alternate')
            alt_link.set('hreflang', hreflang)
            alt_link.set('href', t_url)

        new_root.append(new_url)

    # Save prettified XML to file
    beautified_xml = prettify_xml(new_root)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(beautified_xml)

if __name__ == "__main__":
    main()
