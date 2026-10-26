# LilacRuntime development source

This is a reproducible development fork of [Cordial](https://github.com/luohoa97/cordial), pinned to `cf8aa92fe0055e652ff0aa8dc01d146979d20d6b` (0.34.0). It is not a newly written compatibility engine and no compiled runtime is supplied yet.

The patch names the shell LilacRuntime and gives its application a separate D-Bus identity. The run script redirects all three XDG file roots to `~/.local/share/lilac-runtime-dev`. Upstream icons, internal crate names, runtime window class, keyring implementation and licence notices remain. This is a source-development setup, not a finished distributable.

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

Verified here: upstream source checkout, patch application/reversal, shell syntax, setup refusal paths, build preflight diagnostics. This environment has no Cargo, Clang, GTK build tools or graphical display. Therefore neither `cargo test --workspace` nor `cargo build --release` could run, and this fork has not launched Roblox. Runtime behaviour is **INFERRED** from the unchanged upstream implementation until tested on Mint.

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

The timestamp patch is diagnostic. It has not been compiled in this environment; actual timing results remain pending a Mint run.
