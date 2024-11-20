import os
import sys
import requests
import re
import gzip
import json
from PIL import Image
import io
from dotenv import load_dotenv
from urllib.parse import urlparse
from tqdm import tqdm

def sanitize_filename(name):
    """Convert a string to a safe filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace('\n', ' ').replace('\r', ' ')
    return name.strip()[:50]

def extract_pack_name(url):
    """Extract sticker pack name from Telegram URL."""
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    if 'addstickers' in path_parts:
        return path_parts[-1]
    return None

def convert_tgs_to_lottie(tgs_data):
    """Convert TGS file data to Lottie JSON."""
    try:
        json_data = gzip.decompress(tgs_data)
        return json.loads(json_data)
    except Exception as e:
        print(f"Error converting TGS to Lottie: {e}")
        return None

def convert_webp_to_format(webp_data, format_type='WEBP'):
    """Convert WebP file to specified format."""
    try:
        image = Image.open(io.BytesIO(webp_data))
        if format_type == 'JPEG':
            # Convert to RGB for JPEG format
            image = image.convert('RGB')
        output = io.BytesIO()
        image.save(output, format=format_type)
        return output.getvalue()
    except Exception as e:
        print(f"Error converting WebP to {format_type}: {e}")
        return None

def download_sticker_pack(pack_url, convert_tgs=False, static_format='WEBP', base_dir='downloads'):
    """
    Downloads all stickers from a Telegram sticker pack.
    
    Parameters:
    - pack_url: Full URL to the sticker pack
    - convert_tgs: Whether to convert animated stickers to Lottie JSON
    - static_format: Format for static stickers (WEBP, PNG, or JPEG)
    - base_dir: Base directory for downloads
    """
    load_dotenv()
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
        print("Please create a .env file with your bot token. See README.md for instructions.")
        sys.exit(1)

    # Validate static format
    valid_formats = ['WEBP', 'PNG', 'JPEG']
    if static_format.upper() not in valid_formats:
        print(f"Error: Invalid static format. Must be one of: {', '.join(valid_formats)}")
        sys.exit(1)
    
    pack_name = extract_pack_name(pack_url)
    if not pack_name:
        print("Error: Invalid sticker pack URL")
        print("URL should be in format: https://t.me/addstickers/PackName")
        sys.exit(1)
    
    try:
        # Get sticker set information
        api_url = f"https://api.telegram.org/bot{TOKEN}/getStickerSet"
        response = requests.get(api_url, params={'name': pack_name})
        data = response.json()
        
        if not data.get('ok'):
            print(f"Error: {data.get('description', 'Unknown error')}")
            return
        
        # Get pack details
        pack_info = data['result']
        stickers = pack_info['stickers']
        pack_title = pack_info.get('title', pack_name)
        
        # Create directory for this pack
        pack_dir_name = f"{sanitize_filename(pack_title)} ({pack_name})"
        pack_dir = os.path.join(base_dir, pack_dir_name)
        os.makedirs(pack_dir, exist_ok=True)
        
        print(f"\nFound {len(stickers)} stickers in pack: {pack_title}")
        
        # Save pack information
        pack_info_path = os.path.join(pack_dir, 'pack_info.txt')
        with open(pack_info_path, 'w', encoding='utf-8') as f:
            f.write(f"Pack Name: {pack_title}\n")
            f.write(f"Sticker Count: {len(stickers)}\n")
            f.write(f"Original URL: {pack_url}\n")
            if 'author' in pack_info:
                f.write(f"Author: {pack_info['author']}\n")
            f.write(f"Static stickers format: {static_format}\n")
            f.write(f"Animated stickers saved as: {'Lottie JSON' if convert_tgs else 'TGS'}\n")
        
        # Download each sticker with progress bar
        for i, sticker in enumerate(tqdm(stickers, desc="Downloading stickers", unit="sticker")):
            file_id = sticker['file_id']
            emoji = sticker.get('emoji', '')
            
            # Get file path
            file_path_url = f"https://api.telegram.org/bot{TOKEN}/getFile"
            file_data = requests.get(file_path_url, params={'file_id': file_id}).json()
            
            if not file_data.get('ok'):
                tqdm.write(f"Failed to get file path for sticker {i+1}")
                continue
            
            file_path = file_data['result']['file_path']
            
            # Download the actual file
            download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            sticker_data = requests.get(download_url)
            
            if sticker_data.status_code != 200:
                tqdm.write(f"Failed to download sticker {i+1}")
                continue
            
            # Handle file conversion and saving
            is_animated = file_path.endswith('.tgs')
            if is_animated:
                if convert_tgs:
                    # Convert TGS to Lottie JSON
                    lottie_data = convert_tgs_to_lottie(sticker_data.content)
                    if lottie_data:
                        extension = '.json'
                        sticker_content = json.dumps(lottie_data, indent=2).encode('utf-8')
                    else:
                        extension = '.tgs'  # Fallback to original if conversion fails
                        sticker_content = sticker_data.content
                else:
                    extension = '.tgs'
                    sticker_content = sticker_data.content
            else:
                # Handle static sticker conversion
                if static_format.upper() != 'WEBP':
                    converted_data = convert_webp_to_format(sticker_data.content, static_format)
                    if converted_data:
                        extension = f'.{static_format.lower()}'
                        sticker_content = converted_data
                    else:
                        extension = '.webp'  # Fallback to original if conversion fails
                        sticker_content = sticker_data.content
                else:
                    extension = '.webp'
                    sticker_content = sticker_data.content
            
            # Create filename with emoji and number
            emoji_str = emoji if emoji else "sticker"
            filename = f"{i+1:03d}_{sanitize_filename(emoji_str)}{extension}"
            output_path = os.path.join(pack_dir, filename)
            
            # Save the file
            with open(output_path, 'wb') as f:
                f.write(sticker_content)
        
        print(f"\nDownload complete! Stickers saved in: {pack_dir}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sticker_downloader.py <sticker_pack_url> [--convert-tgs] [--static-format FORMAT]")
        print("\nOptions:")
        print("  --convert-tgs              Convert animated stickers to Lottie JSON format")
        print("  --static-format FORMAT     Format for static stickers (WEBP, PNG, or JPEG) [default: WEBP]")
        print("\nExamples:")
        print("  python sticker_downloader.py https://t.me/addstickers/JollySanta")
        print("  python sticker_downloader.py https://t.me/addstickers/JollySanta --convert-tgs")
        print("  python sticker_downloader.py https://t.me/addstickers/JollySanta --static-format PNG")
        print("  python sticker_downloader.py https://t.me/addstickers/JollySanta --convert-tgs --static-format JPEG")
        sys.exit(1)
    
    pack_url = sys.argv[1]
    convert_tgs = '--convert-tgs' in sys.argv
    
    # Get static format if specified
    static_format = 'WEBP'
    if '--static-format' in sys.argv:
        format_index = sys.argv.index('--static-format') + 1
        if format_index < len(sys.argv):
            static_format = sys.argv[format_index].upper()
    
    download_sticker_pack(pack_url, convert_tgs, static_format)

if __name__ == "__main__":
    main()
