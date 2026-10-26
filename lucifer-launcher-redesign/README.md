# Lucifer Launcher UI Redesign Prototype

This is a standalone, landscape-first responsive browser prototype based on the supplied Lucifer Launcher showcase. It opens with a full-screen branded loading sequence, then hands off to Home; landscape uses a compact rail, scenic backgrounds, and angled panels while portrait remains supported. It is not the proprietary native Android launcher and does not launch Minecraft.

## Run

From this folder, serve the files with any static HTTP server. For example:

```bash
python3 -m http.server 4174 --bind 0.0.0.0
```

Then open `http://localhost:4174` locally (Arena preview is exposed on the server's live-preview URL).

## Screens

Home, Profiles, Versions, Mods/Mod Store/Categories, Downloads, Servers, Controls/HUD, Skins, Scenes, Settings, Accounts, Java Runtime, Renderer & Shaders, Memory & Performance, Game Files/Storage, Logs/Troubleshooting, Recent Activity, Notifications, Onboarding/States, Splash, About, and More.

## Honest preview boundaries

- All sample profiles, versions, mod states, progress bars, device statuses, and server entries are mock data.
- Launch, Microsoft authentication, downloads, Java execution, renderer compatibility, GPU queries, and Android file access are not implemented.
- This folder contains static web files only; there is no native Android/Gradle project here to produce an APK.
- Form edits, profile selection, mod switches, scene choice, control dragging, and other local interactions affect only this page/browser session.
- No account credentials or user data are collected.
