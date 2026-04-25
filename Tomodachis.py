#!/usr/bin/env python3
# Tomodachis — libadwaita GUI for Tomodachi Life: Living the Dream save data.
#
# Forked from ShareMii by Star-F0rce and Ben Rau.
# Original project: https://github.com/Star-F0rce/ShareMii
# Licensed under the GNU GPL v3.0 (see LICENSE).

import argparse
import io
import os
import re
import shutil
import stat
import struct
import sys
from datetime import datetime
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from ShareUGC import ugcStart

APP_ID = "com.pocoguy.Tomodachis"

majVersion = 3
minVersion = 2
patchVersion = 1
preVersion = 0
versionStr = (
    f"{majVersion}.{minVersion}"
    + (f".{patchVersion}" if patchVersion else "")
    + (f".pre{preVersion}" if preVersion else "")
)

ITEM_NAMES = ["Mii", "Food", "Clothing", "Treasure", "Interior", "Exterior", "Objects", "Landscaping"]
EXTENSIONS = [".ltd", ".ltdf", ".ltdc", ".ltdg", ".ltdi", ".ltde", ".ltdo", ".ltdl"]
EXTENSION_DESC = [
    "LtD Mii Files",
    "LtD Food Files",
    "LtD Cloth Files",
    "LtD Goods Files",
    "LtD Interior Files",
    "LtD Exterior Files",
    "LtD MapObject Files",
    "LtD MapFloor Files",
]
MODES = ["List", "Import", "Export", "Export All"]


# -----------------------------------------------------------------------------
# Save-file logic (ported from upstream ShareMii.py - same byte-level behavior)
# -----------------------------------------------------------------------------

def resourcePath(relativePath):
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basePath, relativePath)


def trimStr(path):
    if (path.startswith("'") and path.endswith("'")) or (path.startswith('"') and path.endswith('"')):
        path = path[1:-1]
    return path


def uniqueFile(filepath):
    if not os.path.exists(filepath):
        return filepath
    base, ext = os.path.splitext(filepath)
    counter = 1
    newFilepath = f"{base}_({counter}){ext}"
    while os.path.exists(newFilepath):
        counter += 1
        newFilepath = f"{base}_({counter}){ext}"
    return newFilepath


def offsetLocator(file, hashStr):
    hash = bytes.fromhex(hashStr)
    littleHash = hash[::-1]
    index = file.find(littleHash)
    if index == -1:
        return None
    offsetBytes = file[index + 4:index + 8]
    offset = struct.unpack('<I', offsetBytes)[0]
    return offset


def DecodeSexuality(data):
    return [int(bit) for byte in data for bit in f"{byte:08b}"[::-1]]


def EncodeSexuality(bits):
    if len(bits) % 8 != 0:
        raise ValueError("Bit list length must be a multiple of 8")
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        byte_str = ''.join(str(bit) for bit in byte_bits[::-1])
        result.append(int(byte_str, 2))
    return result


def ShareMii(mode, slot, save, miipath, backup=True):
    miipath = trimStr(miipath)
    save = trimStr(save)

    if mode == "List":
        slot = 1
    if slot > 70 or slot < 0:
        raise RuntimeError("Invalid slot. Please choose a slot 0-70.")
    slot -= 1

    with open(save + "/Mii.sav", "rb") as f:
        miisav = bytearray(f.read())
    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())

    fpOffset1 = offsetLocator(playersav, "4C9819E4") + 4
    fpOffset2 = offsetLocator(playersav, "DECC8954") + 4
    fpOffset3 = offsetLocator(playersav, "23135BC5") + 4
    fpOffset4 = offsetLocator(playersav, "FFC750B6") + 4
    fpOffset5 = offsetLocator(playersav, "A56E42EC") + 4
    miiOffset2 = offsetLocator(miisav, "5E32ADF4") + 4
    miiOffset3 = offsetLocator(playersav, "114EFF89")
    miiOffset4 = offsetLocator(miisav, "2499BFDA") + 4
    miiOffset5 = offsetLocator(miisav, "3A5EDA05") + 4
    miiOffset6 = offsetLocator(miisav, "881CA27A") + 4
    persOffsets = [
        offsetLocator(miisav, "43CD364F") + 4,
        offsetLocator(miisav, "CD8DBAF8") + 4,
        offsetLocator(miisav, "25B48224") + 4,
        offsetLocator(miisav, "607BA160") + 4,
        offsetLocator(miisav, "68E1134E") + 4,
        offsetLocator(miisav, "4913AE1A") + 4,
        offsetLocator(miisav, "141EE086") + 4,
        offsetLocator(miisav, "07B9D175") + 4,
        offsetLocator(miisav, "81CF470A") + 4,
        offsetLocator(miisav, "4D78E262") + 4,
        offsetLocator(miisav, "FBC3FFB0") + 4,
        offsetLocator(miisav, "236E2D73") + 4,
        offsetLocator(miisav, "F3C3DE59") + 4,
        offsetLocator(miisav, "660C5247") + 4,
        offsetLocator(miisav, "5D7D3F45") + 4,
        offsetLocator(miisav, "AB8AE08B") + 4,
        offsetLocator(miisav, "2545E583") + 4,
        offsetLocator(miisav, "6CF484F4") + 4,
    ]
    persOffsetSX = offsetLocator(miisav, "DFC82223") + 4

    miiindex = miiOffset6 + 156 * slot
    miinames = miiOffset4
    miiprefer = miiOffset5

    if mode == "List":
        for x in range(69):
            miiindex = miiOffset6 + 156 * x
            miilistname = miisav[miinames + x * 64:miinames + x * 64 + 64]
            if sum(miisav[miiindex:miiindex + 156]) != 152:
                printName = miilistname[:miilistname.find(bytes.fromhex("00 00 00"))]
                if len(printName) % 2 == 1:
                    printName.append(0)
                print(f"{x + 1} - {printName.decode('utf-16')}")
        return

    if mode == "Import":
        if backup:
            if not os.path.exists(r"./backup"):
                os.mkdir(r"./backup")
            backuppath = "./backup"
            shutil.copytree(save, backuppath + "/" + datetime.now().strftime("SaveData_Backup_%d_%m_%Y_%H%M%S"))

        with open(miipath, "rb") as f:
            mii = bytearray(f.read())

        if mii == bytearray():
            raise RuntimeError("This Mii is empty!")
        if mii[0] not in range(1, 4):
            raise RuntimeError("Incorrect version found. Expected 1-3, got " + str(mii[0]))

        if mii[0] < 3:
            del mii[4]
            if mii[0] == 2:
                mii = mii[:427] + bytearray([0]) + mii[427:]
                canvasStart = mii.find(bytes.fromhex("A3 A3 A3")) + 3
                ugcStartIdx = mii.rfind(bytes.fromhex("A3 A3 A3"))
                mii = mii[:canvasStart] + bytearray([163]) + mii[canvasStart:]
                mii[ugcStartIdx + 1:ugcStartIdx + 4] = bytearray.fromhex("A4 A4 A4")
                mii = mii[:ugcStartIdx + 3] + bytearray([164]) + mii[ugcStartIdx + 3:]

        paintindex = fpOffset3 + 4 * slot
        canvasStart = mii.find(bytes.fromhex("A3 A3 A3 A3")) + 4
        ugcStartIdx = mii.rfind(bytes.fromhex("A4 A4 A4 A4")) + 4
        facepaint = 0
        if slot == -1:
            paintindex = fpOffset3 + 4 * 70
            miiindex = miiOffset3

        if mii[1:3] == bytearray.fromhex('01 01'):
            facepaint = 1
            mii[47] = 1
        if os.path.isfile(miipath + ".canvas.zs") & os.path.isfile(miipath + ".ugctex.zs"):
            facepaint = 2
            mii[47] = 1

        if sum(miisav[miiindex:miiindex + 156]) == 152:
            raise RuntimeError("Mii not initialized! Please create a mii in this slot.")

        if slot == -1:
            print("Writing Mii to the temporary slot...")
            playersav[miiindex:miiindex + 156] = mii[4:4 + 156]
        else:
            print(f"Mii detected at {hex(miiindex)}! Replacing...")
            miisav[miiindex:miiindex + 156] = mii[4:4 + 156]

        if slot == -1:
            paintindex = fpOffset3 + 4 * 70
            if playersav[paintindex:paintindex + 4] != bytearray.fromhex('A5 8A FF AF'):
                facepaintID = 70
            else:
                facepaintID = 255
        else:
            facepaintID = miisav[miiOffset2 + 4 * slot]

        if facepaint:
            print("Facepaint detected! Copying...")
            if facepaintID == 255:
                usedIDs = bytearray([255] * 70)
                for x in range(70):
                    if miisav[miiOffset2 + 4 * x] != 255:
                        usedIDs[x] = miisav[miiOffset2 + 4 * x]
                s = set(usedIDs)
                for i in range(70):
                    if i not in s:
                        facepaintID = i
                        break

            if slot == -1:
                facepaintID = 70
            else:
                miisav[miiOffset2 + 4 * slot:miiOffset2 + 4 * slot + 4] = bytearray([facepaintID, 0, 0, 0])
            playersav[fpOffset1 + 4 * facepaintID:fpOffset1 + 4 * facepaintID + 4] = bytearray.fromhex('F4 01 00 00')
            playersav[fpOffset2 + 4 * facepaintID:fpOffset2 + 4 * facepaintID + 4] = bytearray.fromhex('41 49 93 56')
            playersav[fpOffset3 + 4 * facepaintID:fpOffset3 + 4 * facepaintID + 4] = bytearray.fromhex('F4 AD 7F 1D')
            playersav[fpOffset4 + 4 * facepaintID:fpOffset4 + 4 * facepaintID + 4] = bytearray.fromhex('00 80 00 00')
            playersav[fpOffset5 + 4 * facepaintID:fpOffset5 + 4 * facepaintID + 4] = bytearray([facepaintID, 0, 8, 0])

            facepaintFile = f"00{facepaintID}" if facepaintID < 10 else f"0{facepaintID}"
            UgcDir = Path(save + "/Ugc")
            UgcDir.mkdir(parents=True, exist_ok=True)

            if facepaint == 2:
                shutil.copy(miipath + ".canvas.zs", save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs")
                shutil.copy(miipath + ".ugctex.zs", save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs")
            else:
                with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs", "wb") as f:
                    f.write(mii[canvasStart:ugcStartIdx - 4])
                with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs", "wb") as f:
                    f.write(mii[ugcStartIdx:])
            print("Facepaint successfully copied to " + save + "/Ugc/UgcFacePaint" + facepaintFile)
        else:
            if facepaintID != 255:
                print("This new Mii no longer uses facepaint. Be sure to back up the old facepaint if you still want it.")
                if slot != -1:
                    miisav[miiOffset2 + 4 * slot:miiOffset2 + 4 * slot + 4] = bytearray.fromhex('FF FF FF FF')
                playersav[fpOffset1 + 4 * facepaintID:fpOffset1 + 4 * facepaintID + 4] = bytearray.fromhex('00 00 00 00')
                playersav[fpOffset2 + 4 * facepaintID:fpOffset2 + 4 * facepaintID + 4] = bytearray.fromhex('09 DE EE B6')
                playersav[fpOffset3 + 4 * facepaintID:fpOffset3 + 4 * facepaintID + 4] = bytearray.fromhex('A5 8A FF AF')
                playersav[fpOffset4 + 4 * facepaintID:fpOffset4 + 4 * facepaintID + 4] = bytearray.fromhex('00 00 00 00')
                playersav[fpOffset5 + 4 * facepaintID:fpOffset5 + 4 * facepaintID + 4] = bytearray.fromhex('00 00 00 00')

        if (mii[0] < 2) & (slot != -1):
            print("No personal data configured, skipping...")

        if (mii[0] >= 2) & (slot != -1):
            print("Personal data detected! Applying...")
            for x in range(18):
                miisav[persOffsets[x] + slot * 4:persOffsets[x] + slot * 4 + 4] = mii[160 + x * 4:160 + x * 4 + 4]
            miisav[miinames + slot * 64:miinames + slot * 64 + 64] = mii[232:296]
            miisav[miiprefer + slot * 128:miiprefer + slot * 128 + 128] = mii[296:424]
            miisexuality = list(mii[424:427])
            sexuality = miisav[persOffsetSX:persOffsetSX + 27]
            sexuality = DecodeSexuality(sexuality)
            sexuality[slot * 3:slot * 3 + 3] = miisexuality
            sexuality = EncodeSexuality(sexuality)
            miisav[persOffsetSX:persOffsetSX + 27] = sexuality
            print("Personal data replaced!")

        with open(save + "/Mii.sav", "wb") as f:
            f.write(miisav)
        with open(save + "/Player.sav", "wb") as f:
            f.write(playersav)
        print("Mii successfully imported.")

    if mode == "Export":
        paintindex = fpOffset3 + 4 * slot
        facepaint = False

        if slot != -1:
            if miisav[miiOffset2 + 4 * slot:miiOffset2 + 4 * slot + 4] != bytearray.fromhex('FF FF FF FF'):
                facepaint = True
                facepaintID = miisav[miiOffset2 + 4 * slot]

        if slot == -1:
            paintindex = fpOffset3 + 4 * 70
            miiindex = miiOffset3
            miisav = playersav
            if playersav[paintindex:paintindex + 4] != bytearray.fromhex('A5 8A FF AF'):
                facepaint = True
                facepaintID = 70

        if sum(miisav[miiindex:miiindex + 156]) == 152:
            raise RuntimeError("Mii not initialized! Please create a mii in this slot.")
        if miiindex == -1:
            raise RuntimeError("Miis not found.")

        print(f"Mii detected at {hex(miiindex)}! Writing to file...")

        personality = bytearray()
        for x in range(18):
            CurrentPV = miisav[persOffsets[x] + slot * 4:persOffsets[x] + slot * 4 + 4]
            personality.extend(CurrentPV)
        sexuality = miisav[persOffsetSX:persOffsetSX + 27]
        sexuality = DecodeSexuality(sexuality)
        sexuality = sexuality[slot * 3:slot * 3 + 3]
        sexuality.append(0)

        name = miisav[miinames + slot * 64:miinames + slot * 64 + 64]
        pronounce = miisav[miiprefer + slot * 128:miiprefer + slot * 128 + 128]
        canvasSection = bytearray.fromhex('A3 A3 A3 A3')
        ugcSection = bytearray.fromhex('A4 A4 A4 A4')
        miiVersion = 1 if slot == -1 else 3
        ltdData = bytearray(3)

        if facepaint:
            facepaintFile = f"00{facepaintID}" if facepaintID < 10 else f"0{facepaintID}"
            print(f"Facepaint detected with ID {facepaintID}! Grabbing..")
            with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs", "rb") as f:
                canvastex = bytearray(f.read())
                ltdData[0] = 1
            with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs", "rb") as f:
                ugctex = bytearray(f.read())
                ltdData[1] = 1
        else:
            canvastex = bytearray()
            ugctex = bytearray()

        output = (bytearray([miiVersion]) + ltdData + miisav[miiindex:miiindex + 156]
                  + personality + name + pronounce + bytearray(sexuality)
                  + canvasSection + canvastex + ugcSection + ugctex)

        printName = name[:name.find(bytes.fromhex("00 00 00"))]
        if len(printName) % 2 == 1:
            printName.append(0)
        sanitName = re.sub(r'[^\w.-]', '_', printName.decode("utf-16"))

        if miipath[-4:] == "auto":
            miipath = miipath[:-4] + ("Mii" if slot == -1 else sanitName)

        if ".ltd" not in miipath:
            miipath += ".ltd"
        miipath = uniqueFile(miipath)

        with open(miipath, "wb") as f:
            f.write(output)
        os.chmod(miipath, stat.S_IREAD)

        print(f"Success! {printName.decode('utf-16')} written to {miipath}")


def computeSlots(folder, item):
    """Return slot strings (e.g. '1 - Tom') for the given save folder and item type."""
    folder = trimStr(folder)
    if not folder or not os.path.isdir(folder):
        return []

    miisav_path = os.path.join(folder, "Mii.sav")
    playersav_path = os.path.join(folder, "Player.sav")
    if not (os.path.isfile(miisav_path) and os.path.isfile(playersav_path)):
        return []

    with open(miisav_path, "rb") as f:
        miisav = bytearray(f.read())
    with open(playersav_path, "rb") as f:
        playersav = bytearray(f.read())

    filledSlots = []
    if item == "Mii":
        miinames = offsetLocator(miisav, "2499BFDA") + 4
        miiOffset6 = offsetLocator(miisav, "881CA27A") + 4
        filledSlots = ["0 - In-Progress Mii"]
        for x in range(70):
            miiindex = miiOffset6 + 156 * x
            miilistname = miisav[miinames + x * 64:miinames + x * 64 + 64]
            if sum(miisav[miiindex:miiindex + 156]) != 152:
                printName = miilistname[:miilistname.find(bytes.fromhex("00 00 00"))]
                if len(printName) % 2 == 1:
                    printName.append(0)
                filledSlots.append(f"{x + 1} - {printName.decode('utf-16')}")
        return filledSlots

    type_map = {
        "Food":        ("Food",      "408494F5", 99),
        "Clothing":    ("Cloth",     "40710642", 299),
        "Treasure":    ("Goods",     "2F793EB1", 99),
        "Interior":    ("Interior",  "3DE2C5DD", 99),
        "Exterior":    ("Exterior",  "27C875D6", 99),
        "Objects":     ("MapObject", "56F99338", 99),
        "Landscaping": ("MapFloor",  "918875A9", 99),
    }
    ugcType, hashStr, maxSlots = type_map[item]
    nOffset1 = offsetLocator(playersav, hashStr) + 4

    New = False
    NewSlot = None
    for x in range(maxSlots):
        ugcFile = f"/Ugc{ugcType}{x:03d}.canvas.zs"
        ugcName = playersav[nOffset1 + x * 128:nOffset1 + x * 128 + 128]
        if os.path.isfile(folder + "/Ugc" + ugcFile):
            ugcPrintName = ugcName[:ugcName.find(bytes.fromhex("00 00 00"))]
            if len(ugcPrintName) % 2 == 1:
                ugcPrintName.append(0)
            filledSlots.append(f"{x + 1} - {ugcPrintName.decode('utf-16')}")
        if (not os.path.isfile(folder + "/Ugc" + ugcFile)) and not New:
            NewSlot = f"{x + 1} - Add New Item"
            New = True
    if New:
        filledSlots.append(NewSlot)
    return filledSlots


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class _BufferWriter(io.IOBase):
    """File-like object that appends to a Gtk.TextBuffer on the GLib main loop."""

    def __init__(self, append_fn):
        super().__init__()
        self._append = append_fn

    def writable(self):
        return True

    def write(self, text):
        if text:
            GLib.idle_add(self._append, text)
        return len(text)

    def flush(self):
        pass


class TomodachisWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Tomodachis")
        self.set_default_size(640, 760)
        self.set_size_request(420, 520)
        self.set_icon_name(APP_ID)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()

        menu = Gio.Menu()
        menu.append("_About Tomodachis", "app.about")
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu)
        menu_button.set_tooltip_text("Main Menu")
        header.pack_end(menu_button)
        toolbar.add_top_bar(header)

        self.toast_overlay = Adw.ToastOverlay()
        toolbar.set_content(self.toast_overlay)

        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.toast_overlay.set_child(scrolled)

        clamp = Adw.Clamp(maximum_size=640, tightening_threshold=560)
        scrolled.set_child(clamp)

        page = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
            margin_top=24,
            margin_bottom=24,
            margin_start=12,
            margin_end=12,
        )
        clamp.set_child(page)

        # Save data group ----------------------------------------------------
        save_group = Adw.PreferencesGroup(
            title="Save Data",
            description="Drag and drop a folder or file, or use the buttons.",
        )

        self.folder_row = Adw.EntryRow(title="Save Folder")
        folder_btn = Gtk.Button(icon_name="folder-open-symbolic", valign=Gtk.Align.CENTER)
        folder_btn.add_css_class("flat")
        folder_btn.set_tooltip_text("Choose Save Folder")
        folder_btn.connect("clicked", self.on_browse_folder)
        self.folder_row.add_suffix(folder_btn)
        save_group.add(self.folder_row)

        self.file_row = Adw.EntryRow(title="LTD File")
        file_btn = Gtk.Button(icon_name="document-open-symbolic", valign=Gtk.Align.CENTER)
        file_btn.add_css_class("flat")
        file_btn.set_tooltip_text("Choose File")
        file_btn.connect("clicked", self.on_browse_file)
        self.file_row.add_suffix(file_btn)
        save_group.add(self.file_row)

        page.append(save_group)

        # Operation group ----------------------------------------------------
        op_group = Adw.PreferencesGroup(title="Operation")

        self.item_row = Adw.ComboRow(
            title="Item Type",
            subtitle="What kind of content to share",
            model=Gtk.StringList.new(ITEM_NAMES),
        )
        self.item_row.connect("notify::selected", self.on_item_changed)
        op_group.add(self.item_row)

        self.mode_row = Adw.ComboRow(
            title="Mode",
            model=Gtk.StringList.new(MODES),
        )
        self.mode_row.set_selected(MODES.index("List"))
        self.mode_row.connect("notify::selected", self.on_mode_changed)
        op_group.add(self.mode_row)

        self.slot_row = Adw.ComboRow(
            title="Slot",
            subtitle="Load a save folder to populate",
            model=Gtk.StringList.new(["Save not loaded"]),
        )
        op_group.add(self.slot_row)

        page.append(op_group)

        # Options group ------------------------------------------------------
        opt_group = Adw.PreferencesGroup(title="Options")
        self.backup_row = Adw.SwitchRow(
            title="Create Backup",
            subtitle="Copy your save data to ./backup before importing",
            active=True,
        )
        opt_group.add(self.backup_row)
        page.append(opt_group)

        # Run button ---------------------------------------------------------
        self.run_button = Gtk.Button(label="Start")
        self.run_button.add_css_class("suggested-action")
        self.run_button.add_css_class("pill")
        self.run_button.set_halign(Gtk.Align.CENTER)
        self.run_button.connect("clicked", self.on_run)
        page.append(self.run_button)

        # Output -------------------------------------------------------------
        output_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        output_heading = Gtk.Label(label="Output", xalign=0)
        output_heading.add_css_class("heading")
        output_box.append(output_heading)

        out_frame = Gtk.Frame()
        out_frame.add_css_class("view")
        out_scroll = Gtk.ScrolledWindow(min_content_height=180, hexpand=True)
        out_frame.set_child(out_scroll)

        self.output_buffer = Gtk.TextBuffer()
        self.output_view = Gtk.TextView(
            buffer=self.output_buffer,
            editable=False,
            cursor_visible=False,
            monospace=True,
            wrap_mode=Gtk.WrapMode.WORD_CHAR,
            top_margin=8,
            bottom_margin=8,
            left_margin=8,
            right_margin=8,
        )
        out_scroll.set_child(self.output_view)
        output_box.append(out_frame)
        page.append(output_box)

        self.set_content(toolbar)

        # Drag-and-drop ------------------------------------------------------
        self._attach_drop(self.folder_row, is_folder=True)
        self._attach_drop(self.file_row, is_folder=False)

        # Refresh slots when the folder field changes (typing or pasting).
        self.folder_row.connect("changed", lambda *_: self.refresh_slots())
        self.on_mode_changed(self.mode_row, None)

    # ------------------------------------------------------------------ helpers

    def get_item_name(self):
        return ITEM_NAMES[self.item_row.get_selected()]

    def get_mode_name(self):
        return MODES[self.mode_row.get_selected()]

    def append_output(self, text):
        end = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end, text)
        mark = self.output_buffer.create_mark(None, self.output_buffer.get_end_iter(), False)
        self.output_view.scroll_mark_onscreen(mark)
        self.output_buffer.delete_mark(mark)
        return False

    def clear_output(self):
        self.output_buffer.set_text("", 0)

    def show_toast(self, message, timeout=3):
        toast = Adw.Toast(title=message, timeout=timeout)
        self.toast_overlay.add_toast(toast)

    # ------------------------------------------------------------------ slots

    def refresh_slots(self):
        folder = trimStr(self.folder_row.get_text().strip())
        item = self.get_item_name()
        try:
            slots = computeSlots(folder, item)
        except Exception as e:
            self.append_output(f"Could not read save: {e}\n")
            slots = []

        if not slots:
            slots = ["Save not loaded"]
        self.slot_row.set_model(Gtk.StringList.new(slots))

        if folder and os.path.isdir(folder) and slots != ["Save not loaded"]:
            if item == "Mii":
                self.slot_row.set_selected(min(1, len(slots) - 1))
            else:
                self.slot_row.set_selected(len(slots) - 1)

    def on_item_changed(self, *_):
        self.refresh_slots()

    def on_mode_changed(self, *_):
        is_import = self.get_mode_name() == "Import"
        self.backup_row.set_sensitive(is_import)
        if not is_import:
            self.backup_row.set_subtitle("Only applies in Import mode")
        else:
            self.backup_row.set_subtitle("Copy your save data to ./backup before importing")

    # ------------------------------------------------------------------ pickers

    def on_browse_folder(self, _button):
        dialog = Gtk.FileDialog(title="Select Save Folder", modal=True)
        dialog.select_folder(self, None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error as e:
            if e.code != Gtk.DialogError.DISMISSED:
                self.show_toast(f"Could not open folder: {e.message}")
            return
        if folder and folder.get_path():
            self.folder_row.set_text(folder.get_path())
            self.clear_output()

    def on_browse_file(self, _button):
        mode = self.get_mode_name()
        item_idx = ITEM_NAMES.index(self.get_item_name())

        if mode in ("Export All", "List"):
            dialog = Gtk.FileDialog(title="Select Folder", modal=True)
            dialog.select_folder(self, None, self._on_file_folder_chosen)
            return

        filter_ = Gtk.FileFilter()
        filter_.set_name(EXTENSION_DESC[item_idx])
        filter_.add_pattern("*" + EXTENSIONS[item_idx])
        any_filter = Gtk.FileFilter()
        any_filter.set_name("All files")
        any_filter.add_pattern("*")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_)
        filters.append(any_filter)

        dialog = Gtk.FileDialog(title="Select File", modal=True, filters=filters, default_filter=filter_)

        if mode == "Export":
            dialog.set_initial_name("Mii" + EXTENSIONS[item_idx])
            dialog.save(self, None, self._on_file_chosen_save)
        else:
            dialog.open(self, None, self._on_file_chosen_open)

    def _on_file_chosen_open(self, dialog, result):
        try:
            f = dialog.open_finish(result)
        except GLib.Error as e:
            if e.code != Gtk.DialogError.DISMISSED:
                self.show_toast(f"Could not open file: {e.message}")
            return
        if f and f.get_path():
            self._set_file_path(f.get_path(), detect_type=True)

    def _on_file_chosen_save(self, dialog, result):
        try:
            f = dialog.save_finish(result)
        except GLib.Error as e:
            if e.code != Gtk.DialogError.DISMISSED:
                self.show_toast(f"Could not save file: {e.message}")
            return
        if f and f.get_path():
            self._set_file_path(f.get_path(), detect_type=False)

    def _on_file_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error as e:
            if e.code != Gtk.DialogError.DISMISSED:
                self.show_toast(f"Could not open folder: {e.message}")
            return
        if folder and folder.get_path():
            self.file_row.set_text(folder.get_path())

    def _set_file_path(self, path, detect_type=True):
        if detect_type and not os.path.isdir(path):
            ext = Path(path).suffix
            if ext in EXTENSIONS:
                self.item_row.set_selected(EXTENSIONS.index(ext))
        self.file_row.set_text(path)

    # ------------------------------------------------------------------ DnD

    def _attach_drop(self, widget, is_folder):
        target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        target.connect("drop", self._on_drop, is_folder)
        widget.add_controller(target)

    def _on_drop(self, _target, value, _x, _y, is_folder):
        files = value.get_files() if value else []
        if not files:
            return False
        path = files[0].get_path()
        if not path:
            return False
        if is_folder:
            self.folder_row.set_text(path)
            self.clear_output()
        else:
            self._set_file_path(path, detect_type=True)
        return True

    # ------------------------------------------------------------------ run

    def on_run(self, _button):
        self.clear_output()
        folder = trimStr(self.folder_row.get_text().strip())
        file = trimStr(self.file_row.get_text().strip())
        mode = self.get_mode_name()
        item = self.get_item_name()
        backup = self.backup_row.get_active()

        slot_text = ""
        slot_obj = self.slot_row.get_selected_item()
        if slot_obj is not None:
            slot_text = slot_obj.get_string()
        if " - " not in slot_text:
            self.show_toast("Load a save folder first")
            return

        is_adding = slot_text.split(" - ")[1] == "Add New Item"
        try:
            slot = int(slot_text.split(" - ")[0])
        except ValueError:
            self.show_toast("Invalid slot")
            return

        item_idx_for_ugc = ITEM_NAMES.index(item) - 1  # -1 for Mii, 0..6 for UGC

        if mode in ("Export", "Export All") and is_adding:
            self.show_toast("You can't use this slot with this mode.")
            return
        if not folder:
            self.show_toast("Pick a save folder first")
            return

        if not file and mode == "Export":
            file = "auto"
        if os.path.isdir(file) and mode == "Export":
            file = os.path.join(file, "auto")

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = _BufferWriter(self.append_output)
        try:
            if mode != "Export All":
                if item_idx_for_ugc == -1:
                    ShareMii(mode, slot, folder, file, backup)
                else:
                    ugcStart(mode, slot, folder, file, is_adding, item_idx_for_ugc)
            else:
                if not os.path.isdir(file):
                    raise RuntimeError(f"{file} is not a folder.")
                file = os.path.join(file, "auto")
                model = self.slot_row.get_model()
                names = [model.get_string(i) for i in range(model.get_n_items())]
                if item_idx_for_ugc == -1:
                    names = names[1:]  # drop the in-progress entry
                else:
                    names = names[:-1]  # drop the trailing "Add New Item"
                for entry in names:
                    s = int(entry.split(" - ")[0])
                    if item_idx_for_ugc == -1:
                        ShareMii("Export", s, folder, file, backup)
                    else:
                        ugcStart("Export", s, folder, file, is_adding, item_idx_for_ugc)
            self.show_toast(f"{mode} finished")
        except Exception as e:
            self.append_output(f"\nError: {e}\n")
            self.show_toast(str(e), timeout=5)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            self.refresh_slots()


def _register_bundled_icons():
    """Add the bundled icons/ tree to the default icon theme search path."""
    display = Gdk.Display.get_default()
    if display is None:
        return
    icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
    if not os.path.isdir(icon_dir):
        return
    theme = Gtk.IconTheme.get_for_display(display)
    if icon_dir not in theme.get_search_path():
        theme.add_search_path(icon_dir)


class TomodachisApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.connect("activate", self._on_activate)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Primary>q"])

    def _on_activate(self, _app):
        _register_bundled_icons()
        win = self.props.active_window
        if not win:
            win = TomodachisWindow(self)
        win.present()

    def _on_about(self, *_):
        about = Adw.AboutDialog(
            application_name="Tomodachis",
            application_icon=APP_ID,
            version=versionStr,
            developer_name="POCOGuy",
            website="https://www.pocoguy.com",
            comments=(
                "Import and export Miis and User-Generated Content from "
                "Tomodachi Life: Living the Dream save data."
            ),
            license_type=Gtk.License.GPL_3_0,
            copyright="© Star-F0rce, Ben Rau, and POCOGuy",
        )
        about.set_developers(["Star-F0rce", "Ben Rau", "POCOGuy"])
        about.add_credit_section(
            "Forked from",
            ["ShareMii by Star-F0rce and Ben Rau https://github.com/Star-F0rce/ShareMii"],
        )
        about.set_issue_url("https://github.com/Star-F0rce/ShareMii/issues")
        about.present(self.props.active_window)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description=f"ShareMii v{versionStr} - Import/Export Living the Dream Miis"
    )
    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument("-l", action="store_true", help="List Miis")
    mode_group.add_argument("-i", metavar="Mii.ltd", type=str, help="Import Mii.ltd")
    mode_group.add_argument("-o", metavar="Name", type=str, help="Export Mii to Name.ltd")
    mode_group.add_argument("-a", metavar="Directory", type=str, help="Export all Miis to directory")
    parser.add_argument("--backup", action="store_true", help="Create backup folder of save data")
    parser.add_argument("save", type=str, nargs="?", help="save folder location")
    parser.add_argument("slot", type=int, nargs="?", help="Mii slot to import/export")
    return parser


def _run_cli(args):
    if args.l:
        ShareMii("List", args.slot or 1, args.save, "")
        return 0
    if args.i:
        ShareMii("Import", args.slot, args.save, args.i, args.backup)
        return 0
    if args.o:
        ShareMii("Export", args.slot, args.save, args.o)
        return 0
    if args.a:
        slots = computeSlots(args.save, "Mii")[1:]  # skip in-progress slot
        for entry in slots:
            s = int(entry.split(" - ")[0])
            ShareMii("Export", s, args.save, os.path.join(args.a, "auto"))
        return 0
    return None


def main():
    args = _build_arg_parser().parse_args()
    rc = _run_cli(args)
    if rc is not None:
        sys.exit(rc)

    app = TomodachisApp()
    sys.exit(app.run([sys.argv[0]]))


if __name__ == "__main__":
    main()
