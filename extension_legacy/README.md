# ScholarStream Copilot Browser Extension

Your AI-powered assistant for scholarship and hackathon applications.

## Features

- **Auto-Fill Forms**: Automatically fills out scholarship and hackathon application forms with your saved profile information
- **Smart Field Detection**: Intelligently detects form fields (name, email, GPA, essays, etc.)
- **Application Tracking**: Tracks all applications you start and syncs with your ScholarStream dashboard
- **Essay Assistant**: Get AI-powered help with essay questions (coming soon)
- **Document Management**: Store and reuse transcripts, resumes, and recommendation letters (coming soon)

## Installation (Development)

1. Clone the ScholarStream repository
2. Navigate to `chrome://extensions` in Google Chrome
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the `extension` folder from this repository

## Usage

1. **Log in to ScholarStream**: Visit [scholarstream.app](https://scholarstream.app) and complete your profile
2. **Navigate to an Application**: Go to any scholarship or hackathon application page (e.g., Devpost, Scholarships.com, MLH)
3. **Click the Copilot Button**: A floating ScholarStream button will appear in the bottom-right corner
4. **Auto-Fill**: Click "Auto-Fill Form" to automatically populate detected fields with your profile information
5. **Track Progress**: Your application will be automatically tracked in your dashboard

## Supported Websites

- Devpost (hackathons)
- MLH (Major League Hacking)
- Scholarships.com
- Fastweb
- Niche
- College Board
- And many more!

## Privacy & Security

- All profile data is stored locally in your browser
- No data is shared with third parties
- End-to-end encryption for sensitive information
- You control what information is auto-filled

## Development

### File Structure

```
extension/
├── manifest.json       # Extension configuration
├── content.js         # Main content script (auto-fill logic)
├── background.js      # Background service worker
├── copilot.css       # Copilot UI styles
├── popup.html        # Extension popup interface
├── popup.js          # Popup logic
└── icons/            # Extension icons (16x16, 48x48, 128x128)
```

### Building for Production

1. Update version in `manifest.json`
2. Test all features thoroughly
3. Create a ZIP file of the extension folder
4. Submit to Chrome Web Store

## Coming Soon

- Firefox and Edge support
- AI-powered essay suggestions
- Automatic deadline reminders
- Document OCR and parsing
- Team collaboration features

## Support

For issues or questions:
- Email: support@scholarstream.app
- GitHub: [github.com/scholarstream](https://github.com/scholarstream)
- Discord: [discord.gg/scholarstream](https://discord.gg/scholarstream)

---

**Made with ❤️ by the ScholarStream team**

*Helping students find and win opportunities, one application at a time.*
