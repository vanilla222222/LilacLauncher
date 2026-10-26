# Working development baseline

Checkpoint: `runtime-baseline-2026-10-26` in the LilacLauncher repository. This is a source checkpoint, not a packaged release or a general stability guarantee.

The source recipe at `4f553809f608e4d2f3338f1a5bec2eee2b86f1c4` pins Cordial 0.34.0 at `cf8aa92fe0055e652ff0aa8dc01d146979d20d6b` and applies patches 0001–0004. [baseline.json](baseline.json) records each patch's SHA-256.

## Reported working

On Linux Mint 22.3 x86_64 with Cinnamon/X11, Ryzen 5 5500 and Radeon RX 580 2048SP: Roblox Home and menus open, experiences launch, and overlapping movement keys respond correctly after the buffered-X11-input fix. These are tester reports from the actual desktop. The build environment has no Rust toolchain or display and has not independently reproduced them.

The baseline does not establish long-session stability, compatibility on other desktops or hardware, AppImage packaging, native Home modification or script execution. The fork still uses Cordial's compatibility engine. Application files are separated by the development runner; desktop keyring and network identities are not fully isolated.

## Return to this source without discarding current work

Close the running development client. From the current LilacLauncher checkout:

```bash
git fetch origin
git worktree add ../LilacLauncher-baseline origin/runtime-baseline-2026-10-26
cd ../LilacLauncher-baseline
bash runtime/prepare.sh
bash runtime/build.sh
bash runtime/run.sh
```

The separate worktree gets its own upstream source checkout and Cargo target directory. Current source changes stay in the original checkout. The default application data root remains `~/.local/share/lilac-runtime-dev`; the checkpoint does not back up account or settings data. For a separate experimental data root, set `LILAC_RUNTIME_STATE` to a different absolute directory when launching.

Future Home-screen experiments should be developed on a separate branch and leave this checkpoint unchanged.
