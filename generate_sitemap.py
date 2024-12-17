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
    "hi": "hi",  # Indian
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

def prettify_xml(element):
    """Prettify and return a string representation of the XML with XML declaration including encoding."""
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    # Specify encoding to include it in the XML declaration
    pretty = reparsed.toprettyxml(indent="  ", encoding="UTF-8")
    # Decode bytes to string for writing to file
    return pretty.decode('UTF-8')

def encode_url(url):
    """Encode the URL to make it XML-safe and RFC-compliant."""
    return quote(url, safe=":/?&=")  # Leave common URL-safe characters untouched

def add_static_urls_without_translations(root, urls):
    """Add static URLs without translations to the sitemap."""
    for url in urls:
        url_element = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        loc = ET.SubElement(url_element, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc.text = encode_url(url)
        root.append(url_element)

def add_translated_urls(url_element, original_url):
    """Add translated URLs with language codes appended to the path, including x-default."""
    # Add x-default hreflang pointing to the original URL
    alt_link_default = ET.SubElement(url_element, '{http://www.w3.org/1999/xhtml}link')
    alt_link_default.set('rel', 'alternate')
    alt_link_default.set('hreflang', 'x-default')
    alt_link_default.set('href', encode_url(original_url))

    # Add hreflang links for each language
    for hreflang, lang_code in languages.items():
        # Add the language code to the path
        path_parts = original_url.split('/', 3)
        if len(path_parts) > 3:  # Ensure there's a path to modify
            translated_url = f"{path_parts[0]}//{path_parts[2]}/{lang_code}/{path_parts[3]}"
        else:  # For root-level paths
            translated_url = f"{original_url}/{lang_code}"
        
        # Create <xhtml:link>
        alt_link = ET.SubElement(url_element, '{http://www.w3.org/1999/xhtml}link')
        alt_link.set('rel', 'alternate')
        alt_link.set('hreflang', hreflang)
        alt_link.set('href', encode_url(translated_url))

def main():
    # URLs of the sitemaps
    book_sitemap_url = "https://book.hacktricks.xyz/sitemap.xml"
    cloud_sitemap_url = "https://cloud.hacktricks.xyz/sitemap.xml"

    # Fetch both sitemaps
    print("Fetching sitemaps...")
    book_sitemap_data = fetch_sitemap(book_sitemap_url)
    cloud_sitemap_data = fetch_sitemap(cloud_sitemap_url)

    # Parse XML
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    print("Parsing sitemaps...")
    book_root = ET.fromstring(book_sitemap_data)
    cloud_root = ET.fromstring(cloud_sitemap_data)

    all_urls = book_root.findall('ns:url', ns) + cloud_root.findall('ns:url', ns)

    # Prepare the output sitemap
    ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace('xhtml', "http://www.w3.org/1999/xhtml")
    new_root = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')

    # Add static URLs for training.hacktricks.xyz without translations
    static_training_urls = [
        "https://www.hacktricks.xyz/",
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
    print("Adding static URLs without translations...")
    add_static_urls_without_translations(new_root, static_training_urls)

    # Process main URLs from book and cloud hacktricks sitemaps
    print("Processing main URLs with translations...")
    for url_element in tqdm(all_urls, desc="Processing URLs"):
        loc = url_element.find('ns:loc', ns)
        if loc is None:
            continue

        loc_text = loc.text.strip()
        priority = url_element.find('ns:priority', ns)
        lastmod = url_element.find('ns:lastmod', ns)

        # Create a new <url> element
        url_entry = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')

        # Add <loc>
        loc_el = ET.SubElement(url_entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc_el.text = encode_url(loc_text)

        # Add <priority> if available
        if priority is not None:
            priority_el = ET.SubElement(url_entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
            priority_el.text = priority.text

        # Add <lastmod> if available
        if lastmod is not None:
            lastmod_el = ET.SubElement(url_entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            lastmod_el.text = lastmod.text

        # Add translations and x-default
        add_translated_urls(url_entry, loc_text)

        new_root.append(url_entry)

    # Save prettified XML to file
    print("Generating prettified XML sitemap...")
    beautified_xml = prettify_xml(new_root)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(beautified_xml)
    with open("sitemap2.xml", "w", encoding="utf-8") as f:
        f.write(beautified_xml)

    print("sitemap.xml has been successfully generated.")

if __name__ == "__main__":
    main()
