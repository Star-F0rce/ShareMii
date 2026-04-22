import argparse
from datetime import datetime 
import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect
import re
import struct
from pathlib import Path
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from tkinterdnd2 import DND_FILES, TkinterDnD
from ShareUGC import ugcStart,shareUGC

majVersion = 3
minVersion = 2
patchVersion = 1
preVersion = 0
if preVersion:
    preVersion = str(".pre" + str(preVersion))
else:
    preVersion = ""
if patchVersion:
    patchVersion = "." + str(patchVersion)
else:
    patchVersion = ""
versionStr = str(majVersion) + "." + str(minVersion) + patchVersion + preVersion

## This is to output the command line to the GUI
class TextRedirector():
    def __init__(self,widget, tag=None):
        self.widget = widget
        self.tag = tag

    def write(self,text):
        self.widget.insert(tk.END, text, (self.tag,))
        self.widget.see(tk.END)

    def flush(self):
        pass

## used to add hover tooltips to ttinker widgets
class CreateToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        # Bind the mouse enter and mouse leave events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        # Prevent multiple tooltips from spawning
        if self.tooltip_window or not self.text:
            return
        
        # Calculate the coordinates so it appears right below the widget
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Create a Toplevel window with no borders/decorations
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes("-alpha", 0.85)

        # Create the visual label for the tooltip
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#2b2b2b", foreground="#ffffff", 
                         relief='solid', borderwidth=1,
                         font=("Arial", "9", "normal"), padx=5, pady=3)
        label.pack()

    def hide_tooltip(self, event=None):
        # Destroy the tooltip window when the mouse leaves
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

## Used for GUI icon
def resourcePath(relativePath):
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)

## Used to browse folders in GUI
def browseFolder():
    # Opens folder selection dialog
    selectedDirectory = filedialog.askdirectory()
    if selectedDirectory:
        folderVar.set(selectedDirectory)
        guiOutput.delete("1.0", "end")
        getSlots(selectedDirectory)
        if itemVar.get() != "Mii":
            slotEntry.current(len(slotEntry["values"]) - 1)
        else:
            slotEntry.current(1)

def trimStr(path):
    if (path.startswith("'") and path.endswith("'")) or (path.startswith('"') and path.endswith('"')):
        path=path[1:-1]
    return(path)

## Used to browse files in GUI
def browseFile():
    # Opens folder selection dialog

    item = itemVar.get()
    itemList = list(["Mii","Food","Clothing","Treasure","Interior","Exterior","Objects","Landscaping"])
    item = itemList.index(item)

    fExtensionDesc=["LtD Mii Files","LtD Food Files","LtD Cloth Files","LtD Goods Files","LtD Interior Files","LtD Exterior Files","LtD MapObject Files","LtD MapFloor Files"]
    fExtensionType=["*.ltd","*.ltdf","*.ltdc","*.ltdg","*.ltdi","*.ltde","*.ltdo","*.ltdl"]
    fExtensionDef=[".ltd",".ltdf",".ltdc",".ltdg",".ltdi",".ltde",".ltdo",".ltdl"]
    fExtensionDesc=str(fExtensionDesc[item])
    fExtensionType=str(fExtensionType[item])
    fExtensionDef=str(fExtensionDef[item])
    if modeVar.get() == "Import":
        selectedDirectory = filedialog.askopenfilename(defaultextension=fExtensionDef, filetypes=[(fExtensionDesc, fExtensionType)])
    if modeVar.get() == "Export All":
        selectedDirectory = filedialog.askdirectory()
    if modeVar.get() == "Export":
        selectedDirectory = filedialog.asksaveasfilename(defaultextension=fExtensionDef, filetypes=[(fExtensionDesc, fExtensionType)])
    if modeVar.get() == "List":
        selectedDirectory = filedialog.askdirectory()
    if selectedDirectory:
        fileVar.set(selectedDirectory)

## Handles the drag 'n drop for the GUI
def dragndrop(event):
    files = root.tk.splitlist(event.data)
    if not files:
        return()
    path = files[0]
    if event.widget == folderEntry:
        folderVar.set(path)
        guiOutput.delete("1.0", "end")
        getSlots(path)
        if itemVar.get() != "Mii":
            slotEntry.current(len(slotEntry["values"]) - 1)
        else:
            slotEntry.current(1)
    else:
        if not (os.path.isdir(path)):
            itemList = list(["Mii","Food","Clothing","Treasure","Interior","Exterior","Objects","Landscaping"])
            fExtensionDef=[".ltd",".ltdf",".ltdc",".ltdg",".ltdi",".ltde",".ltdo",".ltdl"]
            ext = Path(path).suffix
            itemVar.set(itemList[fExtensionDef.index(ext)])
        fileVar.set(path)

def offsetLocator(file, hashStr):
    hash = bytes.fromhex(hashStr)
    littleHash = hash[::-1]

    index = file.find(littleHash)
    if index == -1:
        return None
    offsetBytes = file[index + 4:index + 8]
    offset = struct.unpack('<I', offsetBytes)[0]
    
    return offset

## Handles the sexuality bytes
def DecodeSexuality(data: bytearray) -> list[int]:
    return [int(bit) for byte in data for bit in f"{byte:08b}"[::-1]]

def EncodeSexuality(bits: list[int]) -> bytearray:
    if len(bits) % 8 != 0:
        raise ValueError("Bit list length must be a multiple of 8")
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        byte_str = ''.join(str(bit) for bit in byte_bits[::-1])
        result.append(int(byte_str, 2))

    return result

parser = argparse.ArgumentParser(description="ShareMii v" + versionStr +" - Import/Export Living the Dream Miis!")

mode_group = parser.add_mutually_exclusive_group(required=False)
mode_group.add_argument("-l", action="store_true", help="List Miis")
mode_group.add_argument("-i",metavar="Mii.ltd",type=str,help="Import Mii.ltd")
mode_group.add_argument("-o",metavar="Name",type=str,help="Export Mii to Name.ltd")
mode_group.add_argument("-a",metavar="Directory",type=str,help="Export all Miis to directory")
parser.add_argument("--backup", action="store_true", help="Create Backupfolder of Savedata")
parser.add_argument("save", type=str, help="save folder location", nargs="?")
parser.add_argument("slot", type=int, help="Mii slot to import/export", nargs="?")

args = parser.parse_args()

ugcTypeString = list(["Food","Clothing","Treasure","Interior","Exterior","Objects","Landscaping"])
ugcTypeIndex = list(["Food","Cloth","Goods","Interior","Exterior","MapObject","MapFloor"])

def ShareMii(mode: str, slot: int, save: str, miipath:str, backup:bool = True):

    miipath=trimStr(miipath)
    save=trimStr(save)

    if mode == "List":
        slot = 1

    if slot > 70:
        raise RuntimeError("Invalid slot. Please choose a slot 0-70.")
    if slot < 0:
        raise RuntimeError("Invalid slot. Please choose a slot 0-70.")

    slot -= 1

    with open(save + "/Mii.sav", "rb") as f:
        miisav = bytearray(f.read())

    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())

    # Offsets
    fpOffset1=offsetLocator(playersav,"4C9819E4") + 4 # UGC.Facepaint.Price
    fpOffset2=offsetLocator(playersav,"DECC8954") + 4 # UGC.Facepaint.TextureSourceType
    fpOffset3=offsetLocator(playersav,"23135BC5") + 4 # UGC.Facepaint.State
    fpOffset4=offsetLocator(playersav,"FFC750B6") + 4 # UGC.Facepaint.Unknown
    fpOffset5=offsetLocator(playersav,"A56E42EC") + 4 # UGC.Facepaint.Hash
    miiOffset1=int("11420",16) # Mii Sort IDs
    miiOffset2=offsetLocator(miisav,"5E32ADF4") + 4 # Mii.MiiMisc.FaceInfo.FacePaintIndex
    miiOffset3=offsetLocator(playersav,"114EFF89") # Temp Slot Mii Offset
    miiOffset4=offsetLocator(miisav,"2499BFDA") + 4 # Mii Names
    miiOffset5=offsetLocator(miisav,"3A5EDA05") + 4 # Pronounciation
    miiOffset6=offsetLocator(miisav,"881CA27A") + 4 # Raw Mii data
    persOffsetP1=offsetLocator(miisav,"43CD364F") + 4 # Mii.CharacterParam.Sociability
    persOffsetP2=offsetLocator(miisav,"CD8DBAF8") + 4 # Mii.CharacterParam.Audaciousness
    persOffsetP3=offsetLocator(miisav,"25B48224") + 4 # Mii.CharacterParam.Activeness
    persOffsetP4=offsetLocator(miisav,"607BA160") + 4 # Mii.CharacterParam.Commonsense
    persOffsetP5=offsetLocator(miisav,"68E1134E") + 4 # Mii.CharacterParam.Gaiety
    persOffsetV1=offsetLocator(miisav,"4913AE1A") + 4 # Mii.Voice.Formants
    persOffsetV2=offsetLocator(miisav,"141EE086") + 4 # Mii.Voice.Speed
    persOffsetV3=offsetLocator(miisav,"07B9D175") + 4 # Mii.Voice.Intonation
    persOffsetV4=offsetLocator(miisav,"81CF470A") + 4 # Mii.Voice.Pitch
    persOffsetV5=offsetLocator(miisav,"4D78E262") + 4 # Mii.Voice.Tension
    persOffsetV6=offsetLocator(miisav,"FBC3FFB0") + 4 # Mii.Voice.PresetType
    persOffsetS1=offsetLocator(miisav,"236E2D73") + 4 # Mii.MiiMisc.FaceInfo.Gender
    persOffsetS2=offsetLocator(miisav,"F3C3DE59") + 4 # Mii.Name.PronounType
    persOffsetS3=offsetLocator(miisav,"660C5247") + 4 # Mii.MiiMisc.ClothInfo.ClothStyle
    persOffsetB1=offsetLocator(miisav,"5D7D3F45") + 4 # Mii.MiiMisc.BirthdayInfo.Year
    persOffsetB2=offsetLocator(miisav,"AB8AE08B") + 4 # Mii.MiiMisc.BirthdayInfo.Day
    persOffsetB3=offsetLocator(miisav,"2545E583") + 4 # Mii.MiiMisc.BirthdayInfo.DirectAge
    persOffsetB4=offsetLocator(miisav,"6CF484F4") + 4 # Mii.MiiMisc.BirthdayInfo.Month
    persOffsetSX=offsetLocator(miisav,"DFC82223") + 4 # Mii.MiiMisc.FaceInfo.IsLoveGender
    persOffsets=list([persOffsetP1,persOffsetP2,persOffsetP3,persOffsetP4,persOffsetP5,persOffsetV1,persOffsetV2,persOffsetV3,persOffsetV4,persOffsetV5,persOffsetV6,persOffsetS1,persOffsetS2,persOffsetS3,persOffsetB1,persOffsetB2,persOffsetB3,persOffsetB4])

    # Searchable Offsets
    miiindex = miiOffset6 + 156 * (slot)
    miinames = miiOffset4
    miiprefer = miiOffset5

    ## LIST MODE ###################################################################
    if mode == "List":
        for x in range(69):
            miiindex = miiOffset6 + 156 * (x)
            miilistname = miisav[miinames+((x)*64):miinames+((x)*64)+64]
            if sum(miisav[miiindex:miiindex+156]) != 152:
                printName = miilistname[:miilistname.find(bytes.fromhex("00 00 00"))]
                if len(printName) % 2 == 1:
                    printName.append(0)
                print(str(x+1) + " - " + printName.decode("utf-16"))
        return()

    ## IMPORT MODE #################################################################
    if mode == "Import":

        # Backup Save DATA
        if backup:
            if not os.path.exists(r"./backup"):
                os.mkdir(r"./backup")
            backuppath = "./backup"

            shutil.copytree(save,backuppath + "/" + datetime.now().strftime("SaveData_Backup_%d_%m_%Y_%H%M%S"))

        # Import the args
        with open(miipath, "rb") as f:
            mii = bytearray(f.read())

        if mii == bytearray():
            raise RuntimeError("This Mii is empty!") # Did you try looking under the tray?
        if mii[0] not in range(1,4):
            raise RuntimeError("Incorrect version found. Expected 1-3, got" + str(mii[0]))

        ## CONVERSION
        # ltdv3 changed certain parts of the file to be more consistent. This check will convert old Miis into ones that work
        if mii[0] < 3:
            del mii[4]
            if mii[0] == 2:
                mii = mii[:427] + bytearray([0]) + mii[427:]
                canvasStart = mii.find(bytes.fromhex("A3 A3 A3")) + 3
                ugcStart = mii.rfind(bytes.fromhex("A3 A3 A3"))
                mii = mii[:canvasStart] + bytearray([163]) + mii[canvasStart:]
                mii[ugcStart+1:ugcStart+4] = bytearray.fromhex("A4 A4 A4")
                mii = mii[:ugcStart + 3] + bytearray([164]) + mii[ugcStart + 3:]

        # if mii[30] != 110:
        #     raise RuntimeError(".ltd not recognized. Is this really a Mii?")

        #Find where miis are stored in Mii.sav
        paintindex = fpOffset3 + 4 * (slot)
        canvasStart = mii.find(bytes.fromhex("A3 A3 A3 A3")) + 4
        ugcStart = mii.rfind(bytes.fromhex("A4 A4 A4 A4")) + 4
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

        #Errors
        if sum(miisav[miiindex:miiindex+156]) == 152:
            raise RuntimeError("Mii not initialized! Please create a mii in this slot.")

        #Write to file
        if slot == -1:
            print("Writing Mii to the temporary slot...")
            playersav[miiindex:miiindex+156] = mii[4:4+156]
        else:
            print(f"Mii detected at {hex(miiindex)}! Replacing...")
            miisav[miiindex:miiindex+156] = mii[4:4+156]

        ## FACEPAINT ##

        if slot == -1:
            # The Temp slot (slot -1) uses facepaint ID 70. 
            # check Player.sav to see if Facepaint 70 is currently active.
            paintindex = fpOffset3 + 4 * 70
            if playersav[paintindex:paintindex+4] != bytearray.fromhex('A5 8A FF AF'):
                facepaintID = 70
            else:
                facepaintID = 255
        else:
            facepaintID = miisav[miiOffset2+4*(slot)]

        #If we detected facepaint earlier, we should copy it into the save file
        if facepaint:
            print("Facepaint detected! Copying...")
            #If we're replacing a mii that didn't initially have facepaint, we'll give it the next ID facepaint
            if facepaintID == 255:
                usedIDs=bytearray([255] * 70)
                for x in range(70):
                    if miisav[miiOffset2+4*(x)] != 255:
                        usedIDs[x]=miisav[miiOffset2+4*(x)]
                s = set(usedIDs)
                for i in range(70):
                    if i not in s:
                        facepaintID=i
                        break

            #The fun part! Telling the game to read the facepaint files.
            if slot == -1:
                facepaintID = 70
            else:
                miisav[miiOffset2+4*(slot):miiOffset2+4*(slot)+4] = bytearray([facepaintID, 0, 0, 0])
            playersav[fpOffset1+4*(facepaintID ):fpOffset1+4*(facepaintID )+4] = bytearray.fromhex('F4 01 00 00')
            playersav[fpOffset2+4*(facepaintID ):fpOffset2+4*(facepaintID )+4] = bytearray.fromhex('41 49 93 56')
            playersav[fpOffset3+4*(facepaintID ):fpOffset3+4*(facepaintID )+4] = bytearray.fromhex('F4 AD 7F 1D')
            playersav[fpOffset4+4*(facepaintID ):fpOffset4+4*(facepaintID )+4] = bytearray.fromhex('00 80 00 00')
            playersav[fpOffset5+4*(facepaintID ):fpOffset5+4*(facepaintID )+4] = bytearray([facepaintID, 0, 8, 0])

            if facepaintID < 10:
                facepaintFile = "00" + str(facepaintID)
            else:
                facepaintFile = "0" + str(facepaintID)
            #Copying the facepaint.
            # Specify the directory path
            UgcDir = Path(save + "/Ugc")
            UgcDir.mkdir(parents=True, exist_ok=True)


            if facepaint == 2:
                s_canvas = miipath + ".canvas.zs"
                d_canvas = save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs"
                s_ugc = miipath + ".ugctex.zs"
                d_ugc = save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs"
                shutil.copy(s_canvas, d_canvas)
                shutil.copy(s_ugc, d_ugc)
            else:
                with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs", "wb") as f:
                    f.write(mii[canvasStart:ugcStart - 4])
                with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs", "wb") as f:
                    f.write(mii[ugcStart:])
            print("Facepaint successfully copied to " + save + "/Ugc/UgcFacePaint" + facepaintFile)

        #If the imported Mii doesn't have facepaint, we should remove the old one
        else:
            if facepaintID != 255:
                print("This new Mii no longer uses facepaint. Be sure to back up the old facepaint if you still want it.")
                if slot != -1:
                    miisav[miiOffset2+4*(slot):miiOffset2+4*(slot)+4] = bytearray.fromhex('FF FF FF FF')
                
                playersav[fpOffset1+4*(facepaintID ):fpOffset1+4*(facepaintID )+4] = bytearray.fromhex('00 00 00 00')
                playersav[fpOffset2+4*(facepaintID ):fpOffset2+4*(facepaintID )+4] = bytearray.fromhex('09 DE EE B6')
                playersav[fpOffset3+4*(facepaintID ):fpOffset3+4*(facepaintID )+4] = bytearray.fromhex('A5 8A FF AF')
                playersav[fpOffset4+4*(facepaintID ):fpOffset4+4*(facepaintID )+4] = bytearray.fromhex('00 00 00 00')
                playersav[fpOffset5+4*(facepaintID ):fpOffset5+4*(facepaintID )+4] = bytearray.fromhex('00 00 00 00')

        ## FACEPAINT END ##
        ## PERSONALITY ##
        if (mii[0] < 2) & (slot != -1):
            print("No personal data configured, skipping...")

        if (mii[0] >= 2) & (slot != -1):
            print("Personal data detected! Applying...")
            # Apply personality changes
            for x in range(18):
                miisav[persOffsets[x]+(slot)*4:persOffsets[x]+(slot)*4+4] = mii[160+x*4:160+x*4+4]

            miisav[miinames+((slot)*64):miinames+((slot)*64)+64] = mii[232:296]
            miisav[miiprefer+((slot)*128):miiprefer+((slot)*128)+128] = mii[296:424]
            miisexuality=list(mii[424:427])
            sexuality = miisav[persOffsetSX:persOffsetSX+27]
            sexuality = DecodeSexuality(sexuality)
            sexuality[(slot)*3:(slot)*3+3]=miisexuality
            sexuality = EncodeSexuality(sexuality)
            miisav[persOffsetSX:persOffsetSX+27] = sexuality
            print("Personal data replaced!")

        with open(save + "/Mii.sav", "wb") as f:
            f.write(miisav)
        with open(save + "/Player.sav", "wb") as f:
            f.write(playersav)
        print("Mii successfully imported.")

    ## EXPORT MODE #################################################################
    if mode == "Export":
        #Read inputs

        #Locate miis in Mii.sav
        paintindex = fpOffset3 + 4 * (slot)
        facepaint=False

        #Face paint detection
        if slot != -1:
            if miisav[miiOffset2+4*(slot):miiOffset2+4*(slot)+4] != bytearray.fromhex('FF FF FF FF'):
                facepaint=True
                facepaintID=miisav[miiOffset2+4*(slot)]

        #Check to see if using Temp Slot
        if slot == -1:
            paintindex = fpOffset3 + 4 * 70
            miiindex = miiOffset3
            miisav=playersav
            if playersav[paintindex:paintindex+4] != bytearray.fromhex('A5 8A FF AF'):
                facepaint=True
                facepaintID=70

        #Errors
        if sum(miisav[miiindex:miiindex+156]) == 152:
            raise RuntimeError("Mii not initialized! Please create a mii in this slot.")
        if miiindex == -1:
            raise RuntimeError("Miis not found.")
        
        print(f"Mii detected at {hex(miiindex)}! Writing to file...")

        ### PERSONALITY ###
        personality=bytearray()
        # This loop grabs nearly all personality aspects from a Mii
        for x in range(18):
            CurrentPV=miisav[persOffsets[x]+(slot)*4:persOffsets[x]+(slot)*4+4]
            personality.extend(CurrentPV)
        # Sexuality is handled a bit differently so we need to decode what the Mii's sexuality is
        sexuality = miisav[persOffsetSX:persOffsetSX+27]
        sexuality = DecodeSexuality(sexuality)
        sexuality=sexuality[(slot)*3:(slot)*3+3]
        sexuality.append(0)
        
        name = miisav[miinames+((slot)*64):miinames+((slot)*64)+64]
        pronounce = miisav[miiprefer+((slot)*128):miiprefer+((slot)*128)+128]
        canvasSection = bytearray.fromhex('A3 A3 A3 A3')
        ugcSection = bytearray.fromhex('A4 A4 A4 A4')
        #Actually create the Mii file
        if slot == -1:
            miiVersion = 1
        else:
            miiVersion = 3
        ltdData = bytearray(3)
        #If facepaint is detected, copy and rename them
        if facepaint:
            if facepaintID < 10:
                facepaintFile = "00" + str(facepaintID)
            else:
                facepaintFile = "0" + str(facepaintID)
            print("Facepaint detected with ID " + str(facepaintID) +"! Grabbing..")
            # d_canvas = args.o + ".ltd.canvas.zs"
            # s_canvas = save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs"
            # d_ugc = args.o + ".ltd.ugctex.zs"
            # s_ugc = save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs"
            # shutil.copy(s_canvas, d_canvas)
            # shutil.copy(s_ugc, d_ugc)

            with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs", "rb") as f:
                canvastex = bytearray(f.read())
                ltdData[0]=1
            with open(save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs", "rb") as f:
                ugctex = bytearray(f.read())
                ltdData[1]=1

        else:
            canvastex=bytearray()
            ugctex=bytearray()

        output = bytearray([miiVersion]) + ltdData + miisav[miiindex:miiindex+156] + personality + name + pronounce + bytearray(sexuality) + canvasSection + canvastex + ugcSection + ugctex

        printName = name[:name.find(bytes.fromhex("00 00 00"))]
        if len(printName) % 2 == 1:
            printName.append(0)

        sanitName = printName.decode("utf-16")
        sanitName = re.sub(r'[^\w.-]', '_', sanitName)

        ## If user didn't give a name, we'll just set the name to their Mii name
        if (miipath[-4:] == "auto"):
            if slot == -1:
                miipath = miipath[:-4] + "Mii"
            else:
                miipath = miipath[:-4] + sanitName

        if ".ltd" not in miipath:
            miipath += ".ltd"

        with open(miipath, "wb") as f:
            f.write(output)
        
        if slot == -1:
            name=bytearray.fromhex("54 00 65 00 6D 00 70")

        print("Success! " + printName.decode("utf-16") + " written to " + miipath)

def beginProcess():
    guiOutput.delete("1.0", "end")
    folder = trimStr(folderVar.get())
    mode = modeVar.get()
    file = trimStr(fileVar.get())
    slot = slotVar.get()
    item = itemVar.get()
    backup = backupVar.get()
    itemList = list(["Mii","Food","Clothing","Treasure","Interior","Exterior","Objects","Landscaping"])
    item = itemList.index(item) - 1
    isAdding = False
    if slot.split(" - ")[1] == "Add New Item":
        isAdding = True
    slot = int(slot.split(" - ")[0])
    if (mode == "Export" or mode =="Export All") & (isAdding == True):
        raise RuntimeError("You can't use this slot with this mode.")

    if (file == "Drag & drop or upload .ltd(x) here") & (mode == "Export"):
        file = "auto"
    if (os.path.isdir(file)) & (mode == "Export"):
        file = os.path.join(file,"auto")

    if mode != "Export All":
        if item == -1:
            ShareMii(mode, slot, folder, file, backup)
        else:
            ugcStart(mode, slot, folder, file, isAdding, item)
        getSlots(folder)
    else:
        if not (os.path.isdir(file)):
            raise RuntimeError(file + " is not a folder.")
        file = os.path.join(file,"auto")
        mode = "Export"
        names = slotEntry["values"]
        if item == "-1":
            names = names[1:]
        else:
            names = names[:len(names) - 1]
            for x in range(len(names)):
                slot = names[x]
                slot = int(slot.split(" - ")[0])
                if item == -1:
                    ShareMii(mode, slot, folder, file, backup)
                else:
                    ugcStart(mode, slot, folder, file, isAdding, item)

##GUI Setup
root = TkinterDnD.Tk()
root.title("ShareMii v" + versionStr)
root.iconphoto(False, tk.PhotoImage(file=resourcePath("icon.png")))
root.geometry("800x550")
root.rowconfigure(8, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.resizable(True,True)
style = ttk.Style(root)

modeVar=tk.StringVar()
itemVar=tk.StringVar()
slotVar=tk.StringVar(value="Save not loaded")
folderVar=tk.StringVar(value="Drag & drop or upload save folder here")
fileVar=tk.StringVar(value="Drag & drop or upload .ltd(x) here")

## Row 0
logo = tk.PhotoImage(file=resourcePath("logo.png"))
ttk.Label(root, image=logo).grid(row=0, column=1, padx=5, pady=5)

## Row 1
ttk.Label(root, text="Select Item:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
itemEntry = ttk.OptionMenu(root, itemVar,"Mii","Mii","Food","Clothing","Treasure","Interior","Exterior","Objects","Landscaping").grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

## Row 2
ttk.Label(root, text="Select Mode:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
modeEntry = ttk.OptionMenu(root, modeVar,"List","Import", "Export", "Export All", "List").grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

## Row 3
ttk.Label(root, text="Select Save Folder:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
folderEntry = ttk.Entry(root, textvariable=folderVar, width=50)
folderEntry.drop_target_register(DND_FILES)
folderEntry.dnd_bind('<<Drop>>',dragndrop)
folderEntry.grid(row=3, column=1, padx=5, pady=5,sticky=tk.NSEW)
browseButton = ttk.Button(root, text="Browse...", width=12, command=browseFolder).grid(row=3, column=2, padx=3, pady=3, sticky=tk.W)

## Row 4
ttk.Label(root, text="Open/Save As File:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
fileEntry = ttk.Entry(root, textvariable=fileVar, width=50)
fileEntry.drop_target_register(DND_FILES)
fileEntry.dnd_bind('<<Drop>>',dragndrop)
fileEntry.grid(row=4, column=1, padx=5, pady=5,sticky=tk.NSEW)
browseButton = ttk.Button(root, text="Browse...", width=12, command=browseFile).grid(row=4, column=2, padx=3, pady=3, sticky=tk.W)

## Row 5
ttk.Label(root, text="Select Slot:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.E)
slotEntry = ttk.Combobox(root, textvariable=slotVar, state="readonly")
slotEntry.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
slotEntry["values"]=list(["Save not loaded"])

# Row 6
backup_frame = ttk.Frame(root)
backup_frame.grid(row=6, column=1, sticky=tk.W)

ttk.Label(root, text="Enable Backup:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.E)
backupVar = tk.BooleanVar(value=True)
backup_cb = ttk.Checkbutton(backup_frame, variable=backupVar)
backup_cb.pack(side=tk.LEFT)

info_icon = ttk.Label(backup_frame, text="\u24D8", foreground="gray", cursor="question_arrow")
info_icon.pack(side=tk.LEFT, padx=(5, 0))
CreateToolTip(info_icon, "Check this to create a save backup Folder of your Game Save data before Importing\n\n IMPORT MODE ONLY\n\nFOLDER LOCATION: \n<app_root_folder>/backup/SaveData_Backup_<Day_Mont_Year_HourMinuteSecond>")

## Row 7
startButton = ttk.Button(root, text="Start!", command=beginProcess, width=20).grid(row=7, column=1, padx=5, pady=5)

## Row 8
guiOutput = ScrolledText(root,height=10,width=40)
guiOutput.grid(row=8, column=1,sticky=tk.NSEW)

sv_ttk.set_theme(darkdetect.theme())

def updateSlots(options):
    slotEntry["values"] = options
    if itemVar.get() == "Mii":
        slotEntry.current(1)
    else:
        slotEntry.current(len(slotEntry["values"]) - 1)

def getSlots(folder):

    folder=trimStr(folder)

    if folderVar.get() == "Drag & drop or upload save folder here":
        return()
    if folderVar.get() == "":
        return()
    if os.path.isfile(folderVar.get()):
        return()

    with open(folder + "/Mii.sav", "rb") as f:
        miisav = bytearray(f.read())

    with open(folder + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())

    item = itemVar.get()
    filledSlots = []
    if item == "Mii":
        miinames=offsetLocator(miisav,"2499BFDA") + 4
        miiOffset6=offsetLocator(miisav,"881CA27A") + 4
        filledSlots = ["0 - In-Progress Mii"]
        for x in range(70):
            miiindex = miiOffset6 + 156 * (x)
            miilistname = miisav[miinames+((x)*64):miinames+((x)*64)+64]
            if sum(miisav[miiindex:miiindex+156]) != 152:
                printName = miilistname[:miilistname.find(bytes.fromhex("00 00 00"))]
                if len(printName) % 2 == 1:
                    printName.append(0)
                filledSlots.append(str(x+1) + " - " + str(printName.decode("utf-16")))
    if item == "Food":
        maxSlots = 99
        ugcType = item
        nOffset1=offsetLocator(playersav,"408494F5") + 4
    if item == "Clothing":
        maxSlots = 299
        ugcType = "Cloth"
        nOffset1=offsetLocator(playersav,"40710642") + 4
    if item == "Treasure":
        maxSlots = 99
        ugcType = "Goods"
        nOffset1=offsetLocator(playersav,"2F793EB1") + 4
    if item == "Interior":
        maxSlots = 99
        ugcType = item
        nOffset1=offsetLocator(playersav,"3DE2C5DD") + 4
    if item == "Exterior":
        maxSlots = 99
        ugcType = item
        nOffset1=offsetLocator(playersav,"27C875D6") + 4
    if item == "Objects":
        maxSlots = 99
        ugcType = "MapObject"
        nOffset1=offsetLocator(playersav,"56F99338") + 4
    if item == "Landscaping":
        maxSlots = 99
        ugcType = "MapFloor"
        nOffset1=offsetLocator(playersav,"918875A9") + 4
    if item != "Mii":
        New = False
        for x in range(maxSlots):
            if x < 10:
                ugcFile = "/Ugc"+ ugcType + "00" + str(x) + ".canvas.zs"
            else:
                ugcFile = "/Ugc"+ ugcType + "0" + str(x) + ".canvas.zs"
            ugcName = playersav[nOffset1+((x)*128):nOffset1+((x)*128)+128]
            if os.path.isfile(folder + "/Ugc" + ugcFile):
                ugcPrintName = ugcName[:ugcName.find(bytes.fromhex("00 00 00"))]
                if len(ugcPrintName) % 2 == 1:
                    ugcPrintName.append(0)
                filledSlots.append(str(x+1) + " - " + ugcPrintName.decode("utf-16"))
            if (not os.path.isfile(folder + "/Ugc" + ugcFile)) & (New == False):
                NewSlot = str(x+1) + " - Add New Item"
                New = True
        if New:
            filledSlots.append(NewSlot)
    updateSlots(filledSlots)

def updateBackupState(*args):
    if modeVar.get() == "Import":
        backup_cb.state(['!disabled']) 
    else:
        backup_cb.state(['disabled'])

modeVar.trace_add("write", updateBackupState)
updateBackupState()

itemVar.trace_add(
    "write",
    lambda *args: getSlots(folderVar.get())
)

folderVar.trace_add(
    "write",
    lambda *args: getSlots(folderVar.get())
)

## Run script
## Using any args causes the CLI to activate, using none will start the GUI
if args.l:
    modeVar = "List"
    fileVar = 1
    ShareMii(modeVar,args.slot,args.save,fileVar)
    sys.exit(0)
if args.i:
    modeVar = "Import"
    fileVar = args.i
    ShareMii(modeVar,args.slot,args.save,fileVar, args.backup)
    sys.exit(0)
if args.o:
    modeVar = "Export"
    fileVar = args.o
    ShareMii(modeVar,args.slot,args.save,fileVar)
    sys.exit(0)
if args.a:
    fileVar = os.path.join(args.a,"auto")
    modeVar = "Export"
    getSlots(args.save)
    names = slotEntry["values"]
    names = names[1:]
    for x in range(len(names)):
            slot = names[x]
            slot = int(slot.split(" - ")[0])
            ShareMii(modeVar,slot,args.save,fileVar)
    sys.exit(0)
else:
    sys.stdout = TextRedirector(guiOutput)
    sys.stderr = TextRedirector(guiOutput)
    root.mainloop()