# LilacLauncher

A personal Linux desktop hub with a lilac theme. Open Roblox through Sober and Roblox Studio through Vinegar. Keep a local game list, mark games as slop, hide them, and restore them using Show hidden.

## Run the AppImage

Open this repository's Actions tab, select a successful **Build AppImage** run, and download **LilacLauncher-AppImage** under Artifacts. Unzip it, then enable “Allow executing file as program” in the file properties and open the AppImage.

The launcher needs these separate Flatpak apps:

```bash
flatpak install flathub org.vinegarhq.Sober
flatpak install flathub org.vinegarhq.Vinegar
```

Sober already installed? Keep it; no reinstall required. The launcher does not bundle either runtime or Roblox. Missing apps are reported in the hub. Login happens within the upstream apps.

## Development

Node.js 22+ and npm are required.

```bash
npm install
npm start
npm run dist
```

The x86_64 AppImage is written to `dist/`. Build on Linux. The GitHub workflow builds on pushes to main and can also be started manually.

## Current scope

- Roblox and Studio buttons launch the installed Flatpaks.
- The library stores game links and slop/hidden flags locally in Electron's application data. Unmarking slop leaves the game hidden until restored.
- Game entries are currently an organizer; per-game direct launching and custom tag editing are planned.
- Filters apply to this launcher's library, not Roblox's own Discover interface.
- Developer testing tools are planned; no executor or client injection is included.

This is an initial implementation. Real Sober/Vinegar startup and AppImage behavior need verification on Linux Mint; automated packaging does not exercise Roblox or Studio.

Unaffiliated with Roblox, Sober, or Vinegar.
