# Telegram Sticker Pack Downloader

Downloads Telegram sticker packs and converts them to various formats.

## Installation

1. Requires Python 3.6+. Install dependencies:
```bash
pip install requests python-dotenv tqdm Pillow
```

2. Create `.env` file with your Telegram bot token:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
```

To get a token:
- Message [@BotFather](https://t.me/BotFather)
- Send `/newbot`
- Follow prompts
- Copy provided token

## Basic Usage

Download sticker pack:
```bash
python sticker_downloader.py https://t.me/addstickers/packname
```

Convert formats while downloading:
```bash
# Convert static stickers to PNG
python sticker_downloader.py https://t.me/addstickers/packname --static-format PNG

# Convert animated stickers to Lottie JSON
python sticker_downloader.py https://t.me/addstickers/packname --convert-tgs

# Convert both
python sticker_downloader.py https://t.me/addstickers/packname --convert-tgs --static-format PNG
```

## Supported Formats

Static stickers:
- `WEBP` - Default format, maintains transparency
- `PNG` - Lossless with transparency
- `JPEG` - Smallest file size, no transparency

Animated stickers:
- `TGS` - Default format
- `JSON` - Lottie format (web-compatible)

## Output Structure
```
downloads/
└── Pack Name/
    ├── pack_info.txt    # Pack details
    ├── 001_👋.png      # Static sticker
    ├── 002_😊.webp     # Static sticker (original)
    └── 003_🎉.json     # Animated sticker (if converted)
```

## Command Arguments
```
Required:
<sticker_pack_url>        Pack URL from Telegram

Optional:
--static-format FORMAT    Convert static stickers (WEBP/PNG/JPEG)
--convert-tgs            Convert animated stickers to Lottie JSON
```

## Error Handling
- Failed conversions retain original format
- Failed downloads are skipped
- Progress bar shows current status

## Common Issues

If you get "Token not found":
- Check `.env` file exists
- Verify token format
- Ensure `.env` is in script directory

If downloads fail:
- Check internet connection
- Verify pack URL is correct
- Confirm pack is public

## License
MIT
