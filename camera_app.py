
import requests
import flet as ft
from datetime import date, timedelta
from urllib.parse import quote

API_BASE_URL = "http://192.168.1.131:2500"

def to_abs_image_url(image_url: str, fallback: str = "") -> str:
    if not image_url:
        return fallback
    image_url = image_url.strip()
    # If it's a local API URL (already proxied or from uploads), return as-is
    if image_url.startswith("/"):
        return f"{API_BASE_URL}{image_url}"
    # If it's already a local API URL, return as-is
    if image_url.startswith(API_BASE_URL):
        return image_url
    # If it's an external URL, route through proxy to avoid CORS issues
    if image_url.startswith(("http://", "https://")):
        # Preserve existing %-escapes to avoid double-encoding (%40 -> %2540)
        return f"{API_BASE_URL}/proxy-image?url={quote(image_url, safe='%')}"
    return f"{API_BASE_URL}{image_url}"

# ── DESIGN TOKENS ──────────────────────────────────────────────────────────────
# Apple-inspired palette — Light surfaces + iOS accent colors
C_NAVY        = "#1D1D1F"   # Header / AppBar background
C_NAVY_MID    = "#2C2C2E"   # Dark card accent
C_NAVY_SOFT   = "#3A3A3C"   # Secondary dark
C_AMBER       = "#76A2D1"   # CTA / Accent (iOS blue)
C_AMBER_DARK  = "#005FCC"
C_AMBER_LIGHT = "#EAF3FF"
C_BG          = "#F5F5F7"   # Page background
C_SURFACE     = "#FFFFFF"   # Card surface
C_SURFACE_2   = "#FBFBFD"   # Slightly off-white
C_BORDER      = "#D2D2D7"
C_TEXT        = "#1D1D1F"   # Primary text
C_MUTED       = "#6E6E73"   # Secondary text
C_MUTED_LIGHT = "#8E8E93"
C_SUCCESS     = "#34C759"   # Available / Active
C_WARNING     = "#FF9F0A"   # Pending
C_DANGER      = "#FF3B30"   # Error / Cancelled / Maintenance
C_INFO        = "#0A84FF"   # Info / Rented
FIT_COVER     = ft.ImageFit.COVER if hasattr(ft, "ImageFit") else ft.BoxFit.COVER


def br_only(top_left=0, top_right=0, bottom_left=0, bottom_right=0):
    if hasattr(ft, "border_radius") and hasattr(ft.border_radius, "only"):
        return ft.border_radius.only(
            top_left=top_left,
            top_right=top_right,
            bottom_left=bottom_left,
            bottom_right=bottom_right,
        )
    return ft.BorderRadius.only(
        top_left=top_left,
        top_right=top_right,
        bottom_left=bottom_left,
        bottom_right=bottom_right,
    )

# Status config
STATUS_CONFIG = {
    "available":    {"color": C_SUCCESS, "bg": "#EAF8EE", "icon": ft.Icons.CHECK_CIRCLE_OUTLINE,   "label": "ว่าง"},
    "rented":       {"color": C_INFO,    "bg": "#EAF3FF", "icon": ft.Icons.LOCK_CLOCK,              "label": "ถูกเช่าแล้ว"},
    "maintenance":  {"color": C_DANGER,  "bg": "#FFEDEA", "icon": ft.Icons.BUILD_CIRCLE_OUTLINED,  "label": "ซ่อมบำรุง"},
    "pending":      {"color": C_WARNING, "bg": "#FFF4E5", "icon": ft.Icons.PENDING_OUTLINED,        "label": "รออนุมัติ"},
    "active":       {"color": C_SUCCESS, "bg": "#EAF8EE", "icon": ft.Icons.PLAY_CIRCLE_OUTLINE,    "label": "กำลังเช่า"},
    "completed":    {"color": C_MUTED,   "bg": "#F2F2F7", "icon": ft.Icons.TASK_ALT,               "label": "คืนแล้ว"},
    "cancelled":    {"color": C_DANGER,  "bg": "#FFEDEA", "icon": ft.Icons.CANCEL_OUTLINED,        "label": "ยกเลิก"},
}

DEPOSIT_CONFIG = {
    "pending":      {"color": C_WARNING, "bg": "#FFF4E5", "label": "รอรับมัดจำ"},
    "paid":         {"color": C_INFO,    "bg": "#EAF3FF", "label": "รับมัดจำแล้ว"},
    "refunded":     {"color": C_SUCCESS, "bg": "#EAF8EE", "label": "คืนมัดจำแล้ว"},
    "confiscated":  {"color": C_DANGER,  "bg": "#FFEDEA", "label": "ริบมัดจำ"},
}

current_user = {"id": None, "username": None, "role": None}


# ── SHARED WIDGETS ──────────────────────────────────────────────────────────────

def status_badge(status: str, config: dict = None, size: int = 10) -> ft.Container:
    cfg = (config or STATUS_CONFIG).get(status.lower(), {"color": C_MUTED, "bg": "#F1F5F9", "label": status.upper()})
    return ft.Container(
        content=ft.Text(cfg["label"], size=size, weight=ft.FontWeight.W_700, color=cfg["color"]),
        bgcolor=cfg["bg"],
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border=ft.border.all(1, cfg["color"] + "44"),
    )

def icon_text_row(icon, text: str, color: str = None, size: int = 12) -> ft.Row:
    return ft.Row(
        [ft.Icon(icon, size=14, color=color or C_MUTED), ft.Text(text, size=size, color=color or C_MUTED)],
        spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

def section_heading(label: str, icon=None) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(width=4, height=18, bgcolor=C_AMBER, border_radius=2),
                ft.Icon(icon, size=16, color=C_NAVY) if icon else ft.Container(),
                ft.Text(label, size=14, weight=ft.FontWeight.W_700, color=C_NAVY),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        margin=ft.Margin(top=12, bottom=6, left=0, right=0),
    )

def divider_line() -> ft.Container:
    return ft.Container(height=1, bgcolor=C_BORDER, margin=ft.Margin(top=6, bottom=6, left=0, right=0))

def stat_chip(label: str, value: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [ft.Text(value, size=20, weight=ft.FontWeight.W_800, color=color),
             ft.Text(label, size=10, color=C_MUTED_LIGHT)],
            spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C_NAVY_MID,
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
    )

def field_style(**kwargs) -> ft.TextField:
    return ft.TextField(
        height=52,
        border_radius=10,
        filled=True,
        bgcolor=C_SURFACE_2,
        border_color=C_BORDER,
        focused_border_color=C_AMBER,
        focused_bgcolor=C_SURFACE,
        content_padding=ft.padding.only(left=14, right=14, top=10),
        text_style=ft.TextStyle(size=13, color=C_TEXT),
        label_style=ft.TextStyle(size=12, color=C_MUTED),
        **kwargs,
    )

def multiline_field(**kwargs) -> ft.TextField:
    return ft.TextField(
        border_radius=10,
        filled=True,
        bgcolor=C_SURFACE_2,
        border_color=C_BORDER,
        focused_border_color=C_AMBER,
        focused_bgcolor=C_SURFACE,
        content_padding=ft.padding.all(14),
        text_style=ft.TextStyle(size=13, color=C_TEXT),
        label_style=ft.TextStyle(size=12, color=C_MUTED),
        **kwargs,
    )

def primary_button(text, on_click=None, icon=None, width=None) -> ft.Button:
    return ft.Button(
        text,
        icon=icon,
        on_click=on_click,
        width=width,
        color=C_NAVY,
        bgcolor=C_AMBER,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            elevation=0,
            text_style=ft.TextStyle(weight=ft.FontWeight.W_700, size=13),
        ),
        height=46,
    )

def danger_button(text, on_click=None, icon=None) -> ft.Button:
    return ft.Button(
        text,
        icon=icon,
        on_click=on_click,
        color=ft.Colors.WHITE,
        bgcolor=C_DANGER,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), elevation=0),
        height=42,
    )

def ghost_button(text, on_click=None, icon=None) -> ft.OutlinedButton:
    style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10),
        side=ft.BorderSide(1.5, C_BORDER),
        color=C_TEXT,
    )
    if icon:
        return ft.OutlinedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=16, color=C_TEXT),
                    ft.Text(text, color=C_TEXT),
                ],
                spacing=6,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=on_click,
            style=style,
            height=42,
        )

    return ft.OutlinedButton(
        text,
        on_click=on_click,
        style=style,
        height=42,
    )

def text_button(text, on_click=None, icon=None) -> ft.TextButton:
    style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10),
        color=C_NAVY,
    )
    if icon:
        return ft.TextButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=16, color=C_NAVY),
                    ft.Text(text, color=C_NAVY),
                ],
                spacing=6,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=on_click,
            style=style,
        )

    return ft.TextButton(
        text,
        on_click=on_click,
        style=style,
    )

def icon_button(icon, on_click=None, color=None) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        on_click=on_click,
        icon_color=color or C_NAVY,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )


# ── EQUIPMENT CARD ─────────────────────────────────────────────────────────────

def equipment_card(eq: dict, on_click=None, on_edit=None, on_delete=None) -> ft.Container:
    status = eq.get("status", "available").lower()
    s_cfg = STATUS_CONFIG.get(status, {"color": C_MUTED, "bg": "#F1F5F9", "label": status, "icon": ft.Icons.CIRCLE_OUTLINED})
    image_src = to_abs_image_url(
        eq.get("primary_image_url") or (eq.get("image_urls") or [""])[0],
        "https://picsum.photos/seed/no-equipment-image/400/260",
    )

    def _on_tap(e):
        if on_click:
            on_click(eq)

    return ft.Container(
        content=ft.Column(
            [
                # ── Image + overlay ──
                ft.Container(
                    height=130,
                    border_radius=br_only(top_left=14, top_right=14),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Stack(
                        [
                            ft.Image(
                                src=image_src,
                                fit=FIT_COVER,
                                height=130,
                            ),
                            # Dark gradient overlay at bottom
                            ft.Container(
                                gradient=ft.LinearGradient(
                                    begin=ft.Alignment(0, -0.2),
                                    end=ft.Alignment(0, 1),
                                    colors=["#00000000", "#CC000000"],
                                ),
                                height=130,
                            ),
                            # Category tag top-left
                            ft.Container(
                                content=ft.Text(
                                    eq.get("category_name", "Camera"),
                                    size=9,
                                    weight=ft.FontWeight.W_700,
                                    color=ft.Colors.WHITE,
                                ),
                                bgcolor="#88000000",
                                border_radius=20,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                margin=8,
                            ),
                            # Status badge top-right
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(s_cfg["icon"], size=11, color=s_cfg["color"]),
                                        ft.Text(s_cfg["label"], size=9, weight=ft.FontWeight.W_700, color=s_cfg["color"]),
                                    ],
                                    spacing=3,
                                ),
                                bgcolor=s_cfg["bg"],
                                border_radius=20,
                                padding=ft.padding.symmetric(horizontal=7, vertical=3),
                                right=8, top=8,
                            ),
                            # Price bottom-left overlay
                            ft.Container(
                                content=ft.Text(
                                    f"฿{eq.get('daily_rate', 0):,.0f}/วัน",
                                    size=13,
                                    weight=ft.FontWeight.W_800,
                                    color=C_AMBER,
                                ),
                                bottom=8, left=10,
                            ),
                        ],
                        expand=True,
                    ),
                ),
                # ── Info section ──
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                eq.get("name", "Unknown"),
                                size=13,
                                weight=ft.FontWeight.W_700,
                                color=C_TEXT,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                [
                                    icon_text_row(ft.Icons.BUSINESS_OUTLINED, eq.get("brand", "-")),
                                    ft.Text("·", color=C_MUTED),
                                    icon_text_row(ft.Icons.QR_CODE_2, eq.get("serial_number", "-")),
                                ],
                                spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        f"มัดจำ ฿{eq.get('deposit_rate', 0):,.0f}",
                                        size=11,
                                        color=C_MUTED,
                                    ),
                                ],
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                ),
            ],
            spacing=0,
        ),
        bgcolor=C_SURFACE,
        border_radius=14,
        border=ft.border.all(1, C_BORDER),
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, offset=ft.Offset(0, 3), color="#10000000"),
        on_click=_on_tap,
        ink=True,
        # Popup menu for admin
        # We add it as overlay in the card via Stack
    )


def equipment_card_full(eq: dict, on_click=None, on_edit=None, on_delete=None) -> ft.Container:
    """List-style card (row) with popup menu for admin"""
    eq_id = eq.get("id")
    status = eq.get("status", "available").lower()
    s_cfg = STATUS_CONFIG.get(status, {"color": C_MUTED, "bg": "#F1F5F9", "label": status})
    image_src = to_abs_image_url(
        eq.get("primary_image_url") or (eq.get("image_urls") or [""])[0],
        "https://picsum.photos/seed/no-equipment-image/120/180",
    )

    return ft.Container(
        content=ft.Row(
            [
                ft.GestureDetector(
                    content=ft.Row(
                        [
                            ft.Container(
                                width=76,
                                height=88,
                                border_radius=10,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Image(
                                    src=image_src,
                                    fit=FIT_COVER,
                                ),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        eq.get("name", "Unknown"),
                                        size=14,
                                        weight=ft.FontWeight.W_700,
                                        color=C_TEXT,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    icon_text_row(ft.Icons.BUSINESS_OUTLINED, eq.get("brand", "-")),
                                    ft.Row(
                                        [
                                            status_badge(status),
                                        ],
                                    ),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                f"฿{eq.get('daily_rate', 0):,.0f}/วัน",
                                                size=13,
                                                weight=ft.FontWeight.W_800,
                                                color=C_AMBER_DARK,
                                            ),
                                            ft.Text(
                                                f"  มัดจำ ฿{eq.get('deposit_rate', 0):,.0f}",
                                                size=11,
                                                color=C_MUTED,
                                            ),
                                        ],
                                        spacing=2,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    on_tap=lambda e: on_click(eq) if on_click else None,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    expand=True,
                ),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row([ft.Icon(ft.Icons.EDIT_OUTLINED, size=16, color=C_NAVY), ft.Text("แก้ไข", color=C_TEXT)], spacing=10),
                            on_click=lambda e: on_edit(eq) if on_edit else None,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row([ft.Icon(ft.Icons.DELETE_OUTLINE, size=16, color=C_DANGER), ft.Text("ลบ", color=C_DANGER)], spacing=10),
                            on_click=lambda e: on_delete(eq_id) if on_delete else None,
                        ),
                    ],
                    icon=ft.Icons.MORE_VERT,
                    icon_color=C_MUTED,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=12),
        bgcolor=C_SURFACE,
        border=ft.border.all(1, C_BORDER),
        border_radius=14,
        shadow=ft.BoxShadow(blur_radius=8, spread_radius=0, offset=ft.Offset(0, 2), color="#0A000000"),
        margin=ft.Margin(top=0, right=0, bottom=10, left=0),
    )


def equipment_card_user(eq: dict, on_click=None) -> ft.Container:
    """Shop-style card for normal users (no admin menu)."""
    status = eq.get("status", "available").lower()
    s_cfg = STATUS_CONFIG.get(status, {"color": C_MUTED, "bg": "#F1F5F9", "label": status})
    img_src = to_abs_image_url(
        eq.get("primary_image_url") or (eq.get("image_urls") or [""])[0],
        "https://picsum.photos/seed/no-equipment-image/320/220",
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    height=122,
                    border_radius=12,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Image(
                        src=img_src,
                        fit=FIT_COVER,
                        height=122,
                    ),
                ),
                ft.Text(
                    eq.get("name", "Unknown"),
                    size=14,
                    weight=ft.FontWeight.W_700,
                    color=C_TEXT,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(eq.get("brand", "-"), size=11, color=C_MUTED),
                ft.Row(
                    [
                        ft.Text(
                            f"฿{eq.get('daily_rate', 0):,.0f}",
                            size=18,
                            weight=ft.FontWeight.W_800,
                            color="#111827",
                        ),
                        ft.Text("/วัน", size=12, color=C_MUTED),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(s_cfg["label"], size=9, weight=ft.FontWeight.W_700, color=s_cfg["color"]),
                            bgcolor=s_cfg["bg"],
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=5,
        ),
        padding=ft.padding.all(10),
        bgcolor=C_SURFACE,
        border_radius=16,
        border=ft.border.all(1, C_BORDER),
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, offset=ft.Offset(0, 3), color="#10000000"),
        on_click=(lambda e: on_click(eq)) if on_click else None,
        ink=True,
    )


# ── MAIN APP ───────────────────────────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "CamRent Pro"
    page.bgcolor = C_BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(font_family="SF Pro Display, Segoe UI")
    try:
        page.window.min_width = 320
        page.window.min_height = 640
    except Exception:
        pass

    equipments = []
    categories = []
    search_text = [""]
    selected_category_id = [None]

    def get_display_username() -> str:
        return current_user.get("username") or "Guest"

    def clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, value))

    def get_viewport_size() -> tuple[int, int]:
        vw = int(page.width or page.window.width or 390)
        vh = int(page.height or page.window.height or 844)
        return max(320, vw), max(560, vh)

    # ── SNACKBAR ────────────────────────────────────────────────────────────────
    snackbar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snackbar)
    active_bottom_sheet = [None]

    def show_snackbar(message, is_error=False):
        snackbar.content = ft.Row(
            [
                ft.Icon(ft.Icons.ERROR_OUTLINE if is_error else ft.Icons.CHECK_CIRCLE_OUTLINE,
                        color=ft.Colors.WHITE, size=18),
                ft.Text(message, color=ft.Colors.WHITE, size=13, expand=True),
            ],
            spacing=8,
        )
        snackbar.bgcolor = C_DANGER if is_error else "#064E3B"
        snackbar.open = True
        page.update()

    def open_dialog(dlg):
        # Use page.dialog directly for better compatibility across Flet runtimes.
        try:
            current_dialog = getattr(page, "dialog", None)
            if current_dialog and current_dialog is not dlg:
                current_dialog.open = False
            page.dialog = dlg
            if hasattr(dlg, "modal"):
                dlg.modal = True
            dlg.open = True
            page.update()
        except Exception as ex:
            show_snackbar(f"เปิดหน้าต่างไม่ได้: {ex}", is_error=True)

    def close_dialog(dlg):
        try:
            dlg.open = False
            if getattr(page, "dialog", None) is dlg:
                page.dialog = None
            page.update()
        except Exception as ex:
            show_snackbar(f"ปิดหน้าต่างไม่ได้: {ex}", is_error=True)

    def open_bottom_sheet(content):
        try:
            bs_cls = getattr(ft, "BottomSheet", None)
            if not bs_cls:
                return False
            try:
                sheet = bs_cls(content=content)
            except TypeError:
                sheet = bs_cls(content)
            if sheet not in page.overlay:
                page.overlay.append(sheet)
            sheet.open = True
            active_bottom_sheet[0] = sheet
            page.update()
            return True
        except Exception:
            return False

    def close_bottom_sheet(e=None):
        try:
            sheet = active_bottom_sheet[0]
            if not sheet:
                return
            sheet.open = False
            page.update()
            active_bottom_sheet[0] = None
        except Exception:
            pass

    # ── AUTH SCREENS ────────────────────────────────────────────────────────────
    def show_login_page():
        username_field    = field_style(hint_text="Username", prefix_icon=ft.Icons.PERSON_OUTLINE)
        password_field    = field_style(hint_text="Password", password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK_OUTLINE)
        email_field       = field_style(hint_text="Email", prefix_icon=ft.Icons.EMAIL_OUTLINED, visible=False)
        phone_field       = field_style(hint_text="เบอร์โทรศัพท์", prefix_icon=ft.Icons.PHONE_OUTLINED, visible=False)
        id_card_field     = field_style(hint_text="เลขบัตรประชาชน 13 หลัก", prefix_icon=ft.Icons.BADGE_OUTLINED, visible=False)
        address_field     = multiline_field(hint_text="ที่อยู่", min_lines=2, max_lines=3, visible=False)
        info_text         = ft.Text("", size=12, color=C_DANGER)
        auth_view_mode    = ["entry"]

        def get_viewport() -> tuple[int, int]:
            return get_viewport_size()

        def get_form_width() -> int:
            w, _ = get_viewport()
            return clamp(int(w) - 24, 292, 620)

        def get_shell_width() -> int:
            vw, _ = get_viewport()
            return vw

        def get_entry_hero_height() -> int:
            _, vh = get_viewport()
            return clamp(int(vh * 0.52), 280, 560)

        def get_auth_header_height() -> int:
            _, vh = get_viewport()
            return clamp(int(vh * 0.27), 170, 250)

        def set_info(msg="", is_error=True):
            info_text.value = msg
            info_text.color = C_DANGER if is_error else C_SUCCESS

        def handle_login(e):
            if not username_field.value or not password_field.value:
                set_info("กรุณากรอก Username และ Password")
                page.update()
                return
            try:
                r = requests.post(f"{API_BASE_URL}/login",
                                  json={"username": username_field.value, "password": password_field.value},
                                  timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    current_user["id"]       = d["user_id"]
                    current_user["username"] = d["username"]
                    current_user["role"]     = d.get("role", "customer")
                    show_main_app()
                else:
                    set_info(r.json().get("detail", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"))
                    page.update()
            except Exception as ex:
                set_info(f"เชื่อมต่อไม่ได้: {ex}")
                page.update()

        def handle_register(e):
            if not username_field.value or not password_field.value or not phone_field.value:
                set_info("กรุณากรอก Username, Password และ เบอร์โทร")
                page.update()
                return
            try:
                r = requests.post(f"{API_BASE_URL}/register", json={
                    "username":       username_field.value,
                    "password":       password_field.value,
                    "email":          email_field.value or None,
                    "phone":          phone_field.value,
                    "id_card_number": id_card_field.value or None,
                    "address":        address_field.value,
                }, timeout=5)
                if r.status_code == 200:
                    set_info("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ", is_error=False)
                    show_auth_screen("login")
                elif r.status_code == 422:
                    errs = [f"• {e['loc'][-1]}: {e['msg']}" for e in r.json().get("detail", [])]
                    set_info("ข้อมูลไม่ถูกต้อง:\n" + "\n".join(errs))
                    page.update()
                else:
                    set_info(r.json().get("detail", "สมัครสมาชิกไม่สำเร็จ"))
                    page.update()
            except Exception as ex:
                set_info(f"เชื่อมต่อไม่ได้: {ex}")
                page.update()

        def handle_guest(e):
            current_user["id"]       = None
            current_user["username"] = "Guest"
            current_user["role"]     = "guest"
            show_main_app()

        def on_auth_resize(e):
            mode = auth_view_mode[0]
            if mode == "entry":
                show_entry_screen()
            elif mode in ("login", "register"):
                show_auth_screen(mode)

        def reset_auth_chrome():
            page.drawer = None
            page.appbar = None
            page.navigation_bar = None
            page.floating_action_button = None
            close_bottom_sheet()

        def show_entry_screen():
            auth_view_mode[0] = "entry"
            fw = get_form_width()
            ww = get_shell_width()
            hero_h = get_entry_hero_height()
            vw, _ = get_viewport()
            hero_title_size = 44 if vw >= 560 else 40 if vw >= 420 else 34
            hero_padding = 36 if vw >= 560 else 30 if vw >= 420 else 22
            reset_auth_chrome()
            page.clean()
            page.bgcolor = C_NAVY
            page.on_resized = on_auth_resize
            page.add(
                ft.SafeArea(
                    expand=True,
                    content=ft.Container(
                        expand=True,
                        bgcolor=C_NAVY,
                        content=ft.Column(
                            [
                                # Hero image
                                ft.Container(
                                    width=ww, height=hero_h,
                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                    content=ft.Stack(
                                        [
                                            ft.Image(
                                                src="https://storage.googleapis.com/fastwork-static/8cd0b1d6-17ca-4c26-a9ca-c907f08f5c61.jpg",
                                                fit=FIT_COVER, width=ww, height=hero_h,
                                            ),
                                            ft.Container(
                                                gradient=ft.LinearGradient(
                                                    begin=ft.Alignment(0, -0.3),
                                                    end=ft.Alignment(0, 1),
                                                    colors=["#00000000", "#CC1D1D1F"],
                                                ),
                                                width=ww, height=hero_h,
                                            ),
                                            ft.Container(
                                                padding=hero_padding,
                                                alignment=ft.Alignment(-1, 1),
                                                content=ft.Column(
                                                    [
                                                        ft.Text("CameraRent ", size=hero_title_size, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                                                        ft.Text("เช่าอุปกรณ์กล้องมืออาชีพ", size=14, color="#D1D1D6"),
                                                    ],
                                                    spacing=4,
                                                ),
                                            ),
                                        ]
                                    ),
                                ),
                                ft.Container(height=24),
                                ft.Button(
                                    "เข้าสู่ระบบ",
                                    width=fw, height=54,
                                    bgcolor=C_AMBER, color=C_NAVY,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=14),
                                        text_style=ft.TextStyle(weight=ft.FontWeight.W_800, size=15),
                                    ),
                                    on_click=lambda e: show_auth_screen("login"),
                                ),
                                ft.OutlinedButton(
                                    "สมัครสมาชิก",
                                    width=fw, height=54,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=14),
                                        side=ft.BorderSide(2, "#636366"),
                                        color=ft.Colors.WHITE,
                                    ),
                                    on_click=lambda e: show_auth_screen("register"),
                                ),
                                ft.TextButton(
                                    "เข้าใช้เป็น Guest",
                                    style=ft.ButtonStyle(color="#8E8E93"),
                                    on_click=handle_guest,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    ),
                )
            )
            page.update()

        def show_auth_screen(mode: str = "login"):
            auth_view_mode[0] = mode
            is_reg = mode == "register"
            email_field.visible    = is_reg
            phone_field.visible    = is_reg
            id_card_field.visible  = is_reg
            address_field.visible  = is_reg
            set_info("")

            fw = get_form_width()
            ww = get_shell_width()
            top_h = get_auth_header_height()
            vw, _ = get_viewport()
            app_title_size = 20 if vw >= 520 else 18 if vw >= 360 else 16
            heading_size = 26 if vw >= 520 else 23 if vw >= 360 else 20
            top_left_pad = 28 if vw >= 420 else 20
            top_top_pad = 18 if vw >= 420 else 14
            for f in [username_field, password_field, email_field, phone_field, id_card_field]:
                f.width = fw
            address_field.width = fw

            title    = "ยินดีต้อนรับกลับ" if not is_reg else "สร้างบัญชีใหม่"
            subtitle = "เข้าสู่ระบบเพื่อจองอุปกรณ์" if not is_reg else "กรอกข้อมูลเพื่อสมัครสมาชิก"

            reset_auth_chrome()
            page.clean()
            page.bgcolor = C_BG
            page.on_resized = on_auth_resize
            page.add(
                ft.SafeArea(
                    expand=True,
                    content=ft.Container(
                        expand=True,
                        bgcolor=C_BG,
                        content=ft.Column(
                            [
                                # Top bar
                                ft.Container(
                                    bgcolor=C_NAVY,
                                    width=ww, height=top_h,
                                    border_radius=br_only(bottom_left=28, bottom_right=28),
                                    padding=ft.padding.only(left=top_left_pad, bottom=24, top=top_top_pad),
                                    content=ft.Column(
                                        [
                                            ft.Row([
                                                ft.Container(
                                                    content=ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, color=C_AMBER, size=28),
                                                    bgcolor="#85252513",
                                                    border_radius=10,
                                                    padding=8,
                                                ),
                                                ft.Text("CameraRent", size=app_title_size, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                                            ], spacing=10),
                                            ft.Container(height=16),
                                            ft.Text(title, size=heading_size, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                                            ft.Text(subtitle, size=12, color="#D1D1D6"),
                                        ],
                                        spacing=4,
                                    ),
                                ),
                                # Form
                                ft.Container(
                                    width=fw,
                                    padding=ft.padding.symmetric(horizontal=0, vertical=20),
                                    content=ft.Column(
                                        [
                                            username_field,
                                            email_field,
                                            password_field,
                                            phone_field,
                                            id_card_field,
                                            address_field,
                                            info_text,
                                            ft.Button(
                                                "เข้าสู่ระบบ" if not is_reg else "สมัครสมาชิก",
                                                width=fw, height=52,
                                                bgcolor=C_AMBER, color=C_NAVY,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(radius=12),
                                                    text_style=ft.TextStyle(weight=ft.FontWeight.W_800, size=14),
                                                ),
                                                on_click=handle_register if is_reg else handle_login,
                                            ),
                                            ft.Row([
                                                text_button("← ย้อนกลับ", on_click=lambda e: show_entry_screen()),
                                                text_button(
                                                    "สมัครสมาชิก" if not is_reg else "เข้าสู่ระบบ",
                                                    on_click=lambda e: show_auth_screen("register" if not is_reg else "login"),
                                                ),
                                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                            text_button("เข้าใช้เป็น Guest →", on_click=handle_guest),
                                        ],
                                        spacing=10,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                ),
                            ],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                )
            )
            page.update()

        show_entry_screen()

    def logout_to_login():
        current_user["id"] = None
        current_user["username"] = None
        current_user["role"] = None
        page.drawer = None
        page.appbar = None
        page.navigation_bar = None
        page.floating_action_button = None
        close_bottom_sheet()
        show_login_page()

    # ── EQUIPMENT SECTION ───────────────────────────────────────────────────────
    eq_view = ft.ListView(expand=True, padding=ft.padding.symmetric(horizontal=16, vertical=12), spacing=12)

    category_chip_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
    category_filter_container = ft.Container(
        content=category_chip_row,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=C_SURFACE,
        border=ft.border.only(bottom=ft.border.BorderSide(1, C_BORDER)),
    )

    category_showcase_row = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
    category_showcase_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("ประเภทอุปกรณ์", size=15, weight=ft.FontWeight.W_800, color=ft.Colors.BLACK87),
                        ft.Container(expand=True),
                        ft.Text("", size=12, color=C_AMBER),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color="#DDDDDD", height=10),
                category_showcase_row,
            ],
            spacing=8,
        ),
        visible=False,
        padding=ft.padding.symmetric(horizontal=12, vertical=12),
        margin=ft.Margin(left=16, right=16, top=8, bottom=6),
        border_radius=16,
        bgcolor="#FFFFFF",
    )

    # Search bar
    search_bar = ft.TextField(
        hint_text="ค้นหาอุปกรณ์...",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        height=46,
        border_radius=10,
        filled=True,
        bgcolor=C_SURFACE,
        border_color=C_BORDER,
        focused_border_color=C_AMBER,
        content_padding=ft.padding.only(left=12, right=12, top=8),
        text_style=ft.TextStyle(size=13),
    )

    search_container = ft.Container(
        content=ft.Row([search_bar], expand=True),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        bgcolor=C_SURFACE,
    )

    equipment_section = ft.Column(
        [search_container, category_showcase_container, category_filter_container, eq_view],
        spacing=0,
        expand=True,
    )

    # Form fields (admin)
    form_category = ft.Dropdown(
        label="หมวดหมู่",
        options=[ft.dropdown.Option("1", "DSLR Camera"), ft.dropdown.Option("2", "Action Camera"),
                 ft.dropdown.Option("3", "เลนส์"), ft.dropdown.Option("4", "อุปกรณ์เสริม")],
        value="1",
        border_radius=10,
        filled=True,
        bgcolor=C_SURFACE_2,
        border_color=C_BORDER,
    )
    form_name    = field_style(label="ชื่ออุปกรณ์")
    form_brand   = field_style(label="แบรนด์")
    form_serial  = field_style(label="Serial Number")
    form_desc    = multiline_field(label="รายละเอียด", min_lines=2, max_lines=4)
    form_daily   = field_style(label="ราคาเช่า/วัน (฿)", keyboard_type=ft.KeyboardType.NUMBER)
    form_deposit = field_style(label="มัดจำ (฿)", keyboard_type=ft.KeyboardType.NUMBER)
    form_image_urls = multiline_field(
        label="รูปภาพ (ใส่ URL/Path ทีละบรรทัด)",
        hint_text="เช่น /uploads/equipments/cam1.jpg หรือ https://...",
        min_lines=3,
        max_lines=6,
    )
    form_primary_image_index = field_style(
        label="ลำดับรูปหลัก (เริ่มที่ 0)",
        value="0",
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    form_status  = ft.Dropdown(
        label="สถานะ",
        options=[ft.dropdown.Option("available", "ว่าง"), ft.dropdown.Option("rented", "ถูกเช่า"), ft.dropdown.Option("maintenance", "ซ่อมบำรุง")],
        value="available",
        border_radius=10,
        filled=True,
        bgcolor=C_SURFACE_2,
        border_color=C_BORDER,
    )
    current_edit = [None]

    def load_equipments():
        try:
            r = requests.get(f"{API_BASE_URL}/equipments", timeout=5)
            r.raise_for_status()
            equipments.clear()
            items = r.json()
            for item in items:
                item["primary_image_url"] = to_abs_image_url(item.get("primary_image_url"))
                item["image_urls"] = [to_abs_image_url(u) for u in item.get("image_urls", [])]
            equipments.extend(items)
            update_list()
        except Exception as ex:
            show_snackbar(f"โหลดข้อมูลไม่ได้: {ex}", is_error=True)

    def load_categories():
        try:
            r = requests.get(f"{API_BASE_URL}/categories", timeout=5)
            r.raise_for_status()
            categories.clear()
            categories.extend(r.json())
            if categories:
                form_category.options = [ft.dropdown.Option(str(c.get("id")), c.get("name", "-")) for c in categories]
                if not form_category.value or form_category.value not in [str(c.get("id")) for c in categories]:
                    form_category.value = str(categories[0].get("id"))
            build_category_chips()
        except Exception as ex:
            show_snackbar(f"โหลดหมวดหมู่ไม่ได้: {ex}", is_error=True)

    def build_category_chips():
        category_chip_row.controls.clear()
        category_showcase_row.controls.clear()

        def category_image_seed(label: str) -> str:
            name = (label or "camera").lower()
            if "dslr" in name:
                return "dslr-camera"
            if "action" in name or "gopro" in name:
                return "action-camera"
            if "compact" in name:
                return "compact-camera"
            if "mirrorless" in name:
                return "mirrorless-camera"
            if "เลนส์" in name or "lens" in name:
                return "lens-photography"
            if "อุปกรณ์" in name or "access" in name:
                return "camera-accessories"
            return f"camera-{name.replace(' ', '-')[:16]}"

        def make_chip(label: str, cid):
            is_sel = selected_category_id[0] == cid
            return ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.WHITE if is_sel else C_NAVY_SOFT),
                bgcolor=C_NAVY if is_sel else C_SURFACE_2,
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
                border=ft.border.all(1, C_BORDER if not is_sel else C_NAVY),
                on_click=lambda e, v=cid: apply_category_filter(v),
                ink=True,
            )

        def make_showcase_item(label: str, cid):
            is_sel = selected_category_id[0] == cid
            category_obj = next((c for c in categories if c.get("id") == cid), None)
            category_image = to_abs_image_url(
                (category_obj or {}).get("image_url"),
                f"https://files.gqthailand.com/uploads/20250911150955.jpg",
            )
            return ft.Container(
                width=168,
                height=92,
                border_radius=12,
                bgcolor="#3F3F46" if not is_sel else "#52525B",
                border=ft.border.all(1.5, C_AMBER if is_sel else "#52525B"),
                padding=ft.padding.only(left=0, right=10, top=0, bottom=0),
                on_click=lambda e, v=cid: apply_category_filter(v),
                ink=True,
                content=ft.Row(
                    [
                        ft.Container(
                            width=72,
                            height=92,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            border_radius=br_only(top_left=12, bottom_left=12),
                            content=ft.Image(
                                src=category_image,
                                fit=FIT_COVER,
                                width=72,
                                height=92,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                label,
                                size=10,
                                weight=ft.FontWeight.W_700,
                                color=ft.Colors.WHITE,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            alignment=ft.Alignment(-1, 0),
                            padding=ft.padding.only(left=8),
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
            )

        category_chip_row.controls.append(make_chip("ทั้งหมด", None))
        for c in categories:
            category_chip_row.controls.append(make_chip(c.get("name", "-"), c.get("id")))

        user_categories = [{"id": None, "name": "ทั้งหมด"}] + [{"id": c.get("id"), "name": c.get("name", "-")} for c in categories]
        for c in user_categories:
            category_showcase_row.controls.append(make_showcase_item(c["name"], c["id"]))

        page.update()

    def apply_category_filter(cid):
        selected_category_id[0] = cid
        build_category_chips()
        update_list()

    def update_list():
        eq_view.controls.clear()
        is_admin = current_user.get("role") == "admin"
        filtered = equipments
        if selected_category_id[0] is not None:
            filtered = [e for e in equipments if e.get("category_id") == selected_category_id[0]]
        q = search_text[0].lower()
        if q:
            filtered = [e for e in filtered if q in e.get("name", "").lower() or q in e.get("brand", "").lower()]

        if not filtered:
            eq_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        [ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=C_MUTED_LIGHT),
                         ft.Text("ไม่พบอุปกรณ์ในหมวดนี้", color=C_MUTED, size=13)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            if is_admin:
                for eq in filtered:
                    eq_view.controls.append(
                        equipment_card_full(eq, on_click=show_details, on_edit=show_edit_page, on_delete=delete_equipment)
                    )
            else:
                for i in range(0, len(filtered), 2):
                    pair = filtered[i:i + 2]
                    row_cards = [
                        ft.Container(expand=True, content=equipment_card_user(eq, on_click=show_details))
                        for eq in pair
                    ]
                    if len(row_cards) == 1:
                        row_cards.append(ft.Container(expand=True))
                    eq_view.controls.append(
                        ft.Row(row_cards, spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
                    )
        page.update()

    def on_search_change(e):
        search_text[0] = search_bar.value or ""
        update_list()
    search_bar.on_change = on_search_change

    # ── RENTAL QUEUE SECTION ─────────────────────────────────────────────────────
    rentals_view = ft.ListView(
        expand=True,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        spacing=12,
    )

    queue_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("คิว")),
            ft.DataColumn(ft.Text("อุปกรณ์")),
            ft.DataColumn(ft.Text("ผู้เช่า")),
            ft.DataColumn(ft.Text("ช่วงวัน")),
            ft.DataColumn(ft.Text("สถานะ")),
            ft.DataColumn(ft.Text("มัดจำ")),
        ],
        rows=[],
        heading_row_color="#E2E8F0",
        data_row_min_height=40,
        data_row_max_height=54,
        horizontal_margin=12,
        column_spacing=18,
    )

    queue_table_container = ft.Container(
        visible=False,
        margin=ft.Margin(left=16, right=16, top=12, bottom=0),
        padding=12,
        border_radius=12,
        bgcolor=C_SURFACE,
        border=ft.border.all(1, C_BORDER),
        content=ft.Column(
            [
                section_heading("ตารางคิวงาน", ft.Icons.TABLE_ROWS_OUTLINED),
                ft.Row([queue_table], scroll=ft.ScrollMode.HIDDEN),
            ],
            spacing=6,
        ),
    )

    # Show queue table as the first item inside rentals_view so everything scrolls together.
    rentals_section = rentals_view

    def refresh_queue_table(rows: list[dict]):
        queue_table.rows.clear()
        for item in rows[:8]:
            status = (item.get("rental_status") or "pending").lower()
            s_cfg = STATUS_CONFIG.get(status, {"label": status, "color": C_MUTED})
            queue_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(item.get("id", "-")), size=11)),
                        ft.DataCell(ft.Text(item.get("equipment_name") or "-", size=11)),
                        ft.DataCell(ft.Text(item.get("username") or "-", size=11)),
                        ft.DataCell(ft.Text(f"{item.get('start_date', '-')} ถึง {item.get('end_date', '-')}", size=11)),
                        ft.DataCell(ft.Text(s_cfg.get("label", status), size=11, color=s_cfg.get("color", C_MUTED))),
                        ft.DataCell(ft.Text(f"฿{float(item.get('deposit_rate') or 0):,.0f}", size=11)),
                    ]
                )
            )

    def fetch_rental_details(rental_id: int):
        r = requests.get(f"{API_BASE_URL}/rentals/{rental_id}/details", timeout=10)
        r.raise_for_status()
        return r.json()

    def build_rental_card(r: dict) -> ft.Container:
        status       = (r.get("rental_status") or "pending").lower()
        dep_status   = (r.get("deposit_status") or "pending").lower()
        s_cfg        = STATUS_CONFIG.get(status, {"color": C_MUTED, "bg": "#F1F5F9", "label": status, "icon": ft.Icons.CIRCLE_OUTLINED})
        d_cfg        = DEPOSIT_CONFIG.get(dep_status, {"color": C_MUTED, "bg": "#F1F5F9", "label": dep_status})
        penalty_val  = float(r.get("penalty_fee") or 0)
        deposit_val  = float(r.get("deposit_rate") or 0)
        rent_total   = float(r.get("total_rent_price") or 0)
        is_admin     = current_user.get("role") == "admin"
        is_owner     = current_user.get("id") == r.get("user_id")
        return_requested = status == "active" and bool(r.get("actual_return_date"))
        can_customer_request_return = (not is_admin) and is_owner and status == "active" and not return_requested
        can_admin_finalize_return = is_admin and status == "active" and return_requested

        # ── Header strip (Navy) ──
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=C_AMBER, size=18),
                            ft.Text(f"คิว #{r.get('id')}", size=14, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                            ft.Text("·", color="#475569"),
                            ft.Text(r.get("equipment_name", "-"), size=13, color="#CBD5E1",
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ],
                        spacing=6,
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [ft.Icon(s_cfg["icon"], size=11, color=s_cfg["color"]),
                             ft.Text(s_cfg["label"], size=10, weight=ft.FontWeight.W_700, color=s_cfg["color"])],
                            spacing=4,
                        ),
                        bgcolor=s_cfg["bg"],
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=9, vertical=4),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=C_NAVY,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=br_only(top_left=14, top_right=14),
        )

        # ── Info rows ──
        notice_controls = []
        if (not is_admin) and status == "active" and return_requested:
            notice_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF_OUTLINED, size=14, color=C_WARNING),
                            ft.Text("ส่งคำขอคืนแล้ว รอแอดมินตรวจสภาพและแจ้งค่าปรับ", size=11, color=C_WARNING),
                        ],
                        spacing=6,
                    ),
                    bgcolor="#FFFBEB",
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    border=ft.border.all(1, "#FDE68A"),
                )
            )
        if (not is_admin) and status == "completed":
            notice_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED, size=14,
                                    color=C_DANGER if penalty_val > 0 else C_SUCCESS),
                            ft.Text(
                                f"แอดมินแจ้งค่าปรับ ฿{penalty_val:,.0f}" if penalty_val > 0 else "แอดมินยืนยันคืนเรียบร้อย ไม่มีค่าปรับ",
                                size=11,
                                color=C_DANGER if penalty_val > 0 else C_SUCCESS,
                            ),
                        ],
                        spacing=6,
                    ),
                    bgcolor="#FEF2F2" if penalty_val > 0 else "#ECFDF5",
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    border=ft.border.all(1, "#FECACA" if penalty_val > 0 else "#A7F3D0"),
                )
            )
        if is_admin and return_requested:
            notice_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.RULE_FOLDER_OUTLINED, size=14, color=C_WARNING),
                            ft.Text("มีคำขอคืนจากลูกค้า รอตรวจสภาพและปิดงาน", size=11, color=C_WARNING),
                        ],
                        spacing=6,
                    ),
                    bgcolor="#FFFBEB",
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    border=ft.border.all(1, "#FDE68A"),
                )
            )

        info_rows = ft.Container(
            content=ft.Column(
                [
                    # Date range
                    ft.Row(
                        [
                            icon_text_row(ft.Icons.PERSON_OUTLINE, r.get("username", "-"), size=12),
                            ft.Container(width=1, height=14, bgcolor=C_BORDER, margin=ft.Margin(left=6, right=6, top=0, bottom=0)),
                            icon_text_row(ft.Icons.CALENDAR_TODAY_OUTLINED,
                                          f"{r.get('start_date', '-')}  →  {r.get('end_date', '-')}", size=12),
                        ],
                        spacing=4,
                        wrap=True,
                    ),
                    divider_line(),

                    # ── Deposit + Finance row ──
                    ft.Row(
                        [
                            # Deposit badge
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("มัดจำ", size=9, color=C_MUTED),
                                        ft.Text(f"฿{deposit_val:,.0f}", size=15,
                                                weight=ft.FontWeight.W_800, color=C_NAVY_MID),
                                        ft.Container(
                                            content=ft.Text(d_cfg["label"], size=9, color=d_cfg["color"],
                                                            weight=ft.FontWeight.W_700),
                                            bgcolor=d_cfg["bg"],
                                            border_radius=10,
                                            padding=ft.padding.symmetric(horizontal=7, vertical=3),
                                        ),
                                    ],
                                    spacing=3,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                bgcolor=C_SURFACE_2,
                                border_radius=10,
                                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                border=ft.border.all(1, C_BORDER),
                                expand=True,
                            ),
                            ft.Container(width=8),
                            # Rent + Penalty
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("ค่าเช่า", size=9, color=C_MUTED),
                                        ft.Text(f"฿{rent_total:,.0f}", size=15,
                                                weight=ft.FontWeight.W_800, color=C_AMBER_DARK),
                                        ft.Text(f"ค่าปรับ ฿{penalty_val:,.0f}" if penalty_val > 0 else "ไม่มีค่าปรับ",
                                                size=9,
                                                color=C_DANGER if penalty_val > 0 else C_MUTED),
                                    ],
                                    spacing=3,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                bgcolor=C_SURFACE_2,
                                border_radius=10,
                                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                border=ft.border.all(1, C_BORDER),
                                expand=True,
                            ),
                        ],
                    ),

                    divider_line(),

                    # ── Condition Before / After ──
                    ft.Row(
                        [
                            ft.Container(
                                expand=True,
                                content=ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Row(
                                                [ft.Icon(ft.Icons.CAMERA_OUTLINED, size=12, color=C_INFO),
                                                 ft.Text("ก่อนเช่า", size=10, weight=ft.FontWeight.W_700, color=C_INFO)],
                                                spacing=4,
                                            ),
                                            ft.Text(
                                                r.get("condition_before") or "ยังไม่บันทึก",
                                                size=11,
                                                color=C_TEXT if r.get("condition_before") else C_MUTED_LIGHT,
                                                max_lines=2,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ],
                                        spacing=3,
                                    ),
                                    bgcolor="#EFF6FF",
                                    border_radius=8,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                                    border=ft.border.all(1, "#BFDBFE"),
                                ),
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                expand=True,
                                content=ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Row(
                                                [ft.Icon(ft.Icons.CAMERA_REAR_OUTLINED, size=12,
                                                         color=C_SUCCESS if r.get("condition_after") else C_MUTED_LIGHT),
                                                 ft.Text("หลังคืน", size=10, weight=ft.FontWeight.W_700,
                                                         color=C_SUCCESS if r.get("condition_after") else C_MUTED_LIGHT)],
                                                spacing=4,
                                            ),
                                            ft.Text(
                                                r.get("condition_after") or "รอตรวจสอบ",
                                                size=11,
                                                color=C_TEXT if r.get("condition_after") else C_MUTED_LIGHT,
                                                max_lines=2,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ],
                                        spacing=3,
                                    ),
                                    bgcolor="#F0FDF4" if r.get("condition_after") else C_SURFACE_2,
                                    border_radius=8,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                                    border=ft.border.all(1, "#BBF7D0" if r.get("condition_after") else C_BORDER),
                                ),
                            ),
                        ],
                    ),
                    *notice_controls,
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
        )

        # ── Action buttons ──
        actions = []

        # Customer actions
        if (not is_admin) and is_owner and status == "pending":
            actions.append(
                danger_button("ยกเลิกคำขอ", icon=ft.Icons.CANCEL_OUTLINED,
                              on_click=lambda e, rid=r.get("id"): cancel_rental_request_action(rid))
            )

        if can_customer_request_return:
            actions.append(
                primary_button("แจ้งคืนอุปกรณ์",
                               icon=ft.Icons.ASSIGNMENT_RETURN_OUTLINED,
                               on_click=lambda e, rr=r: open_return_dialog(rr))
            )
        if can_admin_finalize_return:
            actions.append(
                primary_button("ตรวจรับคืนและแจ้งค่าปรับ",
                               icon=ft.Icons.FACT_CHECK_OUTLINED,
                               on_click=lambda e, rr=r: open_return_dialog(rr))
            )

        # Condition + Detail buttons (always)
        secondary_row = ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=14, color=C_INFO),
                            ft.Text("ระบบนี้ใช้คำอธิบายสภาพแทนการอัปโหลดรูป", size=11, color=C_MUTED),
                        ],
                        spacing=6,
                    ),
                    bgcolor="#EFF6FF",
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    border=ft.border.all(1, "#BFDBFE"),
                ),
                icon_button(ft.Icons.OPEN_IN_NEW, on_click=lambda e, rr=r: show_rental_detail_page(rr), color=C_NAVY),
            ],
            spacing=4,
            wrap=True,
        )

        if is_admin:
            actions.append(
                ghost_button(
                    "ตรวจ/ยืนยันสภาพ",
                    icon=ft.Icons.FACT_CHECK_OUTLINED,
                    on_click=lambda e, rr=r: open_condition_review_dialog(rr),
                )
            )

        # Admin approve/cancel
        admin_row = ft.Row(spacing=8)
        if is_admin:
            admin_row.controls = [
                ft.Button(
                    "อนุมัติ", icon=ft.Icons.CHECK_CIRCLE_OUTLINED,
                    bgcolor=C_SUCCESS, color=ft.Colors.WHITE,
                    disabled=(status != "pending"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    height=42,
                    on_click=lambda e, rid=r.get("id"): update_rental_status_action(rid, "active"),
                ),
                danger_button("ยกเลิก", icon=ft.Icons.CANCEL_OUTLINED,
                              on_click=lambda e, rid=r.get("id"): update_rental_status_action(rid, "cancelled")),
            ]

        actions_container = ft.Container(
            content=ft.Column(
                [secondary_row] + ([ft.Row(actions, wrap=True, spacing=8)] if actions else []) +
                ([admin_row] if is_admin else []),
                spacing=8,
            ),
            padding=ft.padding.only(left=14, right=14, bottom=14),
        )

        return ft.Container(
            content=ft.Column([header, info_rows, actions_container], spacing=0),
            bgcolor=C_SURFACE,
            border_radius=14,
            border=ft.border.all(1, C_BORDER),
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, offset=ft.Offset(0, 3), color="#0A000000"),
        )

    def load_rentals():
        rentals_view.controls.clear()
        if current_user.get("role") == "guest":
            rentals_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        [ft.Icon(ft.Icons.LOCK_OUTLINE, size=48, color=C_MUTED_LIGHT),
                         ft.Text("กรุณาเข้าสู่ระบบเพื่อดูคิวงาน", color=C_MUTED, size=13)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                )
            )
            page.update()
            return

        try:
            endpoint = f"{API_BASE_URL}/rentals"
            if current_user.get("role") != "admin" and current_user.get("id"):
                endpoint = f"{endpoint}?user_id={current_user.get('id')}"
            r = requests.get(endpoint, timeout=8)
            r.raise_for_status()
            rows = r.json()
            refresh_queue_table(rows)

            if not rows:
                rentals_view.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=C_MUTED_LIGHT),
                             ft.Text("ยังไม่มีรายการเช่า", color=C_MUTED, size=13)],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=40,
                        alignment=ft.Alignment(0, 0),
                    )
                )
            else:
                queue_table_container.visible = True
                rentals_view.controls.append(queue_table_container)
                for row in rows:
                    rentals_view.controls.append(build_rental_card(row))
        except Exception as ex:
            show_snackbar(f"โหลดคิวไม่ได้: {ex}", is_error=True)
        page.update()

    # ── RENTAL DETAIL PAGE ──────────────────────────────────────────────────────
    def show_rental_detail_page(rental: dict):
        page.clean()
        page.navigation_bar = None
        page.floating_action_button = None

        _, vh = get_viewport_size()
        timeline_list_h = clamp(int(vh * 0.22), 140, 220)

        summary      = ft.Column(spacing=6)
        log_list     = ft.ListView(expand=False, height=timeline_list_h, spacing=6)
        tx_list      = ft.ListView(expand=False, height=timeline_list_h, spacing=6)

        def render_sections(data: dict):
            rd   = data.get("rental", {})
            fd   = data.get("form") or {}
            logs = data.get("logs", [])
            txs  = data.get("transactions", [])

            dep_status = (rd.get("deposit_status") or "pending").lower()
            d_cfg = DEPOSIT_CONFIG.get(dep_status, {"color": C_MUTED, "bg": C_SURFACE_2, "label": dep_status})
            status = (rd.get("rental_status") or "pending").lower()
            s_cfg = STATUS_CONFIG.get(status, {"color": C_MUTED, "bg": C_SURFACE_2, "label": status, "icon": ft.Icons.CIRCLE_OUTLINED})

            summary.controls = [
                # Queue ID + status
                ft.Row(
                    [
                        ft.Text(f"คิว #{rd.get('id')}", size=22, weight=ft.FontWeight.W_900, color=C_NAVY),
                        status_badge(status),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(rd.get("equipment_name", "-"), size=16, weight=ft.FontWeight.W_700, color=C_TEXT),
                ft.Text(f"ผู้เช่า: {rd.get('username', '-')}", size=12, color=C_MUTED),
                divider_line(),

                # Date info
                section_heading("วันที่เช่า", ft.Icons.CALENDAR_MONTH_OUTLINED),
                ft.Row([
                    icon_text_row(ft.Icons.CALENDAR_TODAY_OUTLINED,
                                  f"{rd.get('start_date')} ถึง {rd.get('end_date')}", size=13),
                ]),
                ft.Row([
                    icon_text_row(ft.Icons.PHONE_OUTLINED, fd.get("contact_phone") or "-", size=12),
                    ft.Container(width=1, height=14, bgcolor=C_BORDER, margin=ft.Margin(left=6, right=6, top=0, bottom=0)),
                    icon_text_row(ft.Icons.PLACE_OUTLINED, fd.get("pickup_location") or "-", size=12),
                ]),

                # ── Deposit / Finance card ──
                section_heading("ระบบมัดจำ & การเงิน", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Column(
                                        [ft.Text("มัดจำ", size=10, color=C_MUTED),
                                         ft.Text(f"฿{rd.get('deposit_rate', 0):,.0f}", size=20,
                                                 weight=ft.FontWeight.W_900, color=C_NAVY)],
                                        spacing=2,
                                    ),
                                    ft.Column(
                                        [ft.Text("ค่าเช่ารวม", size=10, color=C_MUTED),
                                         ft.Text(f"฿{rd.get('total_rent_price', 0):,.0f}", size=20,
                                                 weight=ft.FontWeight.W_900, color=C_AMBER_DARK)],
                                        spacing=2,
                                    ),
                                    ft.Column(
                                        [ft.Text("ค่าปรับ", size=10, color=C_MUTED),
                                         ft.Text(
                                             f"฿{float(rd.get('penalty_fee') or 0):,.0f}",
                                             size=20,
                                             weight=ft.FontWeight.W_900,
                                             color=C_DANGER if float(rd.get('penalty_fee') or 0) > 0 else C_MUTED_LIGHT,
                                         )],
                                        spacing=2,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                            ft.Container(height=8),
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Row(
                                            [ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, size=14, color=d_cfg["color"]),
                                             ft.Text(f"มัดจำ: {d_cfg['label']}", size=11,
                                                     weight=ft.FontWeight.W_700, color=d_cfg["color"])],
                                            spacing=6,
                                        ),
                                        bgcolor=d_cfg["bg"],
                                        border_radius=20,
                                        padding=ft.padding.symmetric(horizontal=12, vertical=5),
                                    ),
                                ],
                            ),
                        ],
                        spacing=4,
                    ),
                    bgcolor=C_NAVY + "08",
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=16, vertical=14),
                    border=ft.border.all(1, C_BORDER),
                ),

                # ── Condition Before / After ──
                section_heading("สภาพอุปกรณ์", ft.Icons.CAMERA_ALT_OUTLINED),
                ft.Row(
                    [
                        ft.Container(
                            expand=True,
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [ft.Icon(ft.Icons.CAMERA_OUTLINED, size=14, color=C_INFO),
                                             ft.Text("ก่อนเช่า", size=11, weight=ft.FontWeight.W_700, color=C_INFO)],
                                            spacing=4,
                                        ),
                                        ft.Text(rd.get("condition_before") or "ยังไม่บันทึก",
                                                size=12,
                                                color=C_TEXT if rd.get("condition_before") else C_MUTED_LIGHT),
                                    ],
                                    spacing=6,
                                ),
                                bgcolor="#EFF6FF",
                                border_radius=10,
                                padding=12,
                                border=ft.border.all(1, "#BFDBFE"),
                            ),
                        ),
                        ft.Container(width=8),
                        ft.Container(
                            expand=True,
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [ft.Icon(ft.Icons.CAMERA_REAR_OUTLINED, size=14,
                                                     color=C_SUCCESS if rd.get("condition_after") else C_MUTED_LIGHT),
                                             ft.Text("หลังคืน", size=11, weight=ft.FontWeight.W_700,
                                                     color=C_SUCCESS if rd.get("condition_after") else C_MUTED_LIGHT)],
                                            spacing=4,
                                        ),
                                        ft.Text(rd.get("condition_after") or "รอตรวจสอบ",
                                                size=12,
                                                color=C_TEXT if rd.get("condition_after") else C_MUTED_LIGHT),
                                    ],
                                    spacing=6,
                                ),
                                bgcolor="#F0FDF4" if rd.get("condition_after") else C_SURFACE_2,
                                border_radius=10,
                                padding=12,
                                border=ft.border.all(1, "#BBF7D0" if rd.get("condition_after") else C_BORDER),
                            ),
                        ),
                    ],
                ),
            ]

            # ── Status Timeline ──
            log_list.controls.clear()
            if logs:
                for i, log in enumerate(reversed(logs)):
                    is_last = i == len(logs) - 1
                    to_status = log.get("to_status", "-")
                    cfg = STATUS_CONFIG.get(to_status, {"color": C_MUTED, "icon": ft.Icons.CIRCLE_OUTLINED, "label": to_status})
                    log_list.controls.append(
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Container(
                                            content=ft.Icon(cfg["icon"], size=16, color=cfg["color"]),
                                            bgcolor=cfg["color"] + "20",
                                            border_radius=20,
                                            padding=6,
                                        ),
                                        ft.Container(width=2, height=20, bgcolor=C_BORDER) if not is_last else ft.Container(),
                                    ],
                                    spacing=2,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            f"{log.get('from_status') or '-'}  →  {to_status}",
                                            size=12, weight=ft.FontWeight.W_700, color=C_TEXT,
                                        ),
                                        ft.Text(log.get("remark") or "-", size=11, color=C_MUTED),
                                        ft.Text(f"โดย: {log.get('changed_by')} | {log.get('changed_at')}",
                                                size=10, color=C_MUTED_LIGHT),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        )
                    )
            else:
                log_list.controls.append(ft.Text("ยังไม่มี log", color=C_MUTED, size=12))

            # ── Deposit Transactions ──
            tx_list.controls.clear()
            if txs:
                for tx in txs:
                    t_type   = tx.get("transaction_type", "-")
                    t_color  = C_SUCCESS if t_type == "refund" else C_DANGER if t_type in ("confiscate", "penalty") else C_INFO
                    t_icon   = ft.Icons.ARROW_DOWNWARD if t_type == "refund" else ft.Icons.ARROW_UPWARD
                    tx_list.controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Icon(t_icon, size=16, color=t_color),
                                        bgcolor=t_color + "20",
                                        border_radius=20,
                                        padding=6,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(t_type.upper(), size=11, weight=ft.FontWeight.W_700, color=t_color),
                                            ft.Text(tx.get("note") or "-", size=11, color=C_MUTED),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    ft.Text(f"฿{float(tx.get('amount', 0)):,.0f}", size=15,
                                            weight=ft.FontWeight.W_800, color=t_color),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=10,
                            bgcolor=C_SURFACE_2,
                            border_radius=10,
                            border=ft.border.all(1, C_BORDER),
                        )
                    )
            else:
                tx_list.controls.append(ft.Text("ยังไม่มีรายการมัดจำ", color=C_MUTED, size=12))

        def refresh_detail(e=None):
            try:
                data = fetch_rental_details(rental.get("id"))
                render_sections(data)
                page.update()
            except Exception as ex:
                show_snackbar(f"โหลดไม่ได้: {ex}", is_error=True)

        page.add(
            ft.Column(
                [
                    ft.AppBar(
                        title=ft.Text("รายละเอียดการเช่า", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.W_700),
                        bgcolor=C_NAVY,
                        leading=icon_button(ft.Icons.ARROW_BACK, on_click=lambda e: show_main_app(), color=ft.Colors.WHITE),
                        actions=[icon_button(ft.Icons.REFRESH, on_click=refresh_detail, color=C_AMBER)],
                    ),
                    ft.Container(
                        expand=True,
                        padding=16,
                        content=ft.Column(
                            [
                                summary,
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=C_INFO, size=16),
                                            ft.Text("ระบบนี้บันทึกสภาพด้วยข้อความและให้แอดมินยืนยันในระบบ", size=12, color=C_MUTED),
                                        ],
                                        spacing=8,
                                    ),
                                    bgcolor="#EFF6FF",
                                    border_radius=10,
                                    border=ft.border.all(1, "#BFDBFE"),
                                    padding=12,
                                ),
                                section_heading("ไทม์ไลน์สถานะ", ft.Icons.TIMELINE_OUTLINED),
                                log_list,
                                section_heading("รายการมัดจำ", ft.Icons.ACCOUNT_BALANCE_OUTLINED),
                                tx_list,
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=4,
                            expand=True,
                        ),
                    ),
                ],
                expand=True,
                spacing=0,
            )
        )
        refresh_detail()

    # ── STATUS UPDATE ────────────────────────────────────────────────────────────
    def update_rental_status_action(rental_id: int, status: str):
        try:
            r = requests.put(
                f"{API_BASE_URL}/rentals/{rental_id}/status",
                json={"rental_status": status, "actor_user_id": current_user.get("id"),
                      "remark": f"Updated by {current_user.get('username')}"},
                timeout=8,
            )
            if r.status_code == 200:
                show_snackbar(f"อัปเดตสถานะเป็น {status} แล้ว", is_error=False)
                load_equipments()
                load_rentals()
            else:
                show_snackbar(r.json().get("detail", "อัปเดตไม่ได้"), is_error=True)
        except Exception as ex:
            show_snackbar(f"เชื่อมต่อไม่ได้: {ex}", is_error=True)

    def cancel_rental_request_action(rental_id: int):
        try:
            r = requests.put(
                f"{API_BASE_URL}/rentals/{rental_id}/cancel-request",
                json={"actor_user_id": current_user.get("id"),
                      "remark": f"Cancelled by {current_user.get('username')}"},
                timeout=8,
            )
            if r.status_code == 200:
                show_snackbar("ยกเลิกคำขอเช่าแล้ว", is_error=False)
                load_equipments()
                load_rentals()
            else:
                show_snackbar(r.json().get("detail", "ยกเลิกไม่ได้"), is_error=True)
        except Exception as ex:
            show_snackbar(f"เชื่อมต่อไม่ได้: {ex}", is_error=True)

    def open_condition_review_dialog(rental: dict):
        is_admin = current_user.get("role") == "admin"
        if not is_admin:
            show_snackbar("เฉพาะแอดมินที่ตรวจ/ยืนยันสภาพได้", is_error=True)
            return

        cond_before = multiline_field(
            label="คำอธิบายสภาพก่อนเช่า",
            value=rental.get("condition_before") or "",
            min_lines=2,
            max_lines=4,
        )
        cond_after = multiline_field(
            label="คำอธิบายสภาพหลังคืน",
            value=rental.get("condition_after") or "",
            min_lines=2,
            max_lines=4,
        )
        review_note = multiline_field(
            label="บันทึกการยืนยันของแอดมิน",
            hint_text="เช่น ตรวจสอบแล้วตรงตามสภาพจริง",
            min_lines=2,
            max_lines=4,
        )

        def go_back(e=None):
            show_main_app()

        def submit(e):
            try:
                resp = requests.put(
                    f"{API_BASE_URL}/rentals/{rental.get('id')}/condition-review",
                    json={
                        "actor_user_id": current_user.get("id"),
                        "condition_before": cond_before.value,
                        "condition_after": cond_after.value,
                        "review_note": review_note.value,
                    },
                    timeout=8,
                )
                if resp.status_code == 200:
                    show_main_app()
                    show_snackbar("แอดมินยืนยันสภาพเรียบร้อย", is_error=False)
                    load_rentals()
                else:
                    show_snackbar(resp.json().get("detail", "บันทึกการตรวจสภาพไม่ได้"), is_error=True)
            except Exception as ex:
                show_snackbar(f"เชื่อมต่อไม่ได้: {ex}", is_error=True)

        page.clean()
        page.navigation_bar = None
        page.floating_action_button = None
        page.appbar = ft.AppBar(
            title=ft.Text("ตรวจ/ยืนยันสภาพอุปกรณ์", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
            bgcolor=C_NAVY,
            leading=icon_button(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE, on_click=go_back),
        )
        page.add(
            ft.Container(
                expand=True,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(f"คิว #{rental.get('id')} - {rental.get('equipment_name', '-')}", size=14, color=C_TEXT),
                        divider_line(),
                        cond_before,
                        cond_after,
                        review_note,
                        ft.Row(
                            [
                                text_button("กลับ", on_click=go_back),
                                primary_button("บันทึกการยืนยัน", icon=ft.Icons.VERIFIED_OUTLINED, on_click=submit),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )
        page.update()

    def open_return_dialog(rental: dict):
        is_admin = current_user.get("role") == "admin"
        if not is_admin and rental.get("actual_return_date"):
            show_snackbar("คุณส่งคำขอคืนไปแล้ว รอแอดมินตรวจสอบ", is_error=True)
            return

        cond_after = multiline_field(
            label="สภาพหลังคืน",
            value=rental.get("condition_after") or "",
            min_lines=2,
            max_lines=4,
            hint_text="เช่น มีรอยขีดข่วนเล็กน้อยที่ฝาหลัง",
        )
        penalty = field_style(label="ค่าปรับ (฿)", value=str(int(float(rental.get("penalty_fee") or 0))), keyboard_type=ft.KeyboardType.NUMBER)
        dep_action = ft.Dropdown(
            label="การจัดการมัดจำ",
            value="refunded",
            options=[ft.dropdown.Option("paid", "รับมัดจำ"),
                     ft.dropdown.Option("refunded", "คืนมัดจำ"),
                     ft.dropdown.Option("confiscated", "ริบมัดจำ")],
            border_radius=10, filled=True, bgcolor=C_SURFACE_2, border_color=C_BORDER,
        )

        def go_back(e=None):
            show_main_app()

        def submit(e):
            try:
                p_val = float(penalty.value or 0)
            except ValueError:
                show_snackbar("ค่าปรับต้องเป็นตัวเลข", is_error=True)
                return
            try:
                payload = {
                    "condition_after": cond_after.value,
                    "penalty_fee": p_val if is_admin else 0,
                    "deposit_action": dep_action.value if is_admin else "paid",
                    "actor_user_id": current_user.get("id"),
                }
                r = requests.put(
                    f"{API_BASE_URL}/rentals/{rental.get('id')}/return",
                    json=payload,
                    timeout=8,
                )
                if r.status_code == 200:
                    show_main_app()
                    show_snackbar(
                        "ปิดงานคืนสำเร็จ และแจ้งค่าปรับให้ลูกค้าแล้ว" if is_admin else "ส่งคำขอคืนสำเร็จ รอแอดมินตรวจสอบ",
                        is_error=False,
                    )
                    load_equipments()
                    load_rentals()
                else:
                    show_snackbar(r.json().get("detail", "คืนไม่ได้"), is_error=True)
            except Exception as ex:
                show_snackbar(f"เชื่อมต่อไม่ได้: {ex}", is_error=True)

        page.clean()
        page.navigation_bar = None
        page.floating_action_button = None
        page.appbar = ft.AppBar(
            title=ft.Text("ตรวจรับคืนอุปกรณ์" if is_admin else "แจ้งคืนอุปกรณ์", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
            bgcolor=C_NAVY,
            leading=icon_button(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE, on_click=go_back),
        )
        page.add(
            ft.Container(
                expand=True,
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ASSIGNMENT_RETURN_OUTLINED, color=C_NAVY, size=22),
                                ft.Text(f"คิว #{rental.get('id')} - {rental.get('equipment_name', '-')}", size=14, weight=ft.FontWeight.W_700),
                            ],
                            spacing=10,
                        ),
                        divider_line(),
                        cond_after,
                        *([penalty, dep_action] if is_admin else []),
                        ft.Row(
                            [
                                text_button("กลับ", on_click=go_back),
                                primary_button("บันทึกการตรวจรับคืน" if is_admin else "ส่งคำขอคืน", icon=ft.Icons.CHECK, on_click=submit),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )
        page.update()

    # ── PROFILE PAGE ────────────────────────────────────────────────────────────
    def show_profile_page(e=None):
        role = current_user.get("role", "guest")
        user_id = current_user.get("id")
        username = current_user.get("username", "Guest")
        vw, _ = get_viewport_size()
        avatar_size = clamp(int(vw * 0.26), 84, 120)
        label_col_w = clamp(int(vw * 0.32), 92, 150)
        is_guest = role == "guest" or not user_id

        username_title = ft.Text(username, size=22, weight=ft.FontWeight.W_800, color=C_TEXT)
        role_title = ft.Text(
            "ผู้ดูแลระบบ" if role == "admin" else "ลูกค้า" if role == "customer" else "Guest",
            size=13,
            color=C_MUTED,
        )
        account_username_value = ft.Text(username or "-", size=13, color=C_TEXT, expand=True)
        account_id_value = ft.Text(str(user_id or "-"), size=13, color=C_TEXT, expand=True)
        account_role_value = ft.Text(
            "ผู้ดูแล" if role == "admin" else "ลูกค้า" if role == "customer" else "Guest",
            size=13,
            color=C_TEXT,
            expand=True,
        )

        username_field = field_style(label="Username")
        email_field = field_style(label="Email")
        phone_field = field_style(label="เบอร์โทรศัพท์", keyboard_type=ft.KeyboardType.PHONE)
        id_card_field = field_style(label="เลขบัตรประชาชน 13 หลัก", keyboard_type=ft.KeyboardType.NUMBER)
        address_field = multiline_field(label="ที่อยู่", min_lines=2, max_lines=3)
        profile_info = ft.Text("", size=12, color=C_MUTED)

        profile_state = {
            "username": username,
            "email": "",
            "phone": "",
            "id_card_number": "",
            "address": "",
            "role": role,
            "user_id": user_id,
        }
        is_editing = [False]

        def set_form_enabled(enabled: bool):
            editable = enabled and (not is_guest)
            for ctrl in [username_field, email_field, phone_field, id_card_field, address_field]:
                ctrl.disabled = not editable

        def update_action_buttons():
            edit_btn.visible = (not is_editing[0]) and (not is_guest)
            save_btn.visible = is_editing[0] and (not is_guest)
            cancel_btn.visible = is_editing[0] and (not is_guest)

        def fill_form_from_state():
            username_field.value = profile_state.get("username") or ""
            email_field.value = profile_state.get("email") or ""
            phone_field.value = profile_state.get("phone") or ""
            id_card_field.value = profile_state.get("id_card_number") or ""
            address_field.value = profile_state.get("address") or ""

            username_title.value = profile_state.get("username") or "Guest"
            role_now = profile_state.get("role") or role
            role_title.value = "ผู้ดูแลระบบ" if role_now == "admin" else "ลูกค้า" if role_now == "customer" else "Guest"
            account_username_value.value = profile_state.get("username") or "-"
            account_id_value.value = str(profile_state.get("user_id") or "-")
            account_role_value.value = "ผู้ดูแล" if role_now == "admin" else "ลูกค้า" if role_now == "customer" else "Guest"

        def load_profile(show_msg: bool = False):
            if is_guest:
                fill_form_from_state()
                profile_info.value = "บัญชี Guest ยังไม่รองรับการแก้ไขข้อมูล"
                return

            try:
                r = requests.get(f"{API_BASE_URL}/users/{user_id}", timeout=6)
                if r.status_code != 200:
                    detail = r.json().get("detail", "โหลดข้อมูลโปรไฟล์ไม่ได้")
                    profile_info.value = detail
                    if show_msg:
                        show_snackbar(detail, is_error=True)
                    return
                data = r.json()
                profile_state.update(
                    {
                        "username": data.get("username") or profile_state.get("username") or username,
                        "email": data.get("email") or "",
                        "phone": data.get("phone") or "",
                        "id_card_number": data.get("id_card_number") or "",
                        "address": data.get("address") or "",
                        "role": data.get("role") or role,
                        "user_id": data.get("user_id") or user_id,
                    }
                )
                current_user["username"] = profile_state["username"]
                current_user["role"] = profile_state["role"]
                fill_form_from_state()
                profile_info.value = ""
                if show_msg:
                    show_snackbar("รีเฟรชข้อมูลโปรไฟล์แล้ว", is_error=False)
            except Exception as ex:
                profile_info.value = f"เชื่อมต่อไม่ได้: {ex}"
                if show_msg:
                    show_snackbar(profile_info.value, is_error=True)

        def start_edit(e):
            is_editing[0] = True
            profile_info.value = "กำลังแก้ไขข้อมูลโปรไฟล์"
            set_form_enabled(True)
            update_action_buttons()
            page.update()

        def cancel_edit(e):
            is_editing[0] = False
            fill_form_from_state()
            profile_info.value = "ยกเลิกการแก้ไขแล้ว"
            set_form_enabled(False)
            update_action_buttons()
            page.update()

        def save_profile(e):
            payload = {
                "username": (username_field.value or "").strip(),
                "email": (email_field.value or "").strip() or None,
                "phone": (phone_field.value or "").strip() or None,
                "id_card_number": (id_card_field.value or "").strip() or None,
                "address": (address_field.value or "").strip() or None,
            }

            if not payload["username"]:
                profile_info.value = "Username ห้ามว่าง"
                page.update()
                return

            if payload["phone"] is None:
                profile_info.value = "เบอร์โทรศัพท์ห้ามว่าง"
                page.update()
                return

            try:
                r = requests.put(f"{API_BASE_URL}/users/{user_id}", json=payload, timeout=8)
                if r.status_code != 200:
                    profile_info.value = r.json().get("detail", "บันทึกข้อมูลไม่ได้")
                    page.update()
                    return

                data = r.json()
                profile_state.update(
                    {
                        "username": data.get("username") or payload["username"],
                        "email": data.get("email") or "",
                        "phone": data.get("phone") or "",
                        "id_card_number": data.get("id_card_number") or "",
                        "address": data.get("address") or "",
                        "role": data.get("role") or role,
                        "user_id": data.get("user_id") or user_id,
                    }
                )
                current_user["username"] = profile_state["username"]
                current_user["role"] = profile_state["role"]

                is_editing[0] = False
                set_form_enabled(False)
                update_action_buttons()
                fill_form_from_state()
                profile_info.value = "บันทึกข้อมูลโปรไฟล์เรียบร้อยแล้ว"
                show_snackbar("บันทึกโปรไฟล์สำเร็จ", is_error=False)
                page.update()
            except Exception as ex:
                profile_info.value = f"เชื่อมต่อไม่ได้: {ex}"
                page.update()

        edit_btn = primary_button("แก้ไขโปรไฟล์", icon=ft.Icons.EDIT_OUTLINED, on_click=start_edit)
        save_btn = primary_button("บันทึกการแก้ไข", icon=ft.Icons.SAVE_OUTLINED, on_click=save_profile)
        cancel_btn = ghost_button("ยกเลิก", icon=ft.Icons.CLOSE, on_click=cancel_edit)
        refresh_btn = ghost_button("รีโหลดข้อมูล", icon=ft.Icons.REFRESH, on_click=lambda e: load_profile(show_msg=True))

        page.clean()
        page.drawer = None
        page.appbar = ft.AppBar(
            title=ft.Text("โปรไฟล์", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
            bgcolor=C_NAVY,
            leading=icon_button(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE,
                               on_click=lambda e: show_main_app()),
        )
        page.navigation_bar = None

        page.add(
            ft.Container(
                expand=True,
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Container(
                                        width=avatar_size,
                                        height=avatar_size,
                                        border_radius=avatar_size // 2,
                                        bgcolor=C_AMBER,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Icon(ft.Icons.PERSON, size=50, color=C_NAVY),
                                    ),
                                    username_title,
                                    role_title,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                            ),
                            padding=20,
                            alignment=ft.Alignment.CENTER,
                        ),
                        divider_line(),
                        ft.Container(
                            padding=20,
                            content=ft.Column(
                                [
                                    section_heading("ข้อมูลบัญชี", ft.Icons.INFO_OUTLINED),
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Row(
                                                    [
                                                        ft.Text("Username", size=12, color=C_MUTED, width=label_col_w),
                                                        account_username_value,
                                                    ],
                                                    spacing=12,
                                                ),
                                                ft.Row(
                                                    [
                                                        ft.Text("ยูเซอร์ ID", size=12, color=C_MUTED, width=label_col_w),
                                                        account_id_value,
                                                    ],
                                                    spacing=12,
                                                ),
                                                ft.Row(
                                                    [
                                                        ft.Text("บทบาท", size=12, color=C_MUTED, width=label_col_w),
                                                        account_role_value,
                                                    ],
                                                    spacing=12,
                                                ),
                                            ],
                                            spacing=10,
                                        ),
                                        bgcolor=C_SURFACE_2,
                                        border_radius=12,
                                        padding=12,
                                        border=ft.border.all(1, C_BORDER),
                                    ),
                                    section_heading("ข้อมูลติดต่อและยืนยันตัวตน", ft.Icons.BADGE_OUTLINED),
                                    username_field,
                                    email_field,
                                    phone_field,
                                    id_card_field,
                                    address_field,
                                    profile_info,
                                    divider_line(),
                                    ft.Row(
                                        [
                                            refresh_btn,
                                            edit_btn,
                                            cancel_btn,
                                            save_btn,
                                            ghost_button("ย้อนกลับ", on_click=lambda e: show_main_app()),
                                            primary_button("ออกจากระบบ", icon=ft.Icons.LOGOUT_OUTLINED,
                                                          on_click=lambda e: logout_to_login()),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        wrap=True,
                                        spacing=10,
                                    ),
                                ],
                                spacing=12,
                                expand=True,
                                scroll=ft.ScrollMode.HIDDEN,
                            ),
                        ),
                    ],
                    expand=True,
                    spacing=0,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )
        )

        fill_form_from_state()
        set_form_enabled(False)
        update_action_buttons()
        load_profile()
        page.update()

    # ── MAIN APP LAYOUT ──────────────────────────────────────────────────────────
    def show_main_app(e=None):
        page.clean()
        page.on_resized = None
        page.bgcolor = C_BG
        role = current_user.get("role", "guest")
        is_admin = role == "admin"
        vw, _ = get_viewport_size()
        sidebar_w = clamp(int(vw * 0.78), 240, 340)
        close_btn_w = clamp(sidebar_w - 40, 160, 260)

        category_showcase_container.visible = not is_admin
        category_filter_container.visible = is_admin

        content_area = ft.Container(content=equipment_section, expand=True)

        def open_drawer(e):
            now_vw, _ = get_viewport_size()
            new_sidebar_w = clamp(int(now_vw * 0.78), 240, 340)
            sidebar.width = new_sidebar_w
            close_menu_btn.width = clamp(new_sidebar_w - 40, 160, 260)
            sidebar.visible = True
            page.update()

        def switch_to_equipment(e):
            content_area.content = equipment_section
            load_categories()
            load_equipments()
            sidebar.width = 0
            sidebar.visible = False
            page.update()

        def switch_to_rentals(e):
            content_area.content = rentals_section
            load_rentals()
            sidebar.width = 0
            sidebar.visible = False
            page.update()

        def logout_action(e):
            sidebar.width = 0
            sidebar.visible = False
            page.update()
            logout_to_login()
        
        def close_sidebar(e):
            sidebar.width = 0
            sidebar.visible = False
            page.update()

        close_menu_btn = ft.ElevatedButton(
            "ปิด",
            width=close_btn_w,
            bgcolor=C_AMBER,
            color=C_TEXT,
            icon=ft.Icons.CLOSE,
            on_click=close_sidebar,
        )

        # Sidebar menu with animated sliding
        sidebar = ft.Container(
            width=0,
            bgcolor=C_BG,
            padding=0,
            visible=False,
            expand=False,
            content=ft.Column(
                [
                    # Header with logo/app name and close button
                    ft.Container(
                        bgcolor=C_NAVY_MID,
                        padding=16,
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=C_AMBER),
                                        ft.Text("CameraRent", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text("อุปกรณ์ถ่ายภาพยืม", size=10, color=C_MUTED),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_color=ft.Colors.WHITE,
                                    icon_size=24,
                                    on_click=close_sidebar,
                                    tooltip="ปิดเมนู",
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                    ),
                    ft.Container(height=8),
                    # Menu items with hover effect
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, color=C_AMBER, size=22),
                        title=ft.Text("อุปกรณ์", color=C_TEXT, size=14, weight=ft.FontWeight.W_500),
                        subtitle=ft.Text("ดูรายการอุปกรณ์", size=10, color=C_MUTED),
                        on_click=switch_to_equipment,
                        hover_color=ft.Colors.with_opacity(0.1, C_NAVY),
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.QUEUE_OUTLINED, color=C_AMBER, size=22),
                        title=ft.Text("คิวงาน", color=C_TEXT, size=14, weight=ft.FontWeight.W_500),
                        subtitle=ft.Text("ดูสถานะการยืม", size=10, color=C_MUTED),
                        on_click=switch_to_rentals,
                        hover_color=ft.Colors.with_opacity(0.1, C_NAVY),
                    ),
                    ft.Divider(height=1, color=C_BORDER),
                    ft.Container(height=8),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGOUT_OUTLINED, color=C_DANGER, size=22),
                        title=ft.Text("ออกจากระบบ", color=C_DANGER, size=14, weight=ft.FontWeight.W_500),
                        subtitle=ft.Text("ลงชื่อออกจากแอป", size=10, color=C_MUTED),
                        on_click=logout_action,
                        hover_color=ft.Colors.with_opacity(0.1, C_DANGER),
                    ),
                    ft.Container(expand=True),
                    # Footer with close button
                    ft.Container(
                        padding=12,
                        content=ft.Column(
                            [
                                ft.Divider(height=1, color=C_BORDER),
                                close_menu_btn,
                                ft.Text("v1.0 Beta", size=10, color=C_MUTED),
                                ft.Text("© 2026 CameraRent", size=9, color=C_MUTED),
                            ],
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        )

        # Overlay to close sidebar when clicked
        overlay = ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            visible=False,
            on_click=close_sidebar,
        )

        # AppBar with menu
        app_bar = ft.AppBar(
            title=ft.Text("", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
            bgcolor=C_NAVY,
            leading=ft.IconButton(
                icon=ft.Icons.MENU,
                icon_color=ft.Colors.WHITE,
                on_click=lambda e: open_drawer(e),
            ),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.PERSON_OUTLINE,
                    icon_color=ft.Colors.WHITE,
                    tooltip="โปรไฟล์",
                    on_click=lambda e: show_profile_page(),
                ),
            ],
            elevation=0,
        )
        page.appbar = app_bar

        # Main content layout with sidebar that expands to fill space
        main_row = ft.Row(
            [
                sidebar,
                content_area,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )
        
        page.add(
            ft.Container(
                content=main_row,
                expand=True,
                alignment=ft.Alignment(-1, -1),
            )
        )

        if is_admin:
            page.floating_action_button = ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                bgcolor=C_AMBER,
                foreground_color=C_NAVY,
                on_click=lambda e: show_add_page(),
            )
        else:
            page.floating_action_button = None

        load_categories()
        load_equipments()
        page.update()

    # ── EQUIPMENT DETAIL ─────────────────────────────────────────────────────────
    def show_details(eq):
        vw, vh = get_viewport_size()
        detail_hero_h = clamp(int(vh * 0.28), 180, 300)
        day_field_w = clamp(int(vw * 0.34), 120, 180)

        gallery_images = eq.get("image_urls") or []
        if not gallery_images:
            primary = eq.get("primary_image_url")
            if primary:
                gallery_images = [primary]
        if not gallery_images:
            gallery_images = [""]

        selected_image = [gallery_images[0]]

        def equipment_preview_control(url: str, width: int, height: int, icon_size: int = 24):
            if not url:
                return ft.Container(
                    width=width,
                    height=height,
                    bgcolor=C_SURFACE_2,
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.PHOTO_CAMERA_OUTLINED, color=C_MUTED, size=icon_size),
                            ft.Text("ไม่มีรูป", size=11, color=C_MUTED),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            return ft.Image(src=url, fit=FIT_COVER, width=width, height=height)

        def open_rent_page(e):
            if current_user.get("role") == "guest":
                show_snackbar("กรุณาเข้าสู่ระบบก่อนเช่า", is_error=True)
                return
            if not current_user.get("id"):
                show_snackbar("Session ไม่ถูกต้อง", is_error=True)
                return

            start_date_value = [date.today()]
            end_date_value = [date.today() + timedelta(days=1)]

            def date_text(d: date) -> str:
                return d.strftime("%d/%m/%Y")

            rent_days           = field_style(label="จำนวนวัน", value="2", keyboard_type=ft.KeyboardType.NUMBER, width=day_field_w)
            start_date_value_text = ft.Text(date_text(start_date_value[0]), size=14, weight=ft.FontWeight.W_700, color=C_TEXT)
            end_date_value_text   = ft.Text(date_text(end_date_value[0]), size=14, weight=ft.FontWeight.W_700, color=C_TEXT)
            contact_phone_field = field_style(label="เบอร์ติดต่อ", hint_text="เบอร์โทรศัพท์")
            pickup_field        = field_style(label="จุดรับอุปกรณ์", hint_text="ระบุสถานที่หรือวางลิงก์ Google Maps")
            purpose_field       = field_style(label="วัตถุประสงค์ (ถ้ามี)", hint_text="งานแต่ง / ถ่ายคอนเทนต์ ฯลฯ")
            note_field          = multiline_field(label="หมายเหตุ (ถ้ามี)", min_lines=2, max_lines=3)

            total_text   = ft.Text(f"ค่าเช่ารวม: ฿{eq.get('daily_rate', 0):,.0f}",
                                   size=16, weight=ft.FontWeight.W_800, color=C_AMBER_DARK)
            deposit_text = ft.Text(f"มัดจำ: ฿{eq.get('deposit_rate', 0):,.0f}",
                                   size=13, color=C_DANGER)

            def refresh_date_fields():
                start_date_value_text.value = date_text(start_date_value[0])
                end_date_value_text.value = date_text(end_date_value[0])
                delta_days = (end_date_value[0] - start_date_value[0]).days + 1
                rent_days.value = str(max(1, delta_days))

            picker_target = ["start"]
            picker_title = ft.Text("เลือกวันเริ่มเช่า", size=12, color=C_MUTED)
            current_year = date.today().year
            years = list(range(current_year, current_year + 3))
            picker_year_dd = ft.Dropdown(label="ปี", options=[ft.dropdown.Option(str(y)) for y in years], width=120)
            picker_month_dd = ft.Dropdown(label="เดือน", options=[ft.dropdown.Option(str(m)) for m in range(1, 13)], width=100)
            picker_day_dd = ft.Dropdown(label="วัน", width=100)
            picker_sheet = ft.Container(
                height=0,
                animate_size=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                border=ft.border.all(1, C_BORDER),
                border_radius=12,
                bgcolor=C_SURFACE,
                padding=ft.padding.all(12),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Column(
                    [
                        picker_title,
                        ft.Row([picker_day_dd, picker_month_dd, picker_year_dd], spacing=8, wrap=True),
                        ft.Row(
                            [
                                text_button("ยกเลิก", on_click=lambda e: close_inline_picker()),
                                primary_button("ยืนยัน", on_click=lambda e: confirm_inline_picker()),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                        ),
                    ],
                    spacing=8,
                ),
            )

            def rebuild_picker_days(e=None):
                try:
                    y = int(picker_year_dd.value)
                    m = int(picker_month_dd.value)
                    if m == 2:
                        max_day = 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28
                    elif m in (4, 6, 9, 11):
                        max_day = 30
                    else:
                        max_day = 31
                    selected_day = int(picker_day_dd.value) if picker_day_dd.value else 1
                    picker_day_dd.options = [ft.dropdown.Option(str(d)) for d in range(1, max_day + 1)]
                    picker_day_dd.value = str(min(selected_day, max_day))
                    page.update()
                except Exception:
                    pass

            picker_year_dd.on_change = rebuild_picker_days
            picker_month_dd.on_change = rebuild_picker_days

            def open_inline_picker(target: str):
                picker_target[0] = target
                initial_value = start_date_value[0] if target == "start" else end_date_value[0]
                picker_title.value = "เลือกวันเริ่มเช่า" if target == "start" else "เลือกวันสิ้นสุดเช่า"
                picker_year_dd.value = str(initial_value.year)
                picker_month_dd.value = str(initial_value.month)
                picker_day_dd.value = str(initial_value.day)
                rebuild_picker_days()
                picker_sheet.height = 170
                page.update()

            def close_inline_picker():
                picker_sheet.height = 0
                page.update()

            def confirm_inline_picker():
                try:
                    picked = date(int(picker_year_dd.value), int(picker_month_dd.value), int(picker_day_dd.value))
                    if picker_target[0] == "start":
                        set_start_date(picked)
                    else:
                        set_end_date(picked)
                    close_inline_picker()
                    page.update()
                except Exception:
                    show_snackbar("รูปแบบวันที่ไม่ถูกต้อง", is_error=True)

            def set_start_date(picked: date):
                start_date_value[0] = picked
                if end_date_value[0] < picked:
                    end_date_value[0] = picked
                refresh_date_fields()

            def set_end_date(picked: date):
                if picked < start_date_value[0]:
                    show_snackbar("วันสิ้นสุดต้องไม่ก่อนวันเริ่มเช่า", is_error=True)
                    return
                end_date_value[0] = picked
                refresh_date_fields()

            def sync_phone_from_profile():
                uid = current_user.get("id")
                if not uid:
                    return
                try:
                    resp = requests.get(f"{API_BASE_URL}/users/{uid}", timeout=6)
                    if resp.status_code == 200:
                        profile = resp.json()
                        if profile.get("phone"):
                            contact_phone_field.value = profile.get("phone")
                except Exception:
                    pass

            def calc_total(e):
                try:
                    days = int(rent_days.value)
                    if days > 0:
                        total_text.value = f"ค่าเช่ารวม: ฿{days * float(eq.get('daily_rate', 0)):,.0f}"
                        end_date_value[0] = start_date_value[0] + timedelta(days=days - 1)
                        refresh_date_fields()
                        page.update()
                except ValueError:
                    pass
            rent_days.on_change = calc_total
            sync_phone_from_profile()
            refresh_date_fields()

            def submit_rent(e):
                if not start_date_value[0] or not end_date_value[0]:
                    show_snackbar("กรุณาระบุวันเริ่ม-สิ้นสุด", is_error=True)
                    return
                if not contact_phone_field.value or not pickup_field.value:
                    show_snackbar("กรุณาระบุเบอร์ติดต่อและจุดรับอุปกรณ์", is_error=True)
                    return
                try:
                    r = requests.post(
                        f"{API_BASE_URL}/rentals",
                        json={
                            "user_id":         current_user.get("id"),
                            "equipment_id":    eq.get("id"),
                            "start_date":      start_date_value[0].isoformat(),
                            "end_date":        end_date_value[0].isoformat(),
                            "contact_phone":   contact_phone_field.value,
                            "pickup_location": pickup_field.value,
                            "purpose":         purpose_field.value,
                            "note":            note_field.value,
                        },
                        timeout=8,
                    )
                    if r.status_code == 200:
                        show_snackbar("สร้างคำขอเช่าสำเร็จแล้ว!", is_error=False)
                        load_equipments()
                        show_main_app()
                    else:
                        show_snackbar(r.json().get("detail", "สร้างการเช่าไม่ได้"), is_error=True)
                except Exception as ex:
                    show_snackbar(f"เชื่อมต่อไม่ได้: {ex}", is_error=True)

            page.clean()
            page.navigation_bar = None
            page.floating_action_button = None
            page.add(
                ft.Column(
                    [
                        ft.AppBar(
                            title=ft.Text("แบบฟอร์มเช่าอุปกรณ์", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                            bgcolor=C_NAVY,
                            leading=icon_button(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE,
                                                on_click=lambda e: show_details(eq)),
                        ),
                        ft.Container(
                            expand=True,
                            padding=20,
                            content=ft.Column(
                                [
                                    # Equipment summary
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                ft.Container(
                                                    width=64, height=64,
                                                    border_radius=10,
                                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                                    content=equipment_preview_control(selected_image[0], 64, 64, icon_size=18),
                                                ),
                                                ft.Column(
                                                    [
                                                        ft.Text(eq.get("name"), size=14,
                                                                weight=ft.FontWeight.W_700, color=C_TEXT),
                                                        ft.Text(f"{eq.get('brand')} | SN: {eq.get('serial_number')}",
                                                                size=11, color=C_MUTED),
                                                        ft.Row([total_text, deposit_text], spacing=8),
                                                    ],
                                                    spacing=4,
                                                    expand=True,
                                                ),
                                            ],
                                            spacing=12,
                                        ),
                                        bgcolor=C_NAVY + "08",
                                        border_radius=12,
                                        padding=12,
                                        border=ft.border.all(1, C_BORDER),
                                    ),
                                    section_heading("ระยะเวลาเช่า", ft.Icons.CALENDAR_MONTH_OUTLINED),
                                    ft.Row([rent_days], spacing=8, wrap=True),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                        border=ft.border.all(1, C_BORDER),
                                        border_radius=10,
                                        bgcolor=C_SURFACE,
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.Icons.EVENT_OUTLINED, color=C_MUTED, size=18),
                                                ft.Column(
                                                    [
                                                        ft.Text("วันเริ่มเช่า", size=11, color=C_MUTED),
                                                        start_date_value_text,
                                                    ],
                                                    spacing=2,
                                                ),
                                            ],
                                            spacing=8,
                                        ),
                                    ),
                                    ft.Row(
                                        [
                                            ghost_button(
                                                "เลือกวันเริ่ม",
                                                icon=ft.Icons.EVENT_OUTLINED,
                                                on_click=lambda e: open_inline_picker("start"),
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                    ),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                        border=ft.border.all(1, C_BORDER),
                                        border_radius=10,
                                        bgcolor=C_SURFACE,
                                        content=ft.Row(
                                            [
                                                ft.Icon(ft.Icons.EVENT_AVAILABLE_OUTLINED, color=C_MUTED, size=18),
                                                ft.Column(
                                                    [
                                                        ft.Text("วันสิ้นสุด", size=11, color=C_MUTED),
                                                        end_date_value_text,
                                                    ],
                                                    spacing=2,
                                                ),
                                            ],
                                            spacing=8,
                                        ),
                                    ),
                                    ft.Row(
                                        [
                                            ghost_button(
                                                "เลือกวันสิ้นสุด",
                                                icon=ft.Icons.EVENT_AVAILABLE_OUTLINED,
                                                on_click=lambda e: open_inline_picker("end"),
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                    ),
                                    picker_sheet,
                                    section_heading("ข้อมูลการรับอุปกรณ์", ft.Icons.PLACE_OUTLINED),
                                    contact_phone_field,
                                    pickup_field,
                                    purpose_field,
                                    note_field,
                                    divider_line(),
                                    ft.Text("* มัดจำจะคืนเมื่อส่งอุปกรณ์คืนและตรวจสภาพแล้ว",
                                            size=11, color=C_MUTED, italic=True),
                                    ft.Row(
                                        [
                                            ghost_button("ย้อนกลับ", on_click=lambda e: show_details(eq)),
                                            primary_button("ยืนยันการเช่า", icon=ft.Icons.SEND_OUTLINED,
                                                           on_click=submit_rent),
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                        spacing=10,
                                    ),
                                ],
                                scroll=ft.ScrollMode.AUTO,
                                spacing=10,
                                expand=True,
                            ),
                        ),
                    ],
                    expand=True,
                    spacing=0,
                )
            )
            page.update()

        page.clean()
        status = eq.get("status", "available").lower()
        s_cfg  = STATUS_CONFIG.get(status, {"color": C_MUTED, "bg": C_SURFACE_2, "label": status})
        hero_image = ft.Container(
            width=vw,
            height=detail_hero_h,
            content=equipment_preview_control(selected_image[0], vw, detail_hero_h, icon_size=56),
        )

        thumbnail_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)

        def build_thumbnails():
            thumbnail_row.controls.clear()
            for img_url in gallery_images:
                is_active = img_url == selected_image[0]
                thumbnail_row.controls.append(
                    ft.GestureDetector(
                        on_tap=lambda e, u=img_url: set_selected_image(u),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        content=ft.Container(
                            width=72,
                            height=72,
                            border_radius=10,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            border=ft.border.all(2, C_AMBER if is_active else C_BORDER),
                            content=equipment_preview_control(img_url, 72, 72, icon_size=18),
                        ),
                    )
                )

        def set_selected_image(url: str):
            selected_image[0] = url
            hero_image.content = equipment_preview_control(url, vw, detail_hero_h, icon_size=56)
            build_thumbnails()
            page.update()

        build_thumbnails()

        page.add(
            ft.Column(
                [
                    ft.AppBar(
                        title=ft.Text("รายละเอียดอุปกรณ์", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                        bgcolor=C_NAVY,
                        leading=icon_button(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE,
                                            on_click=lambda e: show_main_app()),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Column(
                            [
                                # Hero image
                                ft.Container(
                                    height=detail_hero_h,
                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                    content=ft.Stack(
                                        [
                                            hero_image,
                                            ft.Container(
                                                gradient=ft.LinearGradient(
                                                    begin=ft.Alignment(0, 0),
                                                    end=ft.Alignment(0, 1),
                                                    colors=["#00000000", "#CC0F172A"],
                                                ),
                                                height=detail_hero_h,
                                            ),
                                            ft.Container(
                                                content=ft.Row(
                                                    [ft.Icon(s_cfg.get("icon", ft.Icons.CIRCLE_OUTLINED), size=12, color=s_cfg["color"]),
                                                     ft.Text(s_cfg["label"], size=10, weight=ft.FontWeight.W_700, color=s_cfg["color"])],
                                                    spacing=4,
                                                ),
                                                bgcolor=s_cfg["bg"],
                                                border_radius=20,
                                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                                top=12, right=12,
                                            ),
                                        ],
                                        expand=True,
                                    ),
                                ),
                                ft.Container(
                                    padding=ft.padding.only(left=20, right=20, top=12, bottom=0),
                                    content=thumbnail_row,
                                ),
                                # Info
                                ft.Container(
                                    padding=20,
                                    content=ft.Column(
                                        [
                                            ft.Text(eq.get("name"), size=22, weight=ft.FontWeight.W_800, color=C_NAVY),
                                            ft.Row(
                                                [icon_text_row(ft.Icons.BUSINESS_OUTLINED, eq.get("brand", "-")),
                                                 ft.Text("·", color=C_MUTED),
                                                 icon_text_row(ft.Icons.QR_CODE_2, eq.get("serial_number", "-"))],
                                                spacing=4,
                                            ),
                                            divider_line(),
                                            # Price row
                                            ft.Row(
                                                [
                                                    ft.Container(
                                                        content=ft.Column(
                                                            [ft.Text("ค่าเช่า/วัน", size=10, color=C_MUTED),
                                                             ft.Text(f"฿{eq.get('daily_rate', 0):,.0f}",
                                                                     size=22, weight=ft.FontWeight.W_900, color=C_AMBER_DARK)],
                                                            spacing=2,
                                                        ),
                                                        expand=True,
                                                    ),
                                                    ft.Container(
                                                        content=ft.Column(
                                                            [ft.Text("มัดจำ", size=10, color=C_MUTED),
                                                             ft.Text(f"฿{eq.get('deposit_rate', 0):,.0f}",
                                                                     size=22, weight=ft.FontWeight.W_900, color=C_DANGER)],
                                                            spacing=2,
                                                        ),
                                                        expand=True,
                                                    ),
                                                ],
                                            ),
                                            divider_line(),
                                            ft.Text(eq.get("description", "-"), size=13, color=C_MUTED),
                                            ft.Container(
                                                margin=ft.Margin(top=6, bottom=0, left=0, right=0),
                                                padding=12,
                                                bgcolor=C_SURFACE_2,
                                                border_radius=12,
                                                border=ft.border.all(1, C_BORDER),
                                                content=ft.Column(
                                                    [
                                                        ft.Text("รายละเอียดอุปกรณ์", size=13, weight=ft.FontWeight.W_700, color=C_NAVY),
                                                        ft.Row(
                                                            [
                                                                ft.Text("รหัสอุปกรณ์", size=11, color=C_MUTED, width=100),
                                                                ft.Text(str(eq.get("id") or "-"), size=12, color=C_TEXT, expand=True),
                                                            ],
                                                            spacing=8,
                                                        ),
                                                        ft.Row(
                                                            [
                                                                ft.Text("หมวดหมู่", size=11, color=C_MUTED, width=100),
                                                                ft.Text(eq.get("category_name") or "-", size=12, color=C_TEXT, expand=True),
                                                            ],
                                                            spacing=8,
                                                        ),
                                                        ft.Row(
                                                            [
                                                                ft.Text("สถานะปัจจุบัน", size=11, color=C_MUTED, width=100),
                                                                ft.Text(s_cfg.get("label", "-"), size=12, color=s_cfg.get("color", C_TEXT), expand=True),
                                                            ],
                                                            spacing=8,
                                                        ),
                                                        ft.Row(
                                                            [
                                                                ft.Text("รูปทั้งหมด", size=11, color=C_MUTED, width=100),
                                                                ft.Text(str(len(gallery_images)), size=12, color=C_TEXT, expand=True),
                                                            ],
                                                            spacing=8,
                                                        ),
                                                    ],
                                                    spacing=6,
                                                ),
                                            ),
                                            ft.Container(height=16),
                                            ft.Row(
                                                [
                                                    ghost_button("ย้อนกลับ", on_click=lambda e: show_main_app()),
                                                    primary_button(
                                                        "เช่าเลย",
                                                        icon=ft.Icons.SHOPPING_CART_OUTLINED,
                                                        on_click=open_rent_page if status == "available" else None,
                                                    ) if status == "available" else ft.Button(
                                                        "ไม่ว่างในขณะนี้",
                                                        disabled=True,
                                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                                        height=46,
                                                    ),
                                                ],
                                                alignment=ft.MainAxisAlignment.END,
                                                spacing=10,
                                            ),
                                        ],
                                        spacing=8,
                                        scroll=ft.ScrollMode.AUTO,
                                    ),
                                ),
                            ],
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                        ),
                    ),
                ],
                expand=True,
                spacing=0,
            )
        )

    # ── ADD / EDIT EQUIPMENT ─────────────────────────────────────────────────────

    def show_add_page():
        current_edit[0] = None
        for f in [form_name, form_brand, form_serial, form_desc, form_daily, form_deposit, form_image_urls]:
            f.value = ""
        form_primary_image_index.value = "0"
        form_status.value = "available"
        render_form_page("เพิ่มอุปกรณ์")

    def show_edit_page(eq):
        current_edit[0]   = eq.get("id")
        form_category.value = str(eq.get("category_id"))
        form_name.value    = eq.get("name")
        form_brand.value   = eq.get("brand")
        form_serial.value  = eq.get("serial_number")
        form_desc.value    = eq.get("description")
        form_daily.value   = str(eq.get("daily_rate"))
        form_deposit.value = str(eq.get("deposit_rate"))
        form_status.value  = eq.get("status")
        edit_urls = eq.get("image_urls") or []
        form_image_urls.value = "\n".join(edit_urls)
        primary_url = eq.get("primary_image_url")
        primary_idx = edit_urls.index(primary_url) if primary_url in edit_urls else 0
        form_primary_image_index.value = str(primary_idx)
        render_form_page("แก้ไขอุปกรณ์")

    def render_form_page(title):
        vw, _ = get_viewport_size()
        save_btn_w = clamp(int(vw * 0.78), 220, 360)

        page.clean()
        page.navigation_bar = None
        page.floating_action_button = None
        page.add(
            ft.Column(
                [
                    ft.AppBar(
                        title=ft.Text(title, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                        bgcolor=C_NAVY,
                        leading=icon_button(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE,
                                            on_click=lambda e: show_main_app()),
                    ),
                    ft.Container(
                        expand=True,
                        padding=20,
                        content=ft.Column(
                            [
                                form_category,
                                form_name, form_brand, form_serial,
                                form_daily, form_deposit,
                                form_image_urls,
                                form_primary_image_index,
                                form_status,
                                form_desc,
                                ft.Container(height=4),
                                primary_button("บันทึก", icon=ft.Icons.SAVE_OUTLINED, on_click=save_equipment, width=save_btn_w),
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                            spacing=10,
                        ),
                    ),
                ],
                expand=True,
                spacing=0,
            )
        )

    def save_equipment(e):
        try:
            cat_id = int(form_category.value)
            d_rate = float(form_daily.value)
            dep    = float(form_deposit.value)
            primary_idx = int(form_primary_image_index.value or 0)
        except ValueError:
            show_snackbar("กรุณากรอกตัวเลขให้ถูกต้อง", is_error=True)
            return

        image_urls = [line.strip() for line in (form_image_urls.value or "").splitlines() if line.strip()]
        if primary_idx < 0:
            show_snackbar("ลำดับรูปหลักต้องเป็น 0 หรือมากกว่า", is_error=True)
            return
        if image_urls and primary_idx >= len(image_urls):
            show_snackbar(f"ลำดับรูปหลักต้องน้อยกว่า {len(image_urls)}", is_error=True)
            return

        data = {
            "category_id":  cat_id,
            "name":         form_name.value,
            "brand":        form_brand.value,
            "serial_number": form_serial.value,
            "description":  form_desc.value,
            "daily_rate":   d_rate,
            "deposit_rate": dep,
            "status":       form_status.value,
            "image_urls":   image_urls,
            "primary_image_index": primary_idx,
        }

        try:
            if current_edit[0]:
                r = requests.put(f"{API_BASE_URL}/equipments/{current_edit[0]}", json=data, timeout=5)
            else:
                r = requests.post(f"{API_BASE_URL}/equipments", json=data, timeout=5)

            if r.status_code in (200, 201):
                show_snackbar("บันทึกข้อมูลสำเร็จ!", is_error=False)
                show_main_app()
            elif r.status_code == 422:
                errs = [f"• {e['loc'][-1]}: {e['msg']}" for e in r.json().get("detail", [])]
                show_snackbar("ข้อมูลไม่ถูกต้อง:\n" + "\n".join(errs), is_error=True)
            else:
                show_snackbar(r.json().get("detail", "บันทึกไม่ได้"), is_error=True)
        except Exception as ex:
            show_snackbar(f"เชื่อมต่อไม่ได้: {ex}", is_error=True)

    def delete_equipment(eq_id):
        try:
            requests.delete(f"{API_BASE_URL}/equipments/{eq_id}", timeout=5)
            show_snackbar("ลบสำเร็จ", is_error=False)
            load_equipments()
        except Exception as ex:
            show_snackbar(f"ลบไม่ได้: {ex}", is_error=True)

    show_login_page()


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
