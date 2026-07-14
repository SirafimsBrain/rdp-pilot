# RDP Pilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

RDP Pilot is a plugin for [SSH Pilot](https://github.com/mfat/sshpilot) that adds Remote Desktop Protocol (RDP) support via FreeRDP.

## Features

- Full RDP protocol support via FreeRDP (xfreerdp / wlfreerdp)
- Declarative connection form (host, port, credentials, display, performance, redirection, security, gateway, keyboard, codecs)
- Portable password storage in connection config (optional system keyring fallback)
- Automatic FreeRDP binary detection (wlfreerdp → xfreerdp, with `3`-suffixed versions)
- Flatpak-aware execution (`flatpak-spawn --host`)
- Dynamic window resize (`/dynamic-resolution`) enabled by default
- All major FreeRDP switches exposed via grouped UI fields

## Requirements

- SSH Pilot (latest)
- FreeRDP 2 or 3 installed (`xfreerdp3`, `wlfreerdp3`, `xfreerdp`, or `wlfreerdp`)
  - Debian/Ubuntu: `apt install freerdp3-x11` (or `freerdp2-x11`)
  - Fedora: `dnf install freerdp` (or `freerdp3`)
  - Arch: `pacman -S freerdp` (or `freerdp3`)
  - macOS: `brew install freerdp`

## Installation

```bash
# Copy the plugin to SSH Pilot's user plugin directory
cp -r rdp-pilot ~/.local/share/sshpilot/plugins/rdp/
```

For Flatpak installations:

```bash
cp -r rdp-pilot ~/.var/app/io.github.mfat.sshpilot/data/sshpilot/plugins/rdp/
```

Then open SSH Pilot → **Settings → Plugins**, enable **RDP** and restart the app.

## Usage

1. Create a new connection or edit an existing one
2. Select **RDP (FreeRDP)** from the protocol dropdown
3. Fill in the required fields:
   - **IP / HOSTNAME** — RDP server address
   - **Username** — login username
   - **Password** — login password (stored in connection config for portability)
4. Adjust optional sections as needed (Display, Performance, Redirection, etc.)

The RDP session opens in a native FreeRDP window, not inside the SSH Pilot terminal tab.

## Connection Fields

| Group        | Fields |
|--------------|--------|
| **Main**     | Host, Port, Username, Password, Domain |
| **Display**  | Resolution, Color depth, Work area, Multi-monitor |
| **Performance** | Smooth fonts, Aero, Window drag, Menu animations, Themes, Wallpaper, GDI |
| **Redirection** | Clipboard, Drives, Home dir, Printers, Smartcards, Serial, Audio |
| **Security** | Protocol security, Certificate ignore, Certificate name |
| **Gateway**  | Gateway hostname, Gateway username, Gateway domain |
| **Keyboard** | Layout, Type |
| **Network**  | Connection type, Compression |
| **Codecs**   | RemoteFX, NSCodec, JPEG, JPEG quality |

## Password Storage

Passwords are stored in `connection.data` under the `credential` key and serialized into SSH Pilot's JSON config. This makes them portable when copying the config between machines.

For backward compatibility, passwords previously saved via the system keyring (`ctx.secrets`) are still supported as a fallback.

## Technical Details

### ProtocolBackend Integration

The plugin implements the `ProtocolBackend` SDK interface:

- **`connection_fields()`** — declares all RDP-specific fields with types, defaults, and grouping
- **`build_spawn()`** — resolves the FreeRDP binary, assembles the full argv from connection data
- **`validate()`** — validates host and port before saving
- **`capabilities()`** — returns empty frozenset (RDP is not an SSH protocol)

### Flatpak Support

When running inside Flatpak, the plugin detects `/.flatpak-info` and prefixes FreeRDP invocations with `flatpak-spawn --host` to access the host system's FreeRDP installation.

### Window Behavior

RDP sessions open in a separate native window (not embedded in the SSH Pilot tab). This provides:
- Full GPU acceleration and minimal input lag
- Correct keyboard focus and system shortcut handling
- Clean lifecycle management (closing the FreeRDP window terminates the session)

## Resources

- [SSH Pilot Plugin SDK](https://github.com/mfat/sshpilot/blob/main/PLUGIN_SDK.md)
- [FreeRDP](https://github.com/FreeRDP/FreeRDP)
- [FreeRDP User Manual](https://github.com/awakecoding/FreeRDP-Manuals/blob/master/User/FreeRDP-User-Manual.markdown)

## License

MIT
