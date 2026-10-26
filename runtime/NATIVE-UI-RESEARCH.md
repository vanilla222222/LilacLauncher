# Native Home palette investigation

Status: getter vocabulary observed on Mint; payload observation is opt-in and unverified. No panel-colour modification is implemented.

## Established from the supplied Android build

`classes2.dex` declares these methods on `com.roblox.universalapp.systemtheme.JNISystemThemeProtocol`:

| Method | Descriptor | Access flags |
|---|---|---|
| getProtocolName | ()Ljava/lang/String; | 0x109: public static native |
| getSystemThemeParamKey | ()Ljava/lang/String; | 0x109: public static native |
| getSystemThemeSetThemeMessage | ()Ljava/lang/String; | 0x109: public static native |
| getSystemThemeUpdatedMessage | ()Ljava/lang/String; | 0x109: public static native |

Their names also occur in the engine's JNI symbol-name strings. A successful Mint run observed `getProtocolName=SystemTheme`, `getSystemThemeParamKey=SystemTheme`, `getSystemThemeSetThemeMessage=systemThemeSetTheme`, and `getSystemThemeUpdatedMessage=systemThemeUpdated`. The methods describe a message protocol: a getter called getSystemThemeSetThemeMessage is not itself a setter, and it is not evidence of an RGB palette API.

The Android theme package also contains an enum-shaped type with obfuscated fields. Its supported values and message schema are not established by that observation. No method bytecode was decompiled or copied.

The reference real-Android startup trace has no matching system-theme lines. The existing runtime source has no implementation of these four protocol getters. Its webview module already calls a generic JNI shim for exactly this verified static/no-argument/String-returning shape.

## What patch 0009 measures

The patch reads those four getter values through the existing JNI shim at the webview-vocabulary discovery point, after JNI initialisation. It runs only with `LILAC_PROBE_SYSTEM_THEME=1`. It resolves the exact exports, reports missing exports/call failure, and logs only short identifier-shaped values. It does not publish a message, subscribe to account events, modify memory, change the app bundle or bypass integrity validation.

The existing devctl/MCP interface has no theme-vocabulary query; that is why a narrow opt-in runtime probe is needed rather than a separate input harness. This uses the platform protocol surface already employed for webviews and deep links.

## What patch 0010 measures

With the same opt-in, subscribe to only the discovered set/updated channels after the app bridge starts, alongside the existing webview subscriptions. Ask the engine to compose each message ID. Read its cached message too, because startup may publish before the listener is armed. Use the existing per-message subscription shim; clipboard and webview callbacks keep their own entries. No messages are published.

The logger reports JSON structure, recognised theme-related keys, known light/dark/system words and small integers (-1 through 10). Unknown strings, keys and larger numbers are redacted. Non-JSON, oversized and deeply nested payloads are reported without their contents. Event logging stops after 32 callbacks. A successful subscription call is not proof of live delivery. Missing messages do not establish that the protocol is unused or that custom colours are impossible.

The devctl/MCP surface has no theme-message query or subscription, so it cannot collect this measurement. The patch adds no general bus inspection or arbitrary message-sending API.

## Run on Mint

Close existing game/runtime windows first. This research branch builds on the accepted lilac runtime, not the experimental texture generator.

```bash
git fetch origin
git switch native-ui-research
bash runtime/prepare.sh
bash runtime/build.sh
LILAC_PROBE_SYSTEM_THEME=1 bash runtime/run.sh
```

Press Roblox in the shell, allow Home to load, and open Roblox Settings. If Appearance offers light/dark modes, switch between them, then close the game and runtime. The listener does not supply Android theme events from the Linux desktop. Paste only the lines starting with `[lilac-system-theme]`. No key tracing or private runtime-log upload is needed. This probe does not recolour Home.

A failure to find an export means this build exposes less than the static name list suggested. The observed vocabulary establishes only message identifiers. Payloads and behaviour must be observed before sending anything. Ordinary Light/Dark/System routing, if found, would still not establish arbitrary lilac colours.

## Validation and limits

Verified here: DEX method descriptors and access flags, source integration with the existing getter shim, patch application and whitespace. The original getter probe compiled and returned the four identifiers on Mint. The new payload logger has Rust tests for mode preservation, redaction, invalid JSON, size and nesting limits. Cargo is unavailable in this environment: compilation, tests and message delivery for patch 0010 remain **INFERRED/unverified** until run on Mint. No custom palette capability is claimed.
