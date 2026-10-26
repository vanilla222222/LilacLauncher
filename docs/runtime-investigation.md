# Runtime and actual Roblox Home investigation

Status: static inspection completed; real desktop run pending. No Roblox binaries were patched or executed in the inspection environment. The existing LilacLauncher is separate from this investigation.

## What the uploaded files establish

- `base.apk` has 595 assets and no native libraries.
- `assets/ExtraContent/models/UniversalApp/UniversalApp.rbxm` contains 611 Folder instances, 4,460 ModuleScript instances and six StringValue instances.
- Home and recommendation-related instance names are present. This alone does not identify the active Home implementation.
- ModuleScript Source uses binary property type 0x1d (bytecode), not loose Lua source. SIGN and SIGU chunks are present. The rbx-dom format documentation describes signed client bytecode: https://dom.rojo.space/binary.html . No signature validation or bypass was attempted.
- Companion `_checksum` files exist. A plain SHA-512 of each model did NOT match its companion; their meaning has not been established. Do not treat them as ordinary file checksums.
- `split_config.x86_64.apk` includes a 120,444,968-byte ELF64 x86-64 `libroblox.so`. Its declared dependencies include Android media/audio APIs, Android libc, EGL and GLES.
- A string in the engine references `rbxasset://models/UniversalApp/UniversalApp.rbxm`. This establishes a reference, not an observed load on this build.

## Candidate runtime

Cordial, https://github.com/luohoa97/cordial, has actual source and an existing Android compatibility layer. Its architecture wraps Android interfaces rather than exposing the engine's internal UI. Asset tracing is implemented in `crates/cordial-runtime/src/android/asset.rs` using `CORDIAL_TRACE_ASSETS=1`.

The v0.34.0 release offers an x86-64 AppImage:
https://github.com/luohoa97/cordial/releases/tag/v0.34.0

Review upstream's experimental status and account-compatibility caveats before running it. This project has not audited or tested its release binaries. Our build environment lacks cargo, Clang, GTK development tools, Flatpak, and a display server; it cannot build or run the graphical client here.

## Reproduce on Mint

1. Download the x86-64 Cordial AppImage from the release above, then enable executing it in Properties → Permissions.
2. Start it once. Use **Copy Sober's build** when offered, or **Settings → Roblox → Import from a file**. For manual import, keep `base.apk` and `split_config.x86_64.apk` in the same folder. Cordial maintains its own copy; do not modify Sober's installation.
3. Close Cordial. From this repository run:

```bash
bash tools/trace-home.sh "$HOME/Downloads/Cordial-0.34.0-0-gfe20025-x86_64.AppImage"
```

4. Open Roblox Home, visit Discover/Search, return Home, then close the application.
5. Share only the printed summary or `summary.txt`. The full `runtime-private.log` may contain account or session information; it stays in a private temporary directory and is not committed or uploaded.

The helper does not install software, alter APKs, change integrity settings, or inject scripts. It enables upstream asset logging. Normal runtime startup can create Cordial's own application data.

## What this test can and cannot answer

A UniversalApp asset log would confirm loading the packaged model through the runtime. APP_READY/Home would confirm a corresponding navigation notification. WebView activity alone would NOT prove Home is HTML; login and other screens also use WebViews. Zero counts are inconclusive if tracing or startup failed.

To modify the actual Home interface, we still need an evidence-backed extension point that can add a card action, persist a game blocklist, and filter the displayed feed. Neither APK inspection nor Cordial's plugin system establishes that capability. An independent browser remains the only implemented filtering workflow.
