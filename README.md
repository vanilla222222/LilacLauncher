# LilacLauncher

A personal Linux desktop hub with a lilac theme. Open Roblox through Sober and Roblox Studio through Vinegar. Search Roblox games with thumbnails and player counts, launch them directly into Sober, save favorites, and mark games as slop to hide them from future results.

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

## Home screen

LilacLauncher opens directly to its own game browser. Search, save games, and hide slop here, then use Play to launch a specific game through Sober. The Hub tab contains the Roblox, Studio, and Executor workspace buttons. Returning Home preserves the current search and filters.

This is a replacement browsing workflow in a separate app; Sober and Roblox's internal home screen are unchanged. Opening Roblox from Hub still opens its normal interface. No custom runtime is bundled.

## Game browser

Search games by keyword, use the category search shortcuts, and load more results. These are Roblox search results, not personalized recommendations or a curated category feed. No Roblox login or cookie is needed for browsing.

Each card has Play, Save, Mark slop, and Hide controls. Mark slop also hides the game. Hidden games stay filtered across searches and restarts; use Hidden games or Show hidden to restore them. Unmarking slop does not automatically restore a game. Saved games and filters are stored on this device in Electron application data, separately from the AppImage. Existing version 0.1 game lists migrate automatically.

Play sends a numeric place ID to the installed Sober Flatpak using a Roblox URI. You must log in through Sober to play. A launch request succeeding does not guarantee joining: Roblox may enforce age restrictions, permissions, purchases, or availability.

Public Roblox search and thumbnail APIs can change or rate limit requests. The browser reports failures and keeps saved games usable offline; launching still needs Roblox connectivity. No credentials are collected. Filtering applies only to LilacLauncher.

## Validation

```bash
npm test
```

Tests cover response parsing, pagination cursors, failed thumbnail requests, rate limits, thumbnail host validation, and launch argument validation. Live API search and thumbnails were checked during development. Actual GUI/AppImage startup and joining through Sober still need verification on Linux Mint. GitHub-hosted builds currently require resolving the account billing block; local builds remain available.

## Executor workspace

The third hub button opens a Luau script editor with a Save draft button. Drafts persist locally across restarts and AppImage replacements. Close or Escape dismisses the editor; save changes explicitly before closing.

No execution backend is connected. Execute is disabled. This is a draft workspace only: no injection, attachment, event inspection, or execution is implemented.

Unaffiliated with Roblox, Sober, or Vinegar.
