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

def prettify_xml(element):
    """Prettify and return a string representation of the XML."""
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def encode_url(url):
    """Encode the URL to make it XML-safe and RFC-compliant."""
    return quote(url, safe=":/?&=")

def add_static_urls_without_translations(root, urls):
    """Add static URLs without translations to the sitemap."""
    for url in urls:
        url_element = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')

        loc = ET.SubElement(url_element, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc.text = encode_url(url)

        root.append(url_element)

def main():
    # Prepare the output sitemap
    ET.register_namespace('', "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace('xhtml', "http://www.w3.org/1999/xhtml")
    new_root = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')

    # Add static URLs without translations
    static_urls = [
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
    add_static_urls_without_translations(new_root, static_urls)

    # Add URLs with translations (Example: book.hacktricks.xyz)
    url_element = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')
    loc = ET.SubElement(url_element, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    loc.text = encode_url("https://book.hacktricks.xyz/")
    priority = ET.SubElement(url_element, '{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
    priority.text = "0.84"
    lastmod = ET.SubElement(url_element, '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
    lastmod.text = "2024-12-14"

    # Add translations
    for hreflang, lang_path in languages.items():
        alt_link = ET.SubElement(url_element, '{http://www.w3.org/1999/xhtml}link')
        alt_link.set('rel', 'alternate')
        alt_link.set('hreflang', hreflang)
        alt_link.set('href', encode_url(f"https://book.hacktricks.xyz/{lang_path}"))

    new_root.append(url_element)

    # Save prettified XML to file
    beautified_xml = prettify_xml(new_root)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(beautified_xml)

if __name__ == "__main__":
    main()
