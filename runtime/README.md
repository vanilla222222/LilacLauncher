# LilacRuntime development source

This is a reproducible development fork of [Cordial](https://github.com/luohoa97/cordial), pinned to `cf8aa92fe0055e652ff0aa8dc01d146979d20d6b` (0.34.0). It is not a newly written compatibility engine and no compiled runtime is supplied yet.

The patch names the shell LilacRuntime and gives its application a separate D-Bus identity. The run script redirects all three XDG file roots to `~/.local/share/lilac-runtime-dev`. On the working baseline, upstream icons, internal crate names, runtime window class, keyring implementation and licence notices remain. The optional theme branch replaces the shell artwork and human-facing labels while keeping internal identifiers and source attribution. This is a source-development setup, not a finished distributable.

## Prepare on Mint 22.x

Install Rust through [rustup](https://rustup.rs), then run `rustup update stable`. The build script selects rustup’s stable toolchain when available, avoiding Mint’s potentially older system Cargo. Without rustup it uses Cargo on PATH and refuses versions older than 1.78, the minimum for the version-4 lockfile. Dependencies can require a newer compiler, so current stable is recommended. Do not downgrade or delete Cargo.lock. Set `LILAC_RUST_TOOLCHAIN` only if deliberately selecting another installed rustup toolchain.

Install native dependencies:

```bash
sudo apt install git build-essential clang cmake pkg-config libgtk-4-dev libadwaita-1-dev libpipewire-0.3-dev libwebkitgtk-6.0-dev
bash runtime/prepare.sh
bash runtime/build.sh
bash runtime/run.sh
```

Preparation clones the pinned upstream source into `runtime/source`, applies the identity patch, and fetches upstream submodules. It refuses a different revision or conflicting patch hunks and preserves edits outside the patched hunks. Rerun preparation after pulling updates to apply any new patches without recloning. The build requires GTK >=4.12 and libadwaita >=1.5, runs workspace tests, then builds the shell and runtime with the shell's WebKit feature. Cargo and the C/C++ build will download dependencies and take substantial disk space. If the dependency compiler requires a newer Rust version, update the toolchain and retry.

The first run needs Roblox's Android build. Use the upstream import controls. For this deliberately separate data setup, manual import is the most predictable: keep your `base.apk` and `split_config.x86_64.apk` together and choose the base APK in Settings → Roblox → Import from a file. The original Sober files must not be moved or edited. The shell's automatic Sober detection has not been tested with redirected XDG roots.

No APKs, Roblox assets or decompiled code belong in this repository. The upstream GPL-3.0-or-later licence and third-party notices are retained in the source checkout. Any future binary distribution must include the corresponding source and required notices.

## What has and has not been verified

Verified here: upstream source checkout, patch application/reversal, shell syntax, setup refusal paths, build preflight diagnostics. This environment has no Cargo, Clang, GTK build tools or graphical display. Therefore neither `cargo test --workspace` nor `cargo build --release` could run, and this fork has not launched Roblox. The development build was subsequently run on Mint/X11: the tester reported working menus and games, then confirmed overlapping movement works after patch 0004. This is user-reported verification, not an independent runtime test here. See [the baseline](BASELINE.md).

AppImage packaging is not configured for this fork yet. Do not run upstream release workflows or publish packages under Cordial's identity; they still refer to its repositories and branding. First get a repeatable source build and successful Home/game session, then adapt packaging.

Roblox Home modification and a Luau executor are not implemented. Owning the runtime source does not remove those separate integration problems. This initial fork does not change client integrity checks or the engine binary.

## Updating an existing source checkout

```bash
git pull
bash runtime/prepare.sh
bash runtime/build.sh
bash runtime/run.sh
```

Preparation skips already applied patches. The diagnostics identity patch fixes `doctor_run::tests::the_desktop_id_is_the_application_id` after the Lilac shell rename. A failed test stops the build before release binaries are produced; do not skip the test suite to get past it.

## Diagnosing delayed movement on X11

Patch 0003 adds server-event and runtime-dispatch timestamps under the existing `CORDIAL_TRACE_KEYS=1` switch. These clocks have different origins: compare the intervals between matching events, not their absolute values. X11 timestamps wrap at 32 bits. A normal event interval compressed at dispatch is evidence of batching before delivery, not proof of its cause. A successful native bridge call is not proof of Roblox applying a key to movement.

Key tracing records key identities, including password keystrokes. Sign in before the test and do not type passwords or chat during it. Run:

```bash
(umask 077; CORDIAL_TRACE_KEYS=1 bash runtime/run.sh 2> /tmp/lilac-keys-private.log)
```

Hold W, add D, release W, then release D. Close the runtime and share only movement events:

```bash
rg '\[cordial\] (x11-key down=[01] evdev=(17|30|31|32|57) |key path=native down=[01] evdev=(17|30|31|32|57) )' /tmp/lilac-keys-private.log
```

The timestamp patch is diagnostic. It has not been compiled in this environment; a Mint trace subsequently showed delayed dispatch of movement-key releases (see patch 0004 below).

## X11 buffered-input fix (patch 0004)

The old input pump returned whenever the X11 socket was unreadable, even if Xlib already held queued input. That is a queue-management bug: XPending and other Xlib calls can move data off the socket into userspace. Patch 0004 removes the socket-only gate and retains XPending before each XNextEvent and the 64-event drain bound.

A movement trace showed release events delayed by approximately 2.4 and 2.9 seconds relative to the fastest observed delivery. Buffered-event starvation is a matching cause from source inspection; after rebuilding with patch 0004, the tester reported that the movement issue was fixed. This is a successful user-reported regression check, not an independently repeated controlled measurement. Timestamp logging can add overhead; use the ordinary untraced build for normal play.

Reference: https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html (Event Queue Management). XPending accounts for events queued inside Xlib; socket readability does not.

Apply with `bash runtime/prepare.sh`, rebuild with `bash runtime/build.sh`, and run normally with `bash runtime/run.sh`. Verified here: sequential patch application, resulting source and whitespace checks. Cargo tests/build could not run here because Cargo is absent. They remain required by build.sh on the development machine.

## Lilac runtime theme experiment

The `runtime-lilac-theme` branch adds theme patch 0005 and corrective patch 0006 after the four baseline patches. Patch 0006 restores the internal `Brand::Cordial` enum references in tests; the displayed product name remains LilacRuntime. It applies a dark lilac GTK/libadwaita palette to the runtime shell, header, settings and transient dialogs, and replaces user-facing shell wording with LilacRuntime. A new flower icon replaces the upstream artwork for source builds. About identifies the developer and upstream contributors; GPL and third-party notices remain in source and the embedded provenance notice is retained. Internal paths, protocol names, crate names and environment variables remain unchanged for compatibility.

```bash
git fetch origin
git switch runtime-lilac-theme
bash runtime/prepare.sh
bash runtime/build.sh
bash runtime/run.sh
```

Close any existing runtime before opening the new build. For a palette comparison, restart with `LILAC_THEME=off bash runtime/run.sh`. That keeps the new labels and artwork but skips the lilac stylesheet and forced dark mode. Baseline source is still available on `runtime-baseline-2026-10-26`.

The CSS targets GTK chrome. It does not recolour Roblox's rendered Home screen or game canvas, and X11's native game window decoration remains managed by Cinnamon. Home-screen work is a separate experiment after this theme is verified.

Validation here: ordered patch application, source/prose audit, preserved licence/provenance files, icon XML and square geometry, and whitespace checks. Cargo and GTK4 are unavailable here, so compilation, CSS parser acceptance and visual appearance remain **INFERRED** until checked on Mint. Inspect the first-run screen, settings, About, profile dialogs, diagnostics and error messages, then run the same movement test as the baseline.

## Theme follow-up (patch 0007)

The follow-up installs the theme during application startup, explicitly colours launch controls, warning banners and window surfaces, and adds modern libadwaita CSS variables only on GTK >=4.16. Older GTK keeps the named-colour stylesheet. The launcher now has a flower, wordmark and lilac launch card. Shared plugin and update-library messages use the fork's product name too. Internal technical identifiers, upstream source credit and licence notices remain.

Startup prints `[lilac-theme] palette v2 active` when that stylesheet is loaded. CSS parsing errors are logged with the same prefix. This confirms loading, not correct rendering. The run script now refuses binaries whose successful-build patch manifest does not match the current source stack, preventing a failed rebuild from silently opening an older executable. After pulling this update, complete `prepare.sh` and `build.sh` before `run.sh`.

Visual verification remains pending a Mint run. This palette themes the GTK shell; Cinnamon-managed native X11 window decorations and Roblox-rendered UI are separate surfaces.

Patch 0008 shortens the Discord application-ID preference description to fit the upstream 200-byte drawable-text limit. The previous 207-byte description caused the built-in plugin to be rejected during consent tests; the error mentioned control characters but the violated condition was length. All built-in preference titles, descriptions, groups and option labels were checked against that byte bound and control-character rule.
