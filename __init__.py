"""
SSH Pilot Plugin: FreeRDP Protocol Backend
"""

from __future__ import annotations

import os
import shutil
from typing import Any, Dict, List

from sshpilot.plugins.api import (
    FieldSpec,
    PluginContext,
    ProtocolBackend,
    ProtocolError,
    SpawnSpec,
    SshPilotPlugin,
)

_RESOLUTIONS = [
    ("640x480", "640x480"),
    ("800x600", "800x600"),
    ("1024x768", "1024x768"),
    ("1280x720", "1280x720 (HD)"),
    ("1280x800", "1280x800"),
    ("1366x768", "1366x768"),
    ("1440x900", "1440x900"),
    ("1600x900", "1600x900 (HD+)"),
    ("1680x1050", "1680x1050"),
    ("1920x1080", "1920x1080 (Full HD)"),
    ("2560x1440", "2560x1440 (2K)"),
    ("3840x2160", "3840x2160 (4K)"),
    ("f", "Fullscreen"),
]

_BPP = [
    ("8", "8-bit (256 colors)"),
    ("15", "15-bit (32K)"),
    ("16", "16-bit (65K)"),
    ("24", "24-bit (16M)"),
    ("32", "32-bit (16M+)"),
]

_SEC = [
    ("", "Automatic"),
    ("rdp", "RDP (Standard RDP Security)"),
    ("tls", "TLS (TLS Encryption)"),
    ("nla", "NLA (Network Level Authentication)"),
    ("ext", "NLA Extended"),
]

_KBD_TYPES = [
    ("", "Automatic"),
    ("4", "IBM PC/XT (83-key)"),
    ("7", "IBM PC/AT (84-key)"),
    ("8", "IBM PC/AT 101/102 (Enhanced)"),
    ("12", "IBM ThinkPad"),
    ("15", "Nokia 9000/9210"),
    ("16", "Windows Mobile/Pocket PC"),
]

_GDI = [
    ("", "Default"),
    ("sw", "Software GDI"),
    ("hw", "Hardware GDI"),
]

_NETWORK = [
    ("", "Automatic"),
    ("modem", "Modem (56 Kbps)"),
    ("broadband-low", "Broadband-Low (256 Kbps - 2 Mbps)"),
    ("broadband-high", "Broadband-High (2-10 Mbps)"),
    ("wan", "WAN (10+ Mbps)"),
    ("lan", "LAN (100+ Mbps)"),
]

_AUDIO_MODE = [
    ("0", "Play on this computer"),
    ("1", "Play on remote computer"),
    ("2", "Do not play"),
]

_CONNECTION_TYPE = [
    ("0", "Automatic"),
    ("1", "Modem"),
    ("2", "Broadband-Low"),
    ("3", "Satellite"),
    ("4", "Broadband-High"),
    ("5", "WAN"),
    ("6", "LAN"),
]

_JPEG_QUALITY = [
    ("", "Default"),
    ("50", "50 - Low quality / small size"),
    ("60", "60"),
    ("70", "70"),
    ("75", "75 - Normal"),
    ("80", "80"),
    ("85", "85"),
    ("90", "90 - High quality"),
    ("95", "95"),
    ("100", "100 - Maximum quality / large size"),
]


class FreeRdpBackend(ProtocolBackend):
    protocol_id = "rdp"
    display_name = "RDP (FreeRDP)"
    default_port = 3389

    def capabilities(self) -> frozenset:
        return frozenset()

    def connection_fields(self) -> List[FieldSpec]:
        return [
            # --- Main ---
            FieldSpec(key="host", label="IP / HOSTNAME", kind="text", required=True,
                      placeholder="hostname or IP address"),
            FieldSpec(key="port", label="Port", kind="int", default=3389),
            FieldSpec(key="username", label="Username", kind="text", required=True,
                      placeholder="username"),
            FieldSpec(key="credential", label="Password", kind="password",
                      placeholder="password"),
            FieldSpec(key="domain", label="Domain", kind="text",
                      placeholder="Windows domain (optional)"),

            # --- Display ---
            FieldSpec(key="resolution", label="Resolution", kind="choice",
                      default="1280x720", choices=_RESOLUTIONS, group="Display"),
            FieldSpec(key="bpp", label="Color depth", kind="choice",
                      default="24", choices=_BPP, group="Display"),
            FieldSpec(key="workarea", label="Work area (fit within usable desktop)",
                      kind="switch", default=False, group="Display"),
            FieldSpec(key="multimon", label="Multi-monitor", kind="switch",
                      default=False, group="Display"),

            # --- Performance ---
            FieldSpec(key="fonts", label="Smooth fonts (ClearType)", kind="switch",
                      default=True, group="Performance"),
            FieldSpec(key="aero", label="Desktop composition", kind="switch",
                      default=False, group="Performance"),
            FieldSpec(key="window_drag", label="Full window drag", kind="switch",
                      default=False, group="Performance"),
            FieldSpec(key="menu_anims", label="Menu animations", kind="switch",
                      default=False, group="Performance"),
            FieldSpec(key="themes", label="Themes", kind="switch",
                      default=False, group="Performance"),
            FieldSpec(key="wallpaper", label="Wallpaper", kind="switch",
                      default=False, group="Performance"),
            FieldSpec(key="gdi", label="GDI rendering", kind="choice",
                      default="", choices=_GDI, group="Performance"),

            # --- Redirection ---
            FieldSpec(key="clipboard", label="Clipboard", kind="switch",
                      default=True, group="Redirection"),
            FieldSpec(key="drives", label="Redirect all drives", kind="switch",
                      default=False, group="Redirection"),
            FieldSpec(key="home_drive", label="Redirect home directory",
                      kind="switch", default=False, group="Redirection"),
            FieldSpec(key="printers", label="Redirect printers", kind="switch",
                      default=False, group="Redirection"),
            FieldSpec(key="smartcards", label="Redirect smartcards", kind="switch",
                      default=False, group="Redirection"),
            FieldSpec(key="serial", label="Serial device to redirect",
                      kind="text", placeholder="/dev/ttyUSB0 (optional)",
                      group="Redirection"),
            FieldSpec(key="sound", label="Audio output", kind="choice",
                      default="0", choices=_AUDIO_MODE, group="Redirection"),
            FieldSpec(key="microphone", label="Audio input (microphone)",
                      kind="switch", default=False, group="Redirection"),

            # --- Security ---
            FieldSpec(key="sec", label="Protocol security", kind="choice",
                      default="", choices=_SEC, group="Security"),
            FieldSpec(key="cert_ignore", label="Ignore certificate errors",
                      kind="switch", default=False, group="Security"),
            FieldSpec(key="cert_name", label="Certificate name", kind="text",
                      default="", group="Security"),

            # --- Gateway ---
            FieldSpec(key="gateway", label="Gateway hostname", kind="text",
                      placeholder="gateway.example.com:443", group="Gateway"),
            FieldSpec(key="gateway_user", label="Gateway username", kind="text",
                      group="Gateway"),
            FieldSpec(key="gateway_domain", label="Gateway domain", kind="text",
                      group="Gateway"),

            # --- Keyboard ---
            FieldSpec(key="kbd_layout", label="Keyboard layout", kind="text",
                      placeholder="e.g. 0x409 or 'US' (optional)",
                      group="Keyboard"),
            FieldSpec(key="kbd_type", label="Keyboard type", kind="choice",
                      default="", choices=_KBD_TYPES, group="Keyboard"),

            # --- Network ---
            FieldSpec(key="network", label="Network connection type", kind="choice",
                      default="", choices=_NETWORK, group="Network"),
            FieldSpec(key="compression", label="Compression", kind="switch",
                      default=True, group="Network"),

            # --- Codecs ---
            FieldSpec(key="rfx", label="RemoteFX", kind="switch",
                      default=False, group="Codecs"),
            FieldSpec(key="nsc", label="NSCodec", kind="switch",
                      default=False, group="Codecs"),
            FieldSpec(key="jpeg", label="JPEG codec", kind="switch",
                      default=False, group="Codecs"),
            FieldSpec(key="jpeg_quality", label="JPEG quality", kind="choice",
                      default="", choices=_JPEG_QUALITY, group="Codecs"),
        ]

    def validate(self, data: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not (data.get("host") or data.get("hostname")):
            errors.append("Host is required.")
        port = data.get("port", 3389)
        if port is None:
            port = 3389
        try:
            if not 0 < int(port) < 65536:
                errors.append("Port must be between 1 and 65535.")
        except (TypeError, ValueError):
            errors.append("Port must be a number.")
        return errors

    def _resolve_rdp_binary(self) -> List[str]:
        flatpak_prefix = ["flatpak-spawn", "--host"] if os.path.exists("/.flatpak-info") else []
        base = flatpak_prefix

        candidates = (
            ["wlfreerdp3", "xfreerdp3"]
            if os.environ.get("WAYLAND_DISPLAY")
            else ["xfreerdp3", "wlfreerdp3"]
        )
        candidates += ["wlfreerdp", "xfreerdp"]

        for name in candidates:
            path = shutil.which(name)
            if path:
                return base + [path]

        raise ProtocolError(
            "Neither 'wlfreerdp3'/'xfreerdp3' nor 'wlfreerdp'/'xfreerdp' is installed. "
            "Install FreeRDP to use RDP connections.")

    def build_spawn(self, connection: Any, ctx: PluginContext) -> SpawnSpec:
        data = getattr(connection, "data", None) or {}
        host = (data.get("host") or data.get("hostname")
                or getattr(connection, "hostname", "")
                or getattr(connection, "host", ""))
        if not host:
            raise ProtocolError("No host configured for this connection.")

        username = data.get("username") or ""
        if not username:
            raise ProtocolError("Username is required.")

        try:
            port = int(data.get("port") or self.default_port)
        except (TypeError, ValueError):
            port = self.default_port

        password = data.get("credential") or ""
        if not password:
            secret_key = f"rdp_password_{connection.nickname}"
            password = ctx.secrets.get(secret_key) or ""

        argv = self._resolve_rdp_binary()
        argv += [f"/v:{host}:{port}", f"/u:{username}"]

        # Domain
        domain = data.get("domain")
        if domain:
            argv.append(f"/d:{domain}")

        # Password
        if password:
            argv.append(f"/p:{password}")

        # Display
        argv.append("/dynamic-resolution")

        resolution = data.get("resolution") or "1280x720"
        if resolution.lower() == "f":
            argv.append("/f")
        else:
            argv.append(f"/size:{resolution}")

        bpp = data.get("bpp")
        if bpp:
            argv.append(f"/bpp:{bpp}")

        if data.get("workarea"):
            argv.append("/workarea")

        if data.get("multimon"):
            argv.append("/multimon")

        # Performance
        if not data.get("fonts"):
            argv.append("-fonts")
        else:
            argv.append("+fonts")

        if data.get("aero"):
            argv.append("+aero")

        if data.get("window_drag"):
            argv.append("+window-drag")

        if data.get("menu_anims"):
            argv.append("+menu-anims")

        if not data.get("themes", False):
            argv.append("-themes")

        if not data.get("wallpaper", False):
            argv.append("-wallpaper")

        gdi = data.get("gdi")
        if gdi:
            argv.append(f"/gdi:{gdi}")

        # Redirection
        if data.get("clipboard", True):
            argv.append("+clipboard")

        if data.get("drives"):
            argv.append("/drives")

        if data.get("home_drive"):
            argv.append("/home-drive")

        if data.get("printers"):
            argv.append("/printer")

        if data.get("smartcards"):
            argv.append("/smartcard")

        serial = data.get("serial")
        if serial:
            argv.append(f"/serial:{serial}")

        sound = data.get("sound", "0")
        if sound != "2":
            argv.append("/sound")
            argv.append(f"/audio-mode:{sound}")

        if data.get("microphone"):
            argv.append("/microphone")

        # Security
        sec = data.get("sec")
        if sec:
            argv.append(f"/sec:{sec}")

        if data.get("cert_ignore"):
            argv.append("/cert-ignore")

        cert_name = data.get("cert_name")
        if cert_name:
            argv.append(f"/cert-name:{cert_name}")

        # Gateway
        gateway = data.get("gateway")
        if gateway:
            argv.append(f"/g:{gateway}")
            gateway_user = data.get("gateway_user")
            if gateway_user:
                argv.append(f"/gu:{gateway_user}")
            gateway_domain = data.get("gateway_domain")
            if gateway_domain:
                argv.append(f"/gd:{gateway_domain}")

        # Keyboard
        kbd_layout = data.get("kbd_layout")
        if kbd_layout:
            argv.append(f"/kbd:{kbd_layout}")

        kbd_type = data.get("kbd_type")
        if kbd_type:
            argv.append(f"/kbd-type:{kbd_type}")

        # Network
        network = data.get("network")
        if network:
            argv.append(f"/network:{network}")

        if not data.get("compression", True):
            argv.append("-compression")

        # Codecs
        if data.get("rfx"):
            argv.append("/rfx")

        if data.get("nsc"):
            argv.append("/nsc")

        if data.get("jpeg"):
            argv.append("/jpeg")

        jpeg_quality = data.get("jpeg_quality")
        if jpeg_quality:
            argv.append(f"/jpeg-quality:{jpeg_quality}")

        return SpawnSpec(argv=argv, env=dict(os.environ))


class Plugin(SshPilotPlugin):
    _PATCHED = False

    def activate(self, ctx: PluginContext) -> None:
        self.ctx = ctx
        ctx.register_protocol(FreeRdpBackend())
        self._patch_connection_dialog()

    def _patch_connection_dialog(self) -> None:
        if Plugin._PATCHED:
            return
        try:
            from sshpilot.connection_dialog import ConnectionDialog

            # 1) При смене протокола — чистим validation_results для скрытых SSH-полей
            _orig_apply = ConnectionDialog._apply_protocol_to_ui

            def _patched_apply(self_obj):
                _orig_apply(self_obj)
                pid = self_obj._selected_protocol_id() if hasattr(self_obj, '_selected_protocol_id') else 'ssh'
                if pid != 'ssh':
                    for k in ('hostname', 'username', 'port'):
                        self_obj.validation_results.pop(k, None)
                    if hasattr(self_obj, '_update_save_buttons'):
                        self_obj._update_save_buttons()

            ConnectionDialog._apply_protocol_to_ui = _patched_apply

            # 2) При стартовой валидации — пропускаем скрытые строки
            _orig_validate = ConnectionDialog._run_initial_validation

            def _patched_validate(self_obj):
                try:
                    for field_name, attr_name in [
                        ('name', 'nickname_row'),
                        ('hostname', 'hostname_row'),
                        ('username', 'username_row'),
                        ('port', 'port_row'),
                    ]:
                        row = getattr(self_obj, attr_name, None)
                        if row is not None and row.get_visible():
                            self_obj._validate_field_row(field_name, row)
                    if hasattr(self_obj, '_update_save_buttons'):
                        self_obj._update_save_buttons()
                except Exception:
                    pass

            ConnectionDialog._run_initial_validation = _patched_validate

            Plugin._PATCHED = True
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to patch ConnectionDialog")

    def deactivate(self) -> None:
        pass
