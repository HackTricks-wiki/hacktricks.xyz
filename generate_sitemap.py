import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

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

def check_url_exists(url):
    """Check if a URL exists using a HEAD request."""
    try:
        r = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=30)
        return r.status_code == 200
    except Exception:
        return False

def prettify_xml(element):
    """Prettify and return a string representation of the XML."""
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

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
    loc.text = "https://www.hacktricks.xyz/"
    new_root.append(static_url)

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
            translation_urls[hreflang] = translated_url

        url_entries.append((
            loc_text,
            priority.text if priority is not None else None,
            lastmod.text if lastmod is not None else None,
            translation_urls
        ))

    # Parallel check all translation URLs with progress bar
    all_translation_checks = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks to executor
        future_to_url = {executor.submit(check_url_exists, t_url): (hreflang, t_url) 
                         for _, _, _, t_urls in url_entries for hreflang, t_url in t_urls.items()}

        # Use tqdm to show progress
        for future in tqdm(as_completed(future_to_url), total=len(future_to_url), desc="Checking Translation URLs"):
            hreflang, t_url = future_to_url[future]
            result = future.result()
            all_translation_checks[t_url] = result

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

        # Add existing translations (excluding English, which is default)
        for hreflang, t_url in translation_urls.items():
            if all_translation_checks.get(t_url, False):
                alt_link = ET.SubElement(new_url, '{http://www.w3.org/1999/xhtml}link')
                alt_link.set('rel', 'alternate')
                alt_link.set('hreflang', hreflang)
                alt_link.set('href', t_url)
            else:
                # Print in red if not found
                print("\033[31m" + f"{t_url} NOT FOUND" + "\033[0m")

        new_root.append(new_url)

    # Save prettified XML to file
    beautified_xml = prettify_xml(new_root)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(beautified_xml)

if __name__ == "__main__":
    main()
