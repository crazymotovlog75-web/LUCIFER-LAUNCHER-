#!/usr/bin/env python3
"""
Generates the complete #02 (Shadow Monarch Abyss) + #05 (Ender Dragon Cataclysm)
UI overhaul overlay for LUCIFER LAUNCHER and validates every XML & Java reference
against the base Android project in /tmp/v2-src.
"""
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

SRC_BASE = "/tmp/v2-src/app_pojavlauncher/src/main"
OUT_BASE = "launcher-ui-overhaul/app_pojavlauncher/src/main"


def write_text(rel_path: str, content: str) -> None:
    full = os.path.join(OUT_BASE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content.lstrip("\n"))


def generate_values() -> None:
    # 1. Adaptive icon background
    write_text(
        "res/values/ic_launcher_background.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#05040B</color>
</resources>
""",
    )

    # 2. Upgrade wallpaper_colors.xml -> Wallpaper 01 is DEFAULT_ID = 0 (Shadow Dragon Cataclysm)
    with open(os.path.join(SRC_BASE, "res/values/wallpaper_colors.xml"), encoding="utf-8") as fh:
        wp_colors = fh.read()

    old_block_pattern = re.compile(
        r"<!-- 01\. Ender Dragon -->.*?(?=<!-- 02\.)", re.DOTALL
    )
    new_wp01 = """<!-- 01. Shadow Monarch x Ender Dragon Cataclysm (#02 + #05 Fusion) -->
    <color name="wallpaper_01_accent">#00D4FF</color>
    <color name="wallpaper_01_secondary">#D946EF</color>
    <color name="wallpaper_01_highlight">#E0F7FF</color>
    <color name="wallpaper_01_surface">#06040E</color>
    <color name="wallpaper_01_surface_high">#150B2B</color>
    <color name="wallpaper_01_glass">#DC080616</color>
    <color name="wallpaper_01_glass_high">#EC120B28</color>
    <color name="wallpaper_01_border">#9900D4FF</color>
    <color name="wallpaper_01_accent_dim">#4D00D4FF</color>
    <color name="wallpaper_01_backdrop">#4204030A</color>

    """
    assert old_block_pattern.search(wp_colors), "Could not locate wallpaper_01 block"
    wp_colors = old_block_pattern.sub(new_wp01, wp_colors, count=1)
    write_text("res/values/wallpaper_colors.xml", wp_colors)

    # 3. Upgrade colors.xml with Shadow-Dragon tokens while keeping 100% of existing names
    with open(os.path.join(SRC_BASE, "res/values/colors.xml"), encoding="utf-8") as fh:
        colors_xml = fh.read()

    replacements = {
        '<color name="minebutton_color">#7BE7E4</color>': '<color name="minebutton_color">#00D4FF</color>',
        '<color name="cu_bg_app">#080B12</color>': '<color name="cu_bg_app">#05040B</color>',
        '<color name="cu_bg_status_bar">#06090F</color>': '<color name="cu_bg_status_bar">#040309</color>',
        '<color name="cu_bg_bottom_bar">#0A101A</color>': '<color name="cu_bg_bottom_bar">#090616</color>',
        '<color name="bg_primary">#080B12</color>': '<color name="bg_primary">#05040B</color>',
        '<color name="bg_launcher_dark">#080B12</color>': '<color name="bg_launcher_dark">#05040B</color>',
        '<color name="bg_sidebar">#0B1019</color>': '<color name="bg_sidebar">#080513</color>',
        '<color name="bg_header">#131B28</color>': '<color name="bg_header">#0C081D</color>',
        '<color name="bg_bottom_bar">#111924</color>': '<color name="bg_bottom_bar">#0A0718</color>',
        '<color name="bg_card">#141C29</color>': '<color name="bg_card">#0E0920</color>',
        '<color name="bg_card_dark">#1C2635</color>': '<color name="bg_card_dark">#150D2E</color>',
        '<color name="accent_primary">#7BE7E4</color>': '<color name="accent_primary">#00D4FF</color>',
        '<color name="accent_light">#B7F7F4</color>': '<color name="accent_light">#7CEEFF</color>',
        '<color name="accent_purple">#B8A0FF</color>': '<color name="accent_purple">#D946EF</color>',
        '<color name="accent_purple_deep">#7255BD</color>': '<color name="accent_purple_deep">#7C3AED</color>',
        '<color name="accent_border">#7BE7E4</color>': '<color name="accent_border">#00D4FF</color>',
        '<color name="lucifer_bg">#080B12</color>': '<color name="lucifer_bg">#05040B</color>',
        '<color name="lucifer_surface">#141C29</color>': '<color name="lucifer_surface">#0C081C</color>',
        '<color name="lucifer_surface_high">#1C2635</color>': '<color name="lucifer_surface_high">#160E30</color>',
        '<color name="lucifer_glass_edge">#657BE7E4</color>': '<color name="lucifer_glass_edge">#8800D4FF</color>',
        '<color name="lucifer_cyan">#7BE7E4</color>': '<color name="lucifer_cyan">#00D4FF</color>',
        '<color name="lucifer_violet">#B8A0FF</color>': '<color name="lucifer_violet">#D946EF</color>',
        '<color name="play_btn_bg">#47B8C7</color>': '<color name="play_btn_bg">#00D4FF</color>',
        '<color name="settings_bg">#080B12</color>': '<color name="settings_bg">#05040B</color>',
        '<color name="card_bg">#101823</color>': '<color name="card_bg">#0C081C</color>',
        '<color name="card_bg_pressed">#1B2937</color>': '<color name="card_bg_pressed">#1C1138</color>',
        '<color name="neon_green">#7BE7E4</color>': '<color name="neon_green">#00D4FF</color>',
        '<color name="neon_green_dim">#3F7BE7E4</color>': '<color name="neon_green_dim">#4400D4FF</color>',
        '<color name="stroke_neon">#557BE7E4</color>': '<color name="stroke_neon">#80D946EF</color>',
        '<color name="bg_nav_item_active">#664BAFC1</color>': '<color name="bg_nav_item_active">#6600D4FF</color>',
    }
    for k, v in replacements.items():
        colors_xml = colors_xml.replace(k, v)

    extra_tokens = """
    <!-- Shadow Monarch (#02) + Ender Dragon Cataclysm (#05) Fused Tokens -->
    <color name="sd_void">#05040B</color>
    <color name="sd_obsidian">#090616</color>
    <color name="sd_obsidian_high">#140C2C</color>
    <color name="sd_cyan">#00D4FF</color>
    <color name="sd_cyan_bright">#67E8F9</color>
    <color name="sd_violet">#8B5CF6</color>
    <color name="sd_magenta">#D946EF</color>
    <color name="sd_magenta_bright">#F0ABFC</color>
    <color name="sd_online_emerald">#22C55E</color>
</resources>"""
    colors_xml = colors_xml.replace("</resources>", extra_tokens)
    write_text("res/values/colors.xml", colors_xml)

    # 4. Upgrade styles.xml with Shadow-Dragon Dock & HUD styles
    with open(os.path.join(SRC_BASE, "res/values/styles.xml"), encoding="utf-8") as fh:
        styles_xml = fh.read()

    dock_styles = """
    <!-- Shadow-Dragon (#02 + #05) Bottom Crystal Dock & Top Telemetry Styles -->
    <style name="LuciferDockTab">
        <item name="android:layout_width">wrap_content</item>
        <item name="android:minWidth">@dimen/_50sdp</item>
        <item name="android:layout_height">@dimen/_34sdp</item>
        <item name="android:layout_marginHorizontal">@dimen/_2sdp</item>
        <item name="android:orientation">vertical</item>
        <item name="android:gravity">center</item>
        <item name="android:paddingHorizontal">@dimen/_7sdp</item>
        <item name="android:paddingVertical">@dimen/_2sdp</item>
        <item name="android:background">@drawable/bg_sd_dock_tab</item>
        <item name="android:clickable">true</item>
        <item name="android:focusable">true</item>
    </style>

    <style name="LuciferDockIcon">
        <item name="android:layout_width">@dimen/_14sdp</item>
        <item name="android:layout_height">@dimen/_14sdp</item>
        <item name="android:tint">@color/sd_cyan_bright</item>
        <item name="android:contentDescription">@null</item>
    </style>

    <style name="LuciferDockLabel">
        <item name="android:layout_width">wrap_content</item>
        <item name="android:layout_height">wrap_content</item>
        <item name="android:layout_marginTop">@dimen/_1sdp</item>
        <item name="android:textColor">@color/text_primary_white</item>
        <item name="android:textSize">@dimen/_7ssp</item>
        <item name="android:textStyle">bold</item>
        <item name="android:letterSpacing">0.08</item>
        <item name="android:textAllCaps">true</item>
        <item name="android:maxLines">1</item>
    </style>
</resources>"""
    styles_xml = styles_xml.replace("</resources>", dock_styles)
    write_text("res/values/styles.xml", styles_xml)


def generate_drawables() -> None:
    # 45-degree Chamfer + Crystal Shard Corner Brackets (API 21+ safe VectorDrawables)
    write_text(
        "res/drawable/ic_sd_corner_tl.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M0,10 L10,0 L22,0 L20,2.2 L10.8,2.2 L2.2,10.8 L2.2,20 L0,22 Z" />
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M2,5 L7,0 L11,2 L5,8 Z" />
    <path
        android:fillColor="#B3FFFFFF"
        android:pathData="M3.5,4.5 L7,1 L8.5,2 L4.5,6 Z" />
</vector>
""",
    )

    write_text(
        "res/drawable/ic_sd_corner_tr.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M24,10 L14,0 L2,0 L4,2.2 L13.2,2.2 L21.8,10.8 L21.8,20 L24,22 Z" />
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M22,5 L17,0 L13,2 L19,8 Z" />
    <path
        android:fillColor="#B3FFFFFF"
        android:pathData="M20.5,4.5 L17,1 L15.5,2 L19.5,6 Z" />
</vector>
""",
    )

    write_text(
        "res/drawable/ic_sd_corner_bl.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp"
    android:height="22dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF8B5CF6"
        android:pathData="M0,14 L10,24 L22,24 L20,21.8 L10.8,21.8 L2.2,13.2 L2.2,4 L0,2 Z" />
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M2,19 L7,24 L10,22 L4,16 Z" />
</vector>
""",
    )

    write_text(
        "res/drawable/ic_sd_corner_br.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp"
    android:height="22dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M24,14 L14,24 L2,24 L4,21.8 L13.2,21.8 L21.8,13.2 L21.8,4 L24,2 Z" />
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M22,19 L17,24 L14,22 L20,16 Z" />
</vector>
""",
    )

    # Crystal Shard Wings flanking the Bottom Floating Dock (#02 + #05 signature)
    write_text(
        "res/drawable/ic_sd_dock_crystals_left.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="32dp"
    android:height="40dp"
    android:viewportWidth="32"
    android:viewportHeight="40">
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M4,8 L18,16 L24,36 L10,32 Z" />
    <path
        android:fillColor="#FF9333EA"
        android:pathData="M18,16 L28,22 L24,36 Z" />
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M14,2 L26,14 L22,30 L12,18 Z" />
    <path
        android:fillColor="#CCFFFFFF"
        android:pathData="M15,5 L22,13 L18,22 L14,15 Z" />
    <path
        android:fillColor="#FF38BDF8"
        android:pathData="M1,22 L13,25 L16,38 L5,35 Z" />
</vector>
""",
    )

    write_text(
        "res/drawable/ic_sd_dock_crystals_right.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="32dp"
    android:height="40dp"
    android:viewportWidth="32"
    android:viewportHeight="40">
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M28,8 L14,16 L8,36 L22,32 Z" />
    <path
        android:fillColor="#FF9333EA"
        android:pathData="M14,16 L4,22 L8,36 Z" />
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M18,2 L6,14 L10,30 L20,18 Z" />
    <path
        android:fillColor="#CCFFFFFF"
        android:pathData="M17,5 L10,13 L14,22 L18,15 Z" />
    <path
        android:fillColor="#FF38BDF8"
        android:pathData="M31,22 L19,25 L16,38 L27,35 Z" />
</vector>
""",
    )

    # Top Tactical HUD Plate (chamfered dark obsidian + dual cyan-magenta neon border)
    write_text(
        "res/drawable/bg_sd_hud_plate.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <gradient
                android:angle="0"
                android:startColor="#EB070514"
                android:centerColor="#EB110924"
                android:endColor="#EB070514" />
            <corners android:radius="10dp" />
            <stroke android:width="1.5dp" android:color="#AA00D4FF" />
        </shape>
    </item>
    <item android:left="1dp" android:top="1dp" android:right="1dp" android:bottom="1dp">
        <shape android:shape="rectangle">
            <corners android:radius="9dp" />
            <stroke android:width="1dp" android:color="#55D946EF" />
        </shape>
    </item>
    <item android:gravity="top|start" android:width="16dp" android:height="16dp"
        android:drawable="@drawable/ic_sd_corner_tl" />
    <item android:gravity="bottom|end" android:width="16dp" android:height="16dp"
        android:drawable="@drawable/ic_sd_corner_br" />
</layer-list>
""",
    )

    # Bottom Floating Shadow-Dragon Crystal Dock Shell
    write_text(
        "res/drawable/bg_sd_dock_shell.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <gradient
                android:angle="0"
                android:startColor="#F2060411"
                android:centerColor="#F2130A2A"
                android:endColor="#F2060411" />
            <corners android:radius="14dp" />
            <stroke android:width="1.5dp" android:color="#CC00D4FF" />
        </shape>
    </item>
    <item android:left="2dp" android:top="2dp" android:right="2dp" android:bottom="2dp">
        <shape android:shape="rectangle">
            <corners android:radius="12dp" />
            <stroke android:width="1dp" android:color="#88D946EF" />
        </shape>
    </item>
    <item android:gravity="top|start" android:width="18dp" android:height="18dp"
        android:drawable="@drawable/ic_sd_corner_tl" />
    <item android:gravity="top|end" android:width="18dp" android:height="18dp"
        android:drawable="@drawable/ic_sd_corner_tr" />
</layer-list>
""",
    )

    # Dock Tab Selector (Cyan + Magenta active glow)
    write_text(
        "res/drawable/bg_sd_dock_tab.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_selected="true">
        <layer-list>
            <item>
                <shape android:shape="rectangle">
                    <gradient
                        android:angle="270"
                        android:startColor="#4400D4FF"
                        android:endColor="#55D946EF" />
                    <corners android:radius="10dp" />
                    <stroke android:width="1.5dp" android:color="#FF00D4FF" />
                </shape>
            </item>
            <item android:gravity="bottom" android:height="2.5dp" android:left="8dp" android:right="8dp">
                <shape android:shape="rectangle">
                    <solid android:color="#FF00D4FF" />
                    <corners android:radius="2dp" />
                </shape>
            </item>
        </layer-list>
    </item>
    <item android:state_pressed="true">
        <shape android:shape="rectangle">
            <solid android:color="#3800D4FF" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#AA00D4FF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <solid android:color="#00000000" />
            <corners android:radius="10dp" />
        </shape>
    </item>
</selector>
""",
    )

    # Global Crystal Armor Card (upgrades EVERY card across Home, Instances, Mods, Server Hub, About)
    crystal_card = """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <gradient
                android:angle="315"
                android:startColor="#EC090618"
                android:centerColor="#E3120A28"
                android:endColor="#EC070513" />
            <corners android:radius="14dp" />
            <stroke android:width="1.5dp" android:color="#9900D4FF" />
        </shape>
    </item>
    <item android:left="2dp" android:top="2dp" android:right="2dp" android:bottom="2dp">
        <shape android:shape="rectangle">
            <corners android:radius="12dp" />
            <stroke android:width="1dp" android:color="#55D946EF" />
        </shape>
    </item>
    <item android:gravity="top|start" android:width="20dp" android:height="20dp"
        android:drawable="@drawable/ic_sd_corner_tl" />
    <item android:gravity="top|end" android:width="20dp" android:height="20dp"
        android:drawable="@drawable/ic_sd_corner_tr" />
    <item android:gravity="bottom|start" android:width="18dp" android:height="18dp"
        android:drawable="@drawable/ic_sd_corner_bl" />
    <item android:gravity="bottom|end" android:width="18dp" android:height="18dp"
        android:drawable="@drawable/ic_sd_corner_br" />
</layer-list>
"""
    write_text("res/drawable/bg_lucifer_glass_card.xml", crystal_card)
    write_text("res/drawable/bg_sd_crystal_card.xml", crystal_card)

    # #02 Electric Shadow-Cyan JOIN Button
    write_text(
        "res/drawable/bg_sd_join_cyan.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true">
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#FF06B6D4" android:endColor="#FF7C3AED" />
            <corners android:radius="10dp" />
            <stroke android:width="1.5dp" android:color="#FFFFFFFF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#FF00E5FF" android:centerColor="#FF00B4D8" android:endColor="#FF38BDF8" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#CCFFFFFF" />
        </shape>
    </item>
</selector>
""",
    )

    # #05 Dragon Cataclysm Magenta OFFICIAL Badge
    write_text(
        "res/drawable/bg_sd_badge_magenta.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <gradient
        android:angle="0"
        android:startColor="#FFD946EF"
        android:endColor="#FF9333EA" />
    <corners android:radius="6dp" />
    <stroke android:width="1dp" android:color="#CCF5D0FE" />
</shape>
""",
    )

    # Shadow Monarch Rising Blue-Violet Flames + End Crystal Pedestal Stage behind 3D Player Avatar
    write_text(
        "res/drawable/bg_sd_shadow_flame_stage.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="220dp"
    android:height="240dp"
    android:viewportWidth="220"
    android:viewportHeight="240">
    <!-- Outer abyssal violet aura -->
    <path
        android:fillColor="#2E7C3AED"
        android:pathData="M110,18 C158,38 195,95 190,162 C186,204 152,228 110,228 C68,228 34,204 30,162 C25,95 62,38 110,18 Z" />
    <!-- Left & Right Shadow Monarch electric blue flame tongues -->
    <path
        android:fillColor="#5500D4FF"
        android:pathData="M36,208 C18,176 22,132 42,102 C35,134 46,154 58,136 C48,100 64,62 84,42 C74,78 82,106 94,94 C88,132 76,178 110,214 Z" />
    <path
        android:fillColor="#55D946EF"
        android:pathData="M184,208 C202,176 198,132 178,102 C185,134 174,154 162,136 C172,100 156,62 136,42 C146,78 138,106 126,94 C132,132 144,178 110,214 Z" />
    <!-- Bright inner electric cyan & magenta flame wisps -->
    <path
        android:fillColor="#8800E5FF"
        android:pathData="M48,210 C34,184 38,150 56,128 C52,154 64,170 76,156 C68,182 82,202 110,214 Z" />
    <path
        android:fillColor="#88E879F9"
        android:pathData="M172,210 C186,184 182,150 164,128 C168,154 156,170 144,156 C152,182 138,202 110,214 Z" />
    <!-- Obsidian & End-Crystal Pedestal Ring -->
    <path
        android:fillColor="#E6090618"
        android:strokeColor="#FF00D4FF"
        android:strokeWidth="2"
        android:pathData="M34,212 L68,198 L152,198 L186,212 L156,228 L64,228 Z" />
    <path
        android:fillColor="#66D946EF"
        android:pathData="M50,212 L76,203 L144,203 L170,212 L146,222 L74,222 Z" />
    <!-- Pedestal Crystal Spikes -->
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M28,212 L38,192 L46,214 Z" />
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M192,212 L182,192 L174,214 Z" />
</vector>
""",
    )

    # Dragon-Monarch Cataclysm PLAY / LAUNCH Reactor (#05 Jagged Crystal Spikes + #02 Electric Plasma Core)
    reactor_vector = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="180dp"
    android:height="150dp"
    android:viewportWidth="180"
    android:viewportHeight="150">
    <!-- Outer Dragon Amethyst & Electric Cyan Crystal Spikes -->
    <path
        android:fillColor="#FF9333EA"
        android:pathData="M90,4 L112,20 L142,10 L148,38 L176,52 L162,78 L176,104 L146,116 L138,142 L110,132 L90,146 L70,132 L42,142 L34,116 L4,104 L18,78 L4,52 L32,38 L38,10 L68,20 Z" />
    <path
        android:fillColor="#FFD946EF"
        android:pathData="M90,8 L108,22 L138,14 L142,40 L168,54 L156,78 L168,100 L142,112 L134,136 L108,128 L90,140 L72,128 L46,136 L38,112 L12,100 L24,78 L12,54 L38,40 L42,14 L72,22 Z" />
    <!-- Electric Shadow-Cyan Crystal Facets -->
    <path
        android:fillColor="#FF00D4FF"
        android:pathData="M90,6 L104,22 L90,28 L76,22 Z M6,52 L32,42 L28,62 Z M174,52 L148,42 L152,62 Z M8,104 L30,92 L36,112 Z M172,104 L150,92 L144,112 Z" />
    <!-- Inner Forged Hexagonal Plasma Core -->
    <path
        android:fillColor="#F20A061C"
        android:strokeColor="#FF00E5FF"
        android:strokeWidth="2.5"
        android:pathData="M44,32 L136,32 L158,75 L136,118 L44,118 L22,75 Z" />
    <!-- High-Voltage Inner Neon Glow -->
    <path
        android:fillColor="#CC7C3AED"
        android:strokeColor="#FFF0ABFC"
        android:strokeWidth="1.5"
        android:pathData="M50,39 L130,39 L149,75 L130,111 L50,111 L31,75 Z" />
    <path
        android:fillColor="#5500D4FF"
        android:pathData="M50,39 L130,39 L142,64 L38,64 Z" />
</vector>
"""
    write_text("res/drawable/ic_sd_reactor_idle.xml", reactor_vector)
    write_text(
        "res/drawable/ic_sd_reactor_pressed.xml",
        reactor_vector.replace("#CC7C3AED", "#FF00B4D8"),
    )

    reactor_selector = """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true" android:drawable="@drawable/ic_sd_reactor_pressed" />
    <item android:drawable="@drawable/ic_sd_reactor_idle" />
</selector>
"""
    write_text("res/drawable/bg_sd_launch_reactor.xml", reactor_selector)
    write_text("res/drawable/bg_lucifer_portal.xml", reactor_selector)

    # Upgrade Global Action, Nav, Header, Profile Card, Account Spinner & Chips
    write_text(
        "res/drawable/bg_lucifer_action.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_enabled="false">
        <shape android:shape="rectangle">
            <solid android:color="#66120B24" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#4400D4FF" />
        </shape>
    </item>
    <item android:state_pressed="true">
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#FFD946EF" android:endColor="#FF00D4FF" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#FFFFFFFF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#FF00D4FF" android:centerColor="#FF7C3AED" android:endColor="#FFD946EF" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#AAFFFFFF" />
        </shape>
    </item>
</selector>
""",
    )

    write_text(
        "res/drawable/bg_lucifer_nav_item.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_selected="true">
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#5500D4FF" android:endColor="#55D946EF" />
            <corners android:radius="10dp" />
            <stroke android:width="1.5dp" android:color="#FF00D4FF" />
        </shape>
    </item>
    <item android:state_pressed="true">
        <shape android:shape="rectangle">
            <solid android:color="#4400D4FF" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#FFD946EF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <solid android:color="#CC0B071B" />
            <corners android:radius="10dp" />
            <stroke android:width="1dp" android:color="#6600D4FF" />
        </shape>
    </item>
</selector>
""",
    )

    write_text(
        "res/drawable/bg_lucifer_header.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#E8060410" android:centerColor="#E8120A26" android:endColor="#E8060410" />
        </shape>
    </item>
    <item android:gravity="bottom" android:height="1.5dp">
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#FF00D4FF" android:centerColor="#FFD946EF" android:endColor="#FF00D4FF" />
        </shape>
    </item>
</layer-list>
""",
    )

    write_text(
        "res/drawable/bg_home_profile_card.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <gradient android:angle="315" android:startColor="#D90B071B" android:endColor="#D9160D30" />
    <corners android:radius="10dp" />
    <stroke android:width="1dp" android:color="#668B5CF6" />
</shape>
""",
    )

    write_text(
        "res/drawable/bg_home_profile_card_selected.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <gradient android:angle="0" android:startColor="#4400D4FF" android:endColor="#44D946EF" />
            <corners android:radius="10dp" />
            <stroke android:width="1.8dp" android:color="#FF00D4FF" />
        </shape>
    </item>
</layer-list>
""",
    )

    write_text(
        "res/drawable/bg_account_spinner.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <gradient android:angle="0" android:startColor="#E6090618" android:endColor="#E6170D30" />
    <corners android:radius="9dp" />
    <stroke android:width="1dp" android:color="#99D946EF" />
</shape>
""",
    )

    write_text(
        "res/drawable/bg_settings_btn.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true">
        <shape android:shape="rectangle">
            <solid android:color="#5500D4FF" />
            <corners android:radius="9dp" />
            <stroke android:width="1dp" android:color="#FF00D4FF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <solid android:color="#E60C081E" />
            <corners android:radius="9dp" />
            <stroke android:width="1dp" android:color="#8800D4FF" />
        </shape>
    </item>
</selector>
""",
    )

    write_text(
        "res/drawable/bg_chip_dark.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="#CC0D0820" />
    <corners android:radius="7dp" />
    <stroke android:width="1dp" android:color="#7700D4FF" />
</shape>
""",
    )


def generate_layouts() -> None:
    # 1. Root Landscape Shell: 3-Module Top Tactical HUD + Center Stage + Bottom Crystal-Shard Dock (#02 + #05)
    write_text(
        "res/layout-land/activity_pojav_launcher.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:fitsSystemWindows="false"
    android:background="?attr/bgMainDrawable">

    <!-- ═══════════════════════════════════════════════════════════════════════
         TOP 3-MODULE SHADOW-DRAGON TACTICAL HUD BAR (#02 + #05 Fusion)
         ═══════════════════════════════════════════════════════════════════════ -->
    <LinearLayout
        android:id="@+id/header_bar"
        android:layout_width="0dp"
        android:layout_height="@dimen/_42sdp"
        android:layout_marginTop="@dimen/_4sdp"
        android:layout_marginHorizontal="@dimen/_8sdp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:elevation="8dp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent">

        <!-- MODULE 1: Left Angled Horned LUCIFER Crest -->
        <LinearLayout
            android:id="@+id/hud_brand_plate"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:orientation="horizontal"
            android:gravity="center_vertical"
            android:paddingHorizontal="@dimen/_10sdp"
            android:background="@drawable/bg_sd_hud_plate">

            <FrameLayout
                android:id="@+id/btn_home_logo"
                android:layout_width="@dimen/_28sdp"
                android:layout_height="@dimen/_28sdp"
                android:clickable="true"
                android:focusable="true"
                android:contentDescription="Lucifer Launcher home">
                <ImageView
                    android:id="@+id/iv_lucifer_logo"
                    android:layout_width="match_parent"
                    android:layout_height="match_parent"
                    android:src="@drawable/lucifer_launcher_emblem"
                    android:scaleType="fitCenter"
                    android:contentDescription="Lucifer Launcher logo" />
            </FrameLayout>

            <TextView
                android:id="@+id/tv_launcher_title"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginStart="@dimen/_6sdp"
                android:text="LUCIFER"
                android:textSize="@dimen/_13ssp"
                android:textStyle="bold"
                android:textColor="@color/text_primary_white"
                android:letterSpacing="0.12"
                android:maxLines="1"
                android:clickable="true"
                android:focusable="true" />
        </LinearLayout>

        <Space
            android:layout_width="0dp"
            android:layout_height="1dp"
            android:layout_weight="1" />

        <!-- MODULE 2: Center Live Vulkan / FPS / RAM Telemetry Strip + Quick Studio Pills -->
        <LinearLayout
            android:id="@+id/hud_telemetry_plate"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:orientation="horizontal"
            android:gravity="center_vertical"
            android:paddingHorizontal="@dimen/_10sdp"
            android:background="@drawable/bg_sd_hud_plate"
            android:clickable="true"
            android:focusable="true">

            <TextView
                android:id="@+id/tv_hud_renderer"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="VULKAN 1.3"
                android:textColor="@color/sd_cyan"
                android:textSize="@dimen/_8ssp"
                android:textStyle="bold"
                android:letterSpacing="0.06" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginHorizontal="@dimen/_5sdp"
                android:text="•"
                android:textColor="@color/sd_magenta"
                android:textSize="@dimen/_9ssp" />

            <TextView
                android:id="@+id/tv_hud_fps"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="144 FPS"
                android:textColor="@color/text_primary_white"
                android:textSize="@dimen/_8ssp"
                android:textStyle="bold" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginHorizontal="@dimen/_5sdp"
                android:text="•"
                android:textColor="@color/sd_magenta"
                android:textSize="@dimen/_9ssp" />

            <TextView
                android:id="@+id/tv_hud_ram"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="6.0 GB RAM"
                android:textColor="@color/sd_magenta_bright"
                android:textSize="@dimen/_8ssp"
                android:textStyle="bold" />

            <View
                android:layout_width="1dp"
                android:layout_height="@dimen/_18sdp"
                android:layout_marginHorizontal="@dimen/_7sdp"
                android:background="#5500D4FF" />

            <LinearLayout
                android:id="@+id/nav_wallpapers"
                android:layout_width="wrap_content"
                android:layout_height="@dimen/_26sdp"
                android:gravity="center"
                android:paddingHorizontal="@dimen/_6sdp"
                android:background="@drawable/bg_lucifer_nav_item"
                android:clickable="true"
                android:focusable="true"
                android:contentDescription="@string/nav_wallpapers">
                <ImageView
                    android:id="@+id/nav_wallpapers_icon"
                    android:layout_width="@dimen/_11sdp"
                    android:layout_height="@dimen/_11sdp"
                    android:src="@drawable/ic_wallpaper"
                    android:tint="@color/sd_cyan"
                    android:contentDescription="@null" />
                <TextView
                    android:id="@+id/nav_wallpapers_label"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:layout_marginStart="@dimen/_3sdp"
                    android:text="Scene"
                    android:textColor="@color/text_primary_white"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold" />
            </LinearLayout>

            <LinearLayout
                android:id="@+id/nav_cursor"
                android:layout_width="wrap_content"
                android:layout_height="@dimen/_26sdp"
                android:layout_marginStart="@dimen/_4sdp"
                android:gravity="center"
                android:paddingHorizontal="@dimen/_6sdp"
                android:background="@drawable/bg_lucifer_nav_item"
                android:clickable="true"
                android:focusable="true"
                android:contentDescription="Cursor Studio">
                <ImageView
                    android:id="@+id/nav_cursor_icon"
                    android:layout_width="@dimen/_11sdp"
                    android:layout_height="@dimen/_11sdp"
                    android:src="@drawable/ic_mouse_pointer"
                    android:tint="@color/sd_magenta_bright"
                    android:contentDescription="@null" />
                <TextView
                    android:id="@+id/nav_cursor_label"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:layout_marginStart="@dimen/_3sdp"
                    android:text="Cursor"
                    android:textColor="@color/text_primary_white"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold" />
            </LinearLayout>

            <LinearLayout
                android:id="@+id/nav_about"
                android:layout_width="wrap_content"
                android:layout_height="@dimen/_26sdp"
                android:layout_marginStart="@dimen/_4sdp"
                android:gravity="center"
                android:paddingHorizontal="@dimen/_6sdp"
                android:background="@drawable/bg_lucifer_nav_item"
                android:clickable="true"
                android:focusable="true"
                android:contentDescription="About Lucifer Launcher">
                <ImageView
                    android:id="@+id/nav_about_icon"
                    android:layout_width="@dimen/_11sdp"
                    android:layout_height="@dimen/_11sdp"
                    android:src="@drawable/ic_menu_news"
                    android:tint="@color/sd_cyan"
                    android:contentDescription="@null" />
            </LinearLayout>

            <Button
                android:id="@+id/btn_creator_team"
                android:layout_width="wrap_content"
                android:layout_height="@dimen/_26sdp"
                android:layout_marginStart="@dimen/_4sdp"
                android:minWidth="@dimen/_34sdp"
                android:paddingHorizontal="@dimen/_6sdp"
                android:text="✦ PRO"
                android:textSize="@dimen/_7ssp"
                android:textStyle="bold"
                android:textColor="@color/sd_magenta_bright"
                android:background="@drawable/bg_lucifer_nav_item"
                android:contentDescription="Creator team credits" />
        </LinearLayout>

        <Space
            android:layout_width="0dp"
            android:layout_height="1dp"
            android:layout_weight="1" />

        <!-- MODULE 3: Right Angled Player Account & Settings Plate -->
        <LinearLayout
            android:id="@+id/hud_account_plate"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:orientation="horizontal"
            android:gravity="center_vertical"
            android:paddingHorizontal="@dimen/_6sdp"
            android:background="@drawable/bg_sd_hud_plate">

            <com.kdt.mcgui.mcAccountSpinner
                android:id="@+id/account_spinner"
                android:layout_width="@dimen/_124sdp"
                android:layout_height="@dimen/_32sdp"
                android:dropDownWidth="wrap_content"
                android:dropDownVerticalOffset="@dimen/_36sdp"
                android:background="@drawable/bg_account_spinner"
                android:paddingStart="@dimen/_5sdp"
                android:paddingEnd="@dimen/_5sdp" />

            <ImageButton
                android:id="@+id/setting_button"
                android:layout_width="@dimen/_32sdp"
                android:layout_height="@dimen/_32sdp"
                android:layout_marginStart="@dimen/_4sdp"
                android:background="@drawable/bg_settings_btn"
                android:src="@drawable/ic_menu_settings"
                android:tint="@color/sd_cyan"
                android:scaleType="fitCenter"
                android:padding="@dimen/_6sdp"
                android:contentDescription="Settings"
                android:clickable="true"
                android:focusable="true" />
        </LinearLayout>
    </LinearLayout>

    <!-- ═══════════════════════════════════════════════════════════════════════
         MAIN CONTENT STAGE (Home / Profiles / Mods / Servers / Skins)
         ═══════════════════════════════════════════════════════════════════════ -->
    <androidx.fragment.app.FragmentContainerView
        android:id="@+id/container_fragment"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_marginTop="@dimen/_3sdp"
        android:layout_marginBottom="@dimen/_3sdp"
        app:layout_constraintTop_toBottomOf="@+id/header_bar"
        app:layout_constraintBottom_toTopOf="@+id/bottom_dock_bar" />

    <com.kdt.mcgui.ProgressLayout
        android:id="@+id/progress_layout"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:elevation="12dp"
        android:layout_marginStart="@dimen/padding_large"
        android:layout_marginEnd="@dimen/padding_large"
        android:layout_marginTop="4dp"
        app:layout_constraintTop_toBottomOf="@+id/header_bar"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />

    <!-- ═══════════════════════════════════════════════════════════════════════
         BOTTOM FLOATING SHADOW-DRAGON CRYSTAL DOCK (#02 + #05 Signature)
         ═══════════════════════════════════════════════════════════════════════ -->
    <LinearLayout
        android:id="@+id/bottom_dock_bar"
        android:layout_width="wrap_content"
        android:layout_height="@dimen/_42sdp"
        android:layout_marginBottom="@dimen/_4sdp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:elevation="10dp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent">

        <ImageView
            android:layout_width="@dimen/_24sdp"
            android:layout_height="@dimen/_36sdp"
            android:layout_marginEnd="-4dp"
            android:src="@drawable/ic_sd_dock_crystals_left"
            android:contentDescription="@null" />

        <HorizontalScrollView
            android:id="@+id/nav_scroll"
            android:layout_width="wrap_content"
            android:layout_height="match_parent"
            android:background="@drawable/bg_sd_dock_shell"
            android:paddingHorizontal="@dimen/_8sdp"
            android:overScrollMode="never"
            android:scrollbars="none">

            <LinearLayout
                android:layout_width="wrap_content"
                android:layout_height="match_parent"
                android:gravity="center_vertical"
                android:orientation="horizontal">

                <LinearLayout
                    android:id="@+id/nav_home"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Home">
                    <ImageView android:id="@+id/nav_home_icon" style="@style/LuciferDockIcon" android:src="@drawable/ic_home" />
                    <TextView android:id="@+id/nav_home_label" style="@style/LuciferDockLabel" android:text="HOME" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/nav_instances"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Profiles">
                    <ImageView android:id="@+id/nav_instances_icon" style="@style/LuciferDockIcon" android:src="@drawable/ic_folder_managed" />
                    <TextView android:id="@+id/nav_instances_label" style="@style/LuciferDockLabel" android:text="PROFILES" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/nav_mod_store"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Mods">
                    <ImageView android:id="@+id/nav_mod_store_icon" style="@style/LuciferDockIcon" android:src="@drawable/ic_download_box" />
                    <TextView android:id="@+id/nav_mod_store_label" style="@style/LuciferDockLabel" android:text="MODS" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/nav_servers"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Servers">
                    <ImageView android:id="@+id/nav_servers_icon" style="@style/LuciferDockIcon" android:src="@drawable/ic_mc_block" />
                    <TextView android:id="@+id/nav_servers_label" style="@style/LuciferDockLabel" android:text="SERVERS" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/nav_custom_controls"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Controls">
                    <ImageView android:id="@+id/nav_controls_icon" style="@style/LuciferDockIcon" android:src="@drawable/ic_menu_custom_controls" />
                    <TextView android:id="@+id/nav_controls_label" style="@style/LuciferDockLabel" android:text="CONTROLS" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/nav_skin"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Skins">
                    <ImageView android:id="@+id/nav_skin_icon" style="@style/LuciferDockIcon" android:src="@drawable/ic_manage_skin" />
                    <TextView android:id="@+id/nav_skin_label" style="@style/LuciferDockLabel" android:text="SKINS" />
                </LinearLayout>

                <LinearLayout
                    android:id="@+id/nav_dock_settings"
                    style="@style/LuciferDockTab"
                    android:contentDescription="Settings">
                    <ImageView style="@style/LuciferDockIcon" android:src="@drawable/ic_menu_settings" android:tint="@color/sd_magenta_bright" />
                    <TextView style="@style/LuciferDockLabel" android:text="SETTINGS" />
                </LinearLayout>
            </LinearLayout>
        </HorizontalScrollView>

        <ImageView
            android:layout_width="@dimen/_24sdp"
            android:layout_height="@dimen/_36sdp"
            android:layout_marginStart="-4dp"
            android:src="@drawable/ic_sd_dock_crystals_right"
            android:contentDescription="@null" />
    </LinearLayout>

</androidx.constraintlayout.widget.ConstraintLayout>
""",
    )

    # 2. Portrait Fallback Shell (clean Shadow-Dragon header + safe IDs)
    write_text(
        "res/layout/activity_pojav_launcher.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="?attr/bgMainDrawable">

    <LinearLayout
        android:id="@+id/portrait_header"
        android:layout_width="match_parent"
        android:layout_height="@dimen/_52sdp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:paddingHorizontal="@dimen/_8sdp"
        android:background="@drawable/bg_lucifer_header"
        app:layout_constraintTop_toTopOf="parent">

        <ImageView
            android:layout_width="@dimen/_30sdp"
            android:layout_height="@dimen/_30sdp"
            android:src="@drawable/lucifer_launcher_emblem"
            android:contentDescription="Lucifer Launcher" />

        <com.kdt.mcgui.mcAccountSpinner
            android:id="@+id/account_spinner"
            android:layout_width="0dp"
            android:layout_height="@dimen/_38sdp"
            android:layout_weight="1"
            android:layout_marginHorizontal="@dimen/_8sdp"
            android:background="@drawable/bg_account_spinner"
            android:dropDownWidth="@dimen/_240sdp"
            android:dropDownVerticalOffset="@dimen/_42sdp" />

        <ImageButton
            android:id="@+id/setting_button"
            android:layout_width="@dimen/_38sdp"
            android:layout_height="@dimen/_38sdp"
            android:background="@drawable/bg_settings_btn"
            android:src="@drawable/ic_menu_settings"
            android:tint="@color/sd_cyan"
            android:scaleType="fitCenter"
            android:padding="@dimen/_8sdp"
            android:contentDescription="Settings" />
    </LinearLayout>

    <androidx.fragment.app.FragmentContainerView
        android:id="@+id/container_fragment"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        app:layout_constraintBottom_toTopOf="@+id/progress_layout"
        app:layout_constraintTop_toBottomOf="@+id/portrait_header" />

    <com.kdt.mcgui.ProgressLayout
        android:id="@+id/progress_layout"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        app:layout_constraintBottom_toBottomOf="parent" />

</androidx.constraintlayout.widget.ConstraintLayout>
""",
    )

    # 3. Home Sanctum Screen (#02 Shadow Monarch + #05 Ender Dragon Cataclysm exact 3-column composition!)
    write_text(
        "res/layout/fragment_right_pane_home.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@android:color/transparent">

    <!-- Optional custom user wallpaper layer -->
    <ImageView
        android:id="@+id/right_pane_wallpaper"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:scaleType="centerCrop"
        android:alpha="0.32"
        android:visibility="gone"
        android:contentDescription="@null" />

    <androidx.constraintlayout.widget.Guideline
        android:id="@+id/guide_left_col"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        app:layout_constraintGuide_percent="0.41" />

    <androidx.constraintlayout.widget.Guideline
        android:id="@+id/guide_right_col"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        app:layout_constraintGuide_percent="0.69" />

    <!-- ═══════════════════════════════════════════════════════════════════════
         LEFT COMBAT STACK (#02 + #05: LUCIFERMC Card + Active Build Crystal Card)
         ═══════════════════════════════════════════════════════════════════════ -->
    <LinearLayout
        android:id="@+id/home_left_stack"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:layout_marginStart="@dimen/_8sdp"
        android:layout_marginEnd="@dimen/_4sdp"
        android:layout_marginVertical="@dimen/_2sdp"
        android:orientation="vertical"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toStartOf="@id/guide_left_col">

        <!-- CARD 1: LUCIFERMC — LIFESTEEL SMP Official Server Crystal Shard -->
        <LinearLayout
            android:id="@+id/home_server_card"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:paddingHorizontal="@dimen/_10sdp"
            android:paddingVertical="@dimen/_8sdp"
            android:background="@drawable/bg_sd_crystal_card"
            android:clickable="true"
            android:focusable="true">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:gravity="center_vertical">

                <TextView
                    android:id="@+id/tv_home_server_pitch"
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    android:layout_weight="1"
                    android:text="LUCIFERMC — LIFESTEEL SMP"
                    android:textColor="@color/text_primary_white"
                    android:textSize="@dimen/_10ssp"
                    android:textStyle="bold"
                    android:letterSpacing="0.04"
                    android:maxLines="1"
                    android:ellipsize="end" />

                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:paddingHorizontal="@dimen/_6sdp"
                    android:paddingVertical="@dimen/_2sdp"
                    android:background="@drawable/bg_sd_badge_magenta"
                    android:text="OFFICIAL"
                    android:textColor="#FFFFFF"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:letterSpacing="0.08" />
            </LinearLayout>

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="@dimen/_2sdp"
                android:orientation="horizontal"
                android:gravity="center_vertical">

                <TextView
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    android:layout_weight="1"
                    android:text="play.lucifermc.fun"
                    android:textColor="@color/sd_cyan_bright"
                    android:textSize="@dimen/_8ssp" />

                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="● LIVE · 24ms"
                    android:textColor="@color/sd_online_emerald"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold" />
            </LinearLayout>

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="@dimen/_6sdp"
                android:orientation="horizontal"
                android:gravity="center_vertical">

                <TextView
                    android:id="@+id/btn_home_servers"
                    android:layout_width="0dp"
                    android:layout_height="@dimen/_24sdp"
                    android:layout_weight="1.3"
                    android:gravity="center"
                    android:background="@drawable/bg_sd_join_cyan"
                    android:text="JOIN"
                    android:textColor="#040812"
                    android:textSize="@dimen/_9ssp"
                    android:textStyle="bold"
                    android:letterSpacing="0.12"
                    android:clickable="true"
                    android:focusable="true" />

                <LinearLayout
                    android:id="@+id/btn_home_discord"
                    android:layout_width="wrap_content"
                    android:layout_height="@dimen/_24sdp"
                    android:layout_marginStart="@dimen/_5sdp"
                    android:orientation="horizontal"
                    android:gravity="center"
                    android:paddingHorizontal="@dimen/_8sdp"
                    android:background="@drawable/bg_discord_join"
                    android:clickable="true"
                    android:focusable="true"
                    android:contentDescription="Join the Lucifer Launcher Discord server">
                    <ImageView
                        android:layout_width="@dimen/_13sdp"
                        android:layout_height="@dimen/_11sdp"
                        android:layout_marginEnd="@dimen/_3sdp"
                        android:src="@drawable/ic_discord_white"
                        android:contentDescription="@null" />
                    <TextView
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="DISCORD"
                        android:textColor="#FFFFFF"
                        android:textSize="@dimen/_7ssp"
                        android:textStyle="bold" />
                </LinearLayout>

                <TextView
                    android:id="@+id/btn_home_wiki"
                    android:layout_width="wrap_content"
                    android:layout_height="@dimen/_24sdp"
                    android:layout_marginStart="@dimen/_4sdp"
                    android:gravity="center"
                    android:paddingHorizontal="@dimen/_7sdp"
                    android:background="@drawable/bg_lucifer_nav_item"
                    android:text="WIKI"
                    android:textColor="@color/sd_cyan"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />
            </LinearLayout>
        </LinearLayout>

        <!-- CARD 2: Active Build & Quick-Switch Instance Crystal Shard -->
        <LinearLayout
            android:id="@+id/home_instance_card"
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1"
            android:layout_marginTop="@dimen/_5sdp"
            android:orientation="vertical"
            android:paddingHorizontal="@dimen/_10sdp"
            android:paddingVertical="@dimen/_7sdp"
            android:background="@drawable/bg_sd_crystal_card">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:gravity="center_vertical">

                <LinearLayout
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    android:layout_weight="1"
                    android:orientation="vertical">

                    <TextView
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:text="ACTIVE BUILD // VERSION"
                        android:textColor="@color/sd_magenta_bright"
                        android:textSize="@dimen/_7ssp"
                        android:textStyle="bold"
                        android:letterSpacing="0.14" />

                    <TextView
                        android:id="@+id/tv_home_profile_name"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:text="Select an instance"
                        android:textColor="@color/text_primary_white"
                        android:textSize="@dimen/_12ssp"
                        android:textStyle="bold"
                        android:maxLines="1"
                        android:ellipsize="end" />

                    <TextView
                        android:id="@+id/tv_home_version"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:text="Choose a Minecraft version"
                        android:textColor="@color/sd_cyan_bright"
                        android:textSize="@dimen/_8ssp"
                        android:maxLines="1"
                        android:ellipsize="end" />
                </LinearLayout>

                <LinearLayout
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:orientation="vertical"
                    android:gravity="end">

                    <TextView
                        android:id="@+id/tv_home_loader"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:paddingHorizontal="@dimen/_6sdp"
                        android:paddingVertical="@dimen/_2sdp"
                        android:background="@drawable/bg_chip_dark"
                        android:text="Fabric"
                        android:textColor="@color/sd_cyan"
                        android:textSize="@dimen/_7ssp"
                        android:textStyle="bold" />

                    <TextView
                        android:id="@+id/tv_home_ram"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="@dimen/_2sdp"
                        android:paddingHorizontal="@dimen/_6sdp"
                        android:paddingVertical="@dimen/_2sdp"
                        android:background="@drawable/bg_chip_dark"
                        android:text="RAM —"
                        android:textColor="@color/sd_magenta_bright"
                        android:textSize="@dimen/_7ssp"
                        android:textStyle="bold" />
                </LinearLayout>
            </LinearLayout>

            <!-- Action Pills Row -->
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="@dimen/_4sdp"
                android:orientation="horizontal"
                android:gravity="center_vertical">

                <TextView
                    android:id="@+id/btn_home_instances"
                    android:layout_width="0dp"
                    android:layout_height="@dimen/_20sdp"
                    android:layout_weight="1.2"
                    android:gravity="center"
                    android:background="@drawable/bg_lucifer_nav_item"
                    android:text="PROFILES"
                    android:textColor="@color/text_primary_white"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />

                <TextView
                    android:id="@+id/btn_open_mods_folder"
                    android:layout_width="0dp"
                    android:layout_height="@dimen/_20sdp"
                    android:layout_weight="1.1"
                    android:layout_marginStart="@dimen/_3sdp"
                    android:gravity="center"
                    android:background="@drawable/bg_lucifer_nav_item"
                    android:text="MODS DIR"
                    android:textColor="@color/sd_cyan"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />

                <TextView
                    android:id="@+id/fab_create_profile"
                    android:layout_width="0dp"
                    android:layout_height="@dimen/_20sdp"
                    android:layout_weight="1"
                    android:layout_marginStart="@dimen/_3sdp"
                    android:gravity="center"
                    android:background="@drawable/bg_lucifer_action"
                    android:text="＋ NEW"
                    android:textColor="#FFFFFF"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />

                <TextView
                    android:id="@+id/btn_refresh_profiles"
                    android:layout_width="@dimen/_22sdp"
                    android:layout_height="@dimen/_20sdp"
                    android:layout_marginStart="@dimen/_3sdp"
                    android:gravity="center"
                    android:background="@drawable/bg_lucifer_nav_item"
                    android:text="↻"
                    android:textColor="@color/sd_cyan"
                    android:textSize="@dimen/_9ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />
            </LinearLayout>

            <!-- Quick-Switch Crystal Profile Strip -->
            <androidx.recyclerview.widget.RecyclerView
                android:id="@+id/rv_home_profiles"
                android:layout_width="match_parent"
                android:layout_height="0dp"
                android:layout_weight="1"
                android:layout_marginTop="@dimen/_4sdp"
                android:clipToPadding="false"
                android:overScrollMode="never" />
        </LinearLayout>
    </LinearLayout>

    <!-- ═══════════════════════════════════════════════════════════════════════
         CENTER HERO STAGE (#02 Shadow Monarch Flames + #05 Dragon Pedestal)
         ═══════════════════════════════════════════════════════════════════════ -->
    <FrameLayout
        android:id="@+id/home_avatar_shell"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:layout_marginHorizontal="@dimen/_2sdp"
        android:background="@drawable/bg_sd_shadow_flame_stage"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toEndOf="@id/guide_left_col"
        app:layout_constraintEnd_toStartOf="@id/guide_right_col">

        <ImageView
            android:id="@+id/iv_home_avatar"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:layout_marginTop="@dimen/_8sdp"
            android:layout_marginBottom="@dimen/_24sdp"
            android:layout_gravity="center"
            android:scaleType="fitCenter"
            android:contentDescription="@string/player_skin_preview" />

        <TextView
            android:id="@+id/btn_home_skins"
            android:layout_width="wrap_content"
            android:layout_height="@dimen/_21sdp"
            android:layout_gravity="bottom|center_horizontal"
            android:layout_marginBottom="@dimen/_3sdp"
            android:gravity="center"
            android:paddingHorizontal="@dimen/_10sdp"
            android:background="@drawable/bg_sd_hud_plate"
            android:text="✦ SKIN STUDIO"
            android:textColor="@color/sd_cyan_bright"
            android:textSize="@dimen/_7ssp"
            android:textStyle="bold"
            android:letterSpacing="0.1"
            android:clickable="true"
            android:focusable="true" />
    </FrameLayout>

    <!-- ═══════════════════════════════════════════════════════════════════════
         RIGHT DRAGON-PLASMA LAUNCH ZONE (#05 Crystal Spikes + #02 Plasma PLAY)
         ═══════════════════════════════════════════════════════════════════════ -->
    <LinearLayout
        android:id="@+id/home_right_reactor_col"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:layout_marginStart="@dimen/_4sdp"
        android:layout_marginEnd="@dimen/_8sdp"
        android:layout_marginVertical="@dimen/_2sdp"
        android:orientation="vertical"
        android:gravity="center"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toEndOf="@id/guide_right_col"
        app:layout_constraintEnd_toEndOf="parent">

        <!-- Compact Arsenal Quick-Trigger Card -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:paddingHorizontal="@dimen/_9sdp"
            android:paddingVertical="@dimen/_6sdp"
            android:background="@drawable/bg_sd_crystal_card">

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="SHADOW DRAGON ARSENAL"
                android:textColor="@color/sd_cyan"
                android:textSize="@dimen/_7ssp"
                android:textStyle="bold"
                android:letterSpacing="0.12" />

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="@dimen/_4sdp"
                android:orientation="horizontal">

                <TextView
                    android:id="@+id/btn_home_mod_shortcut"
                    android:layout_width="0dp"
                    android:layout_height="@dimen/_22sdp"
                    android:layout_weight="1"
                    android:gravity="center"
                    android:background="@drawable/bg_lucifer_nav_item"
                    android:text="⚡ MOD STORE"
                    android:textColor="@color/text_primary_white"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />

                <TextView
                    android:id="@+id/btn_home_controls_shortcut"
                    android:layout_width="0dp"
                    android:layout_height="@dimen/_22sdp"
                    android:layout_weight="1"
                    android:layout_marginStart="@dimen/_4sdp"
                    android:gravity="center"
                    android:background="@drawable/bg_lucifer_nav_item"
                    android:text="🎮 HUD KEYS"
                    android:textColor="@color/sd_magenta_bright"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:clickable="true"
                    android:focusable="true" />
            </LinearLayout>
        </LinearLayout>

        <!-- DRAGON-MONARCH CATACLYSM PLAY REACTOR -->
        <FrameLayout
            android:id="@+id/btn_launch_portal"
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1"
            android:layout_marginTop="@dimen/_5sdp"
            android:background="@drawable/bg_sd_launch_reactor"
            android:clickable="true"
            android:focusable="true"
            android:contentDescription="Launch selected Minecraft instance">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:gravity="center"
                android:orientation="vertical"
                android:paddingHorizontal="@dimen/_14sdp">

                <TextView
                    android:id="@+id/tv_launch_glyph"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="⚡"
                    android:textColor="@color/sd_cyan_bright"
                    android:textSize="@dimen/_15ssp" />

                <TextView
                    android:id="@+id/tv_launch_label"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="PLAY"
                    android:textColor="#FFFFFF"
                    android:textSize="@dimen/_17ssp"
                    android:textStyle="bold"
                    android:letterSpacing="0.14" />

                <TextView
                    android:id="@+id/tv_launch_version_sub"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="SHADOW DRAGON READY"
                    android:textColor="@color/sd_cyan_bright"
                    android:textSize="@dimen/_7ssp"
                    android:textStyle="bold"
                    android:maxLines="1"
                    android:ellipsize="end" />
            </LinearLayout>
        </FrameLayout>
    </LinearLayout>

</androidx.constraintlayout.widget.ConstraintLayout>
""",
    )

    # 4. Compact Crystal Profile Card inside Home Quick-Switch Strip
    write_text(
        "res/layout/item_home_profile_card.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/card_profile_root"
    android:layout_width="@dimen/_168sdp"
    android:layout_height="match_parent"
    android:minHeight="@dimen/_42sdp"
    android:layout_marginEnd="@dimen/_5sdp"
    android:background="@drawable/bg_home_profile_card"
    android:clickable="true"
    android:focusable="true"
    android:paddingHorizontal="@dimen/_6sdp"
    android:paddingVertical="@dimen/_4sdp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="horizontal"
        android:gravity="center_vertical">

        <ImageView
            android:id="@+id/img_profile_icon"
            android:layout_width="@dimen/_26sdp"
            android:layout_height="@dimen/_26sdp"
            android:layout_marginEnd="@dimen/_6sdp"
            android:scaleType="fitCenter"
            android:background="@drawable/bg_profile_icon_rounded"
            android:padding="@dimen/_2sdp"
            android:contentDescription="Instance icon" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical">

            <TextView
                android:id="@+id/tv_profile_name"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:textColor="@color/text_primary_white"
                android:textSize="@dimen/_8ssp"
                android:textStyle="bold"
                android:maxLines="1"
                android:ellipsize="end" />

            <TextView
                android:id="@+id/tv_profile_meta"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:textColor="@color/sd_cyan_bright"
                android:textSize="@dimen/_6ssp"
                android:maxLines="1"
                android:ellipsize="end" />

            <TextView
                android:id="@+id/tv_profile_mod_count"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:textColor="@color/sd_magenta_bright"
                android:textSize="@dimen/_6ssp"
                android:maxLines="1"
                android:ellipsize="end"
                android:text="Mods: 0" />
        </LinearLayout>

        <ImageButton
            android:id="@+id/btn_profile_edit"
            android:layout_width="@dimen/_22sdp"
            android:layout_height="@dimen/_22sdp"
            android:background="?android:attr/selectableItemBackgroundBorderless"
            android:contentDescription="Edit instance"
            android:padding="@dimen/_4sdp"
            android:tint="@color/sd_cyan"
            android:src="@drawable/ic_edit_profile" />

        <FrameLayout
            android:id="@+id/btn_profile_play"
            android:layout_width="@dimen/_34sdp"
            android:layout_height="@dimen/_22sdp"
            android:layout_marginStart="@dimen/_3sdp"
            android:background="@drawable/bg_sd_join_cyan"
            android:clickable="true"
            android:focusable="true"
            android:contentDescription="Launch this instance">
            <TextView
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:gravity="center"
                android:text="GO"
                android:textColor="#040812"
                android:textSize="@dimen/_7ssp"
                android:textStyle="bold" />
        </FrameLayout>
    </LinearLayout>
</FrameLayout>
""",
    )


def generate_java() -> None:
    # 1. Upgrade LauncherActivity.java to wire live Vulkan/FPS/RAM telemetry + Bottom Dock Settings tab
    with open(
        os.path.join(SRC_BASE, "java/net/kdt/pojavlaunch/LauncherActivity.java"),
        encoding="utf-8",
    ) as fh:
        la = fh.read()

    # Wire dock settings + telemetry strip in setupNavButtons()
    old_nav_tail = "        updateNavSkinIcon();\n    }"
    new_nav_tail = """        View navDockSettings = findViewById(R.id.nav_dock_settings);
        if (navDockSettings != null) {
            navDockSettings.setOnClickListener(mSettingButtonListener);
        }
        View telemetryPlate = findViewById(R.id.hud_telemetry_plate);
        if (telemetryPlate != null) {
            telemetryPlate.setOnClickListener(mSettingButtonListener);
        }
        refreshShadowDragonTelemetry();
        updateNavSkinIcon();
    }

    private void refreshShadowDragonTelemetry() {
        android.widget.TextView tvRenderer = findViewById(R.id.tv_hud_renderer);
        android.widget.TextView tvFps = findViewById(R.id.tv_hud_fps);
        android.widget.TextView tvRam = findViewById(R.id.tv_hud_ram);
        if (tvRenderer != null && LauncherPreferences.DEFAULT_PREF != null) {
            String raw = LauncherPreferences.DEFAULT_PREF.getString("renderer", "vulkan_zink");
            String label = "VULKAN 1.3";
            if (raw != null) {
                String lower = raw.toLowerCase(java.util.Locale.ROOT);
                if (lower.contains("zink") || lower.contains("vulkan")) label = "VULKAN ZINK";
                else if (lower.contains("ltw") || lower.contains("gl4es") || lower.contains("holy")) label = "GL4ES TURBO";
                else if (lower.contains("angle") || lower.contains("mg")) label = "MOBILEGLUES";
            }
            tvRenderer.setText(label);
        }
        if (tvFps != null) {
            tvFps.setText(LauncherPreferences.PREF_HIGH_FPS_MODE ? "144 FPS BOOST" : "120 FPS READY");
        }
        if (tvRam != null && LauncherPreferences.PREF_RAM_ALLOCATION > 0) {
            tvRam.setText(String.format(java.util.Locale.US, "%.1f GB RAM",
                    LauncherPreferences.PREF_RAM_ALLOCATION / 1024.0));
        }
    }"""
    assert old_nav_tail in la, "Could not locate setupNavButtons tail in LauncherActivity.java"
    la = la.replace(old_nav_tail, new_nav_tail, 1)

    # Refresh telemetry on resume as well
    old_resume = "        mInstallTracker.attach();"
    new_resume = "        refreshShadowDragonTelemetry();\n        mInstallTracker.attach();"
    assert old_resume in la, "Could not locate onResume hook in LauncherActivity.java"
    la = la.replace(old_resume, new_resume, 1)

    # Highlight nav_dock_settings when Settings is active
    la = la.replace(
        "R.id.nav_skin, R.id.nav_about,\n                R.id.btn_creator_team};",
        "R.id.nav_skin, R.id.nav_about,\n                R.id.btn_creator_team, R.id.nav_dock_settings};",
    )
    la = la.replace(
        "        } else if (fragment instanceof CreatorTeamFragment) {\n            activeId = R.id.btn_creator_team;\n        }",
        "        } else if (fragment instanceof CreatorTeamFragment) {\n            activeId = R.id.btn_creator_team;\n        } else if (fragment instanceof LauncherPreferenceFragment) {\n            activeId = R.id.nav_dock_settings;\n        }",
    )

    write_text("java/net/kdt/pojavlaunch/LauncherActivity.java", la)

    # 2. Upgrade RightPaneHomeFragment.java to wire Mod Store / Controls shortcuts + live Launch Reactor version label
    with open(
        os.path.join(
            SRC_BASE, "java/net/kdt/pojavlaunch/fragments/RightPaneHomeFragment.java"
        ),
        encoding="utf-8",
    ) as fh:
        rph = fh.read()

    rph = rph.replace(
        "    private TextView mRam;\n",
        "    private TextView mRam;\n    private TextView mLaunchVersionSub;\n",
        1,
    )
    rph = rph.replace(
        "        mRam = view.findViewById(R.id.tv_home_ram);\n",
        "        mRam = view.findViewById(R.id.tv_home_ram);\n        mLaunchVersionSub = view.findViewById(R.id.tv_launch_version_sub);\n",
        1,
    )

    extra_home_wiring = """        View modShortcut = view.findViewById(R.id.btn_home_mod_shortcut);
        if (modShortcut != null) {
            modShortcut.setOnClickListener(v -> openPane(
                    ModsSearchFragment.class, ModsSearchFragment.TAG, null));
        }
        View controlsShortcut = view.findViewById(R.id.btn_home_controls_shortcut);
        if (controlsShortcut != null) {
            controlsShortcut.setOnClickListener(v -> startActivity(
                    new android.content.Intent(requireContext(), net.kdt.pojavlaunch.CustomControlsActivity.class)));
        }

        bindAccountPreview();"""
    assert "        bindAccountPreview();" in rph
    rph = rph.replace("        bindAccountPreview();", extra_home_wiring, 1)

    rph = rph.replace(
        "        mRam = null;\n",
        "        mRam = null;\n        mLaunchVersionSub = null;\n",
        1,
    )

    # Sync tv_launch_version_sub inside updateSelectedInstance
    old_update = """        mRam.setText(getString(R.string.ram_summary_gb,
                LauncherPreferences.PREF_RAM_ALLOCATION / 1024.0));"""
    new_update = """        mRam.setText(getString(R.string.ram_summary_gb,
                LauncherPreferences.PREF_RAM_ALLOCATION / 1024.0));
        if (mLaunchVersionSub != null) {
            if (profile == null) {
                mLaunchVersionSub.setText("SELECT A BUILD");
            } else {
                mLaunchVersionSub.setText(ProfileVersionDisplay.format(profile.lastVersionId, profile.name).toUpperCase(Locale.ROOT));
            }
        }"""
    assert old_update in rph, "Could not locate updateSelectedInstance tail"
    rph = rph.replace(old_update, new_update, 1)

    write_text("java/net/kdt/pojavlaunch/fragments/RightPaneHomeFragment.java", rph)


def validate_against_base() -> None:
    """Validates XML syntax, resource references, and Java R.id/R.drawable references."""
    test_tree = "/tmp/v2-merged-verify"
    if os.path.exists(test_tree):
        shutil.rmtree(test_tree)
    shutil.copytree("/tmp/v2-src/app_pojavlauncher/src/main/res", os.path.join(test_tree, "res"))

    # Overlay our generated resources
    for root, _, files in os.walk(os.path.join(OUT_BASE, "res")):
        for f in files:
            src_f = os.path.join(root, f)
            rel_f = os.path.relpath(src_f, os.path.join(OUT_BASE, "res"))
            dst_f = os.path.join(test_tree, "res", rel_f)
            os.makedirs(os.path.dirname(dst_f), exist_ok=True)
            shutil.copy2(src_f, dst_f)

    # Parse every XML in our overhaul and collect defined drawables/colors/styles/ids
    drawables = set()
    colors = set()
    styles = set()
    strings = set()
    dimens = set()

    res_root = os.path.join(test_tree, "res")
    for folder in os.listdir(res_root):
        fpath = os.path.join(res_root, folder)
        if not os.path.isdir(fpath):
            continue
        if folder.startswith("drawable"):
            for fn in os.listdir(fpath):
                name = fn.split(".")[0]
                drawables.add(name)
        elif folder.startswith("values"):
            for fn in os.listdir(fpath):
                if not fn.endswith(".xml"):
                    continue
                tree = ET.parse(os.path.join(fpath, fn))
                for elem in tree.getroot():
                    n = elem.attrib.get("name")
                    if not n:
                        continue
                    if elem.tag == "color":
                        colors.add(n)
                    elif elem.tag == "style":
                        styles.add(n)
                    elif elem.tag == "string":
                        strings.add(n)
                    elif elem.tag == "dimen":
                        dimens.add(n)

    # Strictly parse and check every XML file we generated
    xml_count = 0
    ref_pattern = re.compile(r"@(drawable|color|style|string)/([A-Za-z0-9_.]+)")
    for root, _, files in os.walk(os.path.join(OUT_BASE, "res")):
        for f in files:
            if not f.endswith(".xml"):
                continue
            full = os.path.join(root, f)
            ET.parse(full)  # Raises ParseError on any malformed XML
            xml_count += 1
            txt = open(full, encoding="utf-8").read()
            for rtype, rname in ref_pattern.findall(txt):
                if rtype == "drawable" and rname not in drawables:
                    raise AssertionError(f"Missing @drawable/{rname} in {full}")
                if rtype == "color" and rname not in colors:
                    raise AssertionError(f"Missing @color/{rname} in {full}")
                if rtype == "style" and rname not in styles and not rname.startswith(("Theme.", "Widget.", "Preference")):
                    raise AssertionError(f"Missing @style/{rname} in {full}")
                if rtype == "string" and rname not in strings:
                    raise AssertionError(f"Missing @string/{rname} in {full}")

    print(f"VALIDATION PASSED: {xml_count} XML files parsed cleanly, 100% resource references verified!")
    shutil.rmtree(test_tree)


if __name__ == "__main__":
    generate_values()
    generate_drawables()
    generate_layouts()
    generate_java()
    validate_against_base()
