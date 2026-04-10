import argparse
import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk
import sv_ttk
import darkdetect
from pathlib import Path
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from tkinterdnd2 import DND_FILES, TkinterDnD

majVersion = 3
minVersion = 1
versionStr = str(majVersion) + "." + str(minVersion)

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
        ShareMii("List", 1, selectedDirectory, "2")
        getSlots(selectedDirectory)
        slotEntry.current(1)

## Used to browse files in GUI
def browseFile():
    # Opens folder selection dialog
    if modeVar.get() == "Import":
        selectedDirectory = filedialog.askopenfilename(defaultextension=".ltd", filetypes=[('LtD Mii Files', '*.ltd')])
    else:
        selectedDirectory = filedialog.asksaveasfilename(defaultextension=".ltd", filetypes=[('LtD Mii Files', '*.ltd')])
    
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
        ShareMii("List", 1, path, "2")
        getSlots(path)
        slotEntry.current(1)
    else:
        fileVar.set(path)

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
parser.add_argument("save", type=str, help="save folder location", nargs="?")
parser.add_argument("slot", type=int, help="Mii slot to import/export", nargs="?")

args = parser.parse_args()

def ShareMii(mode: str, slot: int, save: str, miipath:str):

    ## Lazily redirecting into old stuff
    
    if mode == "Export":
        args.o = miipath
        args.i = False
        args.l = False
    if mode == "Import":
        args.i = miipath
        args.o = False
        args.l = False
    if mode == "List":
        args.l = True
    args.slot = slot
    args.save = save
    if args.l:
        args.slot = 1

    if args.slot > 70:
        raise RuntimeError("Invalid slot. Please choose a slot 0-70.")
    if args.slot < 0:
        raise RuntimeError("Invalid slot. Please choose a slot 0-70.")

    args.slot -= 1

    with open(args.save + "/Mii.sav", "rb") as f:
        miisav = bytearray(f.read())

    with open(args.save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())

    #Ensure the slots match in-game

    # Offsets
    fpOffset1=int("C1CC",16) # Facepaint Flags.. or something? They make facepaints work.
    fpOffset2=int("45AB0",16)
    fpOffset3=int("46864",16)
    fpOffset4=int("6354C",16)
    fpOffset5=int("63EC8",16)
    miiOffset1=int("11420",16) # Mii Sort IDs
    miiOffset2=int("EFA4",16) # Mii Facepaint IDs
    miiOffset3=int("616E0",16) # Temp Slot Mii Offset
    miiOffset4=int("289E84",16) # Earliest offset for names
    miiOffset5=int("2C7FAC",16) # Earliest offset for pronounce
    miiOffset6=int("1FE6E4",16) # Earliest offset for Mii data
    persOffsetP1=int("F414",16) # Personality Values
    persOffsetSX=int("23AC",16) # x27
    persOffsets=list([int("F414",16),int("FF1C",16),int("107F8",16),int("10A30",16),int("10B4C",16),int("5F8C",16),int("96E0",16),int("F0C0",16),int("F2F8",16),int("FCE4",16),int("329D4",16),int("1A7B8",16),int("15008",16),int("271C0",16),int("5B1C",16),int("5D54",16),int("5E70",16),int("11890",16)])
    #Check to see if the slot the user desires matches the one in game. If not, pivot to that one
    # if (args.slot != -1) & (miisav[miiOffset1+4*(args.slot)] != 255):
    #     if miisav[miiOffset1+4*(args.slot)] != (args.slot):
    #         args.slot = int(miisav[miiOffset1+4*(args.slot)])

    #Count Miis in-game
    numMii=list()
    for x in range(69):
        if miisav[persOffsetP1+4*(x)] != 0:
            numMii.append(miisav[persOffsetP1+4*(x)])
    numMii = len(numMii)

    # Searchable Offsets
    miiindex = miiOffset6 + ((numMii - 1) * 280) + 156 * (args.slot)
    miinames = miiOffset4 + (numMii - 1) * 296
    miiprefer = miiOffset5 + (numMii - 1) * 296

    ## LIST MODE ###################################################################
    if args.l:
        for x in range(69):
            miiindex = miiOffset6 + ((numMii - 1) * 280) + 156 * (x)
            miilistname = miisav[miinames+((x)*64):miinames+((x)*64)+64]
            if sum(miisav[miiindex:miiindex+156]) != 152:
                printName = miilistname[:miilistname.find(bytes.fromhex("00 00 00"))]
                if len(printName) % 2 == 1:
                    printName.append(0)
                print(str(x+1) + " - " + printName.decode("utf-16"))
        return()

    ## IMPORT MODE #################################################################
    if args.i:
        # Import the args
        with open(args.i, "rb") as f:
            mii = bytearray(f.read())

        #Find where miis are stored in Mii.sav
        paintindex = fpOffset3 + 4 * (args.slot)
        canvasStart = mii.find(bytes.fromhex("A3 A3 A3")) + 3
        ugcStart = mii.rfind(bytes.fromhex("A3 A3 A3")) + 3
        facepaint = 0
        # AFAIK, with Player.sav, everything is static so we can just use those here
        if args.slot == -1:
            paintindex = fpOffset3 + 4 * 70
            miiindex = miiOffset3
        
        if mii[1:3] == bytearray.fromhex('01 01'):
            facepaint = 1
            mii[48] = 1
        if os.path.isfile(args.i + ".canvas.zs") & os.path.isfile(args.i + ".ugctex.zs"):
            facepaint = 2
            mii[48] = 1

        #Errors
        if sum(miisav[miiindex:miiindex+156]) == 152:
            raise RuntimeError("Mii not initialized! Please create a mii in this slot.")

        #Write to file
        if args.slot == -1:
            print("Writing Mii to the temporary slot...")
            playersav[miiindex:miiindex+156] = mii[5:5+156]
        else:
            print(f"Mii detected at {hex(miiindex)}! Replacing...")
            miisav[miiindex:miiindex+156] = mii[5:5+156]

        ## FACEPAINT ##

        #First we need to get the facepaint ID
        facepaintID=miisav[miiOffset2+4*(args.slot)]

        #If we detected facepaint earlier, we should copy it into the save file
        if facepaint:
            print("Facepaint detected! Copying...")
            #If we're replacing a mii that didn't initially have facepaint, we'll give it the next ID facepaint
            if facepaintID == 255:
                usedIDs=bytearray(70)
                for x in range(70):
                    if miisav[miiOffset2+4*(x)] != 255:
                        usedIDs[x]=miisav[miiOffset2+4*(x)]
                s = set(usedIDs)
                if s == {0}:
                    facepaintID = 0
                else:
                    for i in range(70):
                        if i not in s:
                            facepaintID=i
                            break

            #The fun part! Telling the game to read the facepaint files.
            if args.slot == -1:
                facepaintID = 70
                facepaintFile="070"
                playersav[fpOffset1+4*(facepaintID ):fpOffset1+4*(facepaintID )+4] = bytearray.fromhex('F4 01 00 00')
                playersav[fpOffset2+4*(facepaintID ):fpOffset2+4*(facepaintID )+4] = bytearray.fromhex('41 49 93 56')
                playersav[fpOffset5+4*(facepaintID ):fpOffset5+4*(facepaintID )+1] = bytearray.fromhex('46')
            else:
                miisav[miiOffset2+4*(args.slot):miiOffset2+4*(args.slot)+4] = bytearray([facepaintID, 0, 0, 0])
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
            UgcDir = Path(args.save + "/Ugc")
            UgcDir.mkdir(parents=True, exist_ok=True)


            if facepaint == 2:
                s_canvas = args.i + ".canvas.zs"
                d_canvas = args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs"
                s_ugc = args.i + ".ugctex.zs"
                d_ugc = args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs"
                shutil.copy(s_canvas, d_canvas)
                shutil.copy(s_ugc, d_ugc)
            else:
                with open(args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs", "wb") as f:
                    f.write(mii[canvasStart:ugcStart - 3])
                with open(args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs", "wb") as f:
                    f.write(mii[ugcStart:])
            print("Facepaint successfully copied.")

        #If the imported Mii doesn't have facepaint, we should remove the old one
        else:
            if facepaintID != 255:
                print("This new Mii no longer uses facepaint. Be sure to back up the old facepaint if you still want it.")
                miisav[miiOffset2+4*(args.slot):miiOffset2+4*(args.slot)+4] = bytearray.fromhex('FF FF FF FF')
                playersav[fpOffset1+4*(facepaintID ):fpOffset1+4*(facepaintID )+4] = bytearray.fromhex('00 00 00 00')
                playersav[fpOffset2+4*(facepaintID ):fpOffset2+4*(facepaintID )+4] = bytearray.fromhex('09 DE EE B6')
                playersav[fpOffset3+4*(facepaintID ):fpOffset3+4*(facepaintID )+4] = bytearray.fromhex('A5 8A FF AF')
                playersav[fpOffset4+4*(facepaintID ):fpOffset4+4*(facepaintID )+4] = bytearray.fromhex('00 00 00 00')
                playersav[fpOffset5+4*(facepaintID ):fpOffset5+4*(facepaintID )+4] = bytearray.fromhex('00 00 00 00')

        ## FACEPAINT END ##
        ## PERSONALITY ##
        if (mii[0] != 2) & (args.slot != -1):
            print("No personal data configured, skipping...")

        if (mii[0] == 2) & (args.slot != -1):
            print("Personality detected! Applying...")
            # Apply personality changes
            for x in range(18):
                miisav[persOffsets[x]+(args.slot)*4:persOffsets[x]+(args.slot)*4+4] = mii[161+x*4:161+x*4+4]

            miisav[miinames+((args.slot)*64):miinames+((args.slot)*64)+64] = mii[233:297]
            miisav[miiprefer+((args.slot)*128):miiprefer+((args.slot)*128)+128] = mii[297:425]
            miisexuality=list(mii[425:428])
            sexuality = miisav[persOffsetSX:persOffsetSX+27]
            sexuality = DecodeSexuality(sexuality)
            sexuality[(args.slot)*3:(args.slot)*3+3]=miisexuality
            sexuality = EncodeSexuality(sexuality)
            miisav[persOffsetSX:persOffsetSX+27] = sexuality
            print("Personality done!")

        with open(args.save + "/Mii.sav", "wb") as f:
            f.write(miisav)
        with open(args.save + "/Player.sav", "wb") as f:
            f.write(playersav)
        print("Mii successfully imported.")

    ## EXPORT MODE #################################################################
    if args.o:
        #Read inputs

        #Locate miis in Mii.sav
        paintindex = fpOffset3 + 4 * (args.slot)
        facepaint=False

        #Face paint detection
        if args.slot != -1:
            if miisav[miiOffset2+4*(args.slot):miiOffset2+4*(args.slot)+4] != bytearray.fromhex('FF FF FF FF'):
                facepaint=True
                facepaintID=miisav[miiOffset2+4*(args.slot)]

        #Check to see if using Temp Slot
        if args.slot == -1:
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
            CurrentPV=miisav[persOffsets[x]+(args.slot)*4:persOffsets[x]+(args.slot)*4+4]
            personality.extend(CurrentPV)
        # Sexuality is handled a bit differently so we need to decode what the Mii's sexuality is
        sexuality = miisav[persOffsetSX:persOffsetSX+27]
        sexuality = DecodeSexuality(sexuality)
        sexuality=sexuality[(args.slot)*3:(args.slot)*3+3]
        
        name = miisav[miinames+((args.slot)*64):miinames+((args.slot)*64)+64]
        pronounce = miisav[miiprefer+((args.slot)*128):miiprefer+((args.slot)*128)+128]
        section = bytearray.fromhex('A3 A3 A3')

        #Actually create the Mii file
        if args.slot == -1:
            miiVersion = 1
        else:
            miiVersion = 2
        ltdData = bytearray(4)
        #If facepaint is detected, copy and rename them
        if facepaint:
            if facepaintID < 10:
                facepaintFile = "00" + str(facepaintID)
            else:
                facepaintFile = "0" + str(facepaintID)
            print("Facepaint detected with ID " + str(facepaintID) +"! Grabbing..")
            # d_canvas = args.o + ".ltd.canvas.zs"
            # s_canvas = args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs"
            # d_ugc = args.o + ".ltd.ugctex.zs"
            # s_ugc = args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs"
            # shutil.copy(s_canvas, d_canvas)
            # shutil.copy(s_ugc, d_ugc)

            with open(args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".canvas.zs", "rb") as f:
                canvastex = bytearray(f.read())
                ltdData[0]=1
            with open(args.save + "/Ugc/UgcFacePaint" + facepaintFile + ".ugctex.zs", "rb") as f:
                ugctex = bytearray(f.read())
                ltdData[1]=1

        else:
            canvastex=bytearray()
            ugctex=bytearray()

        output = bytearray([miiVersion]) + ltdData + miisav[miiindex:miiindex+156] + personality + name + pronounce + bytearray(sexuality) + section + canvastex + section + ugctex

        printName = name[:name.find(bytes.fromhex("00 00 00"))]
        if len(printName) % 2 == 1:
            printName.append(0)

        ## If user didn't give a name, we'll just set the name to their Mii name
        if (args.o[-4:] == "auto"):
            args.o = args.o[:-4] + printName.decode("utf-16")
            if args.slot == -1:
                args.o = args.o[:-4] + "Mii"

        if ".ltd" not in args.o:
            args.o += ".ltd"

        with open(args.o, "wb") as f:
            f.write(output)
        
        if args.slot == -1:
            name=bytearray.fromhex("54 00 65 00 6D 00 70")

        print("Success! " + printName.decode("utf-16") + " written to " + args.o)

def beginProcess():
    guiOutput.delete("1.0", "end")
    folder = folderVar.get()
    mode = modeVar.get()
    file = fileVar.get()
    slot = slotVar.get()
    slot = int(slot[0])

    if (file == "Drag & drop or choose Mii here") & (mode == "Export"):
        file = "auto"
    if (os.path.isdir(file)) & (mode == "Export"):
        file = os.path.join(file,"auto")

    if mode != "Export All":
        ShareMii(mode, slot, folder, file)
        getSlots(folder)
    else:
        file = os.path.join(file,"auto")
        mode = "Export"
        names = slotEntry["values"]
        names = names[1:]
        for x in range(len(names)):
            slot = names[x]
            slot = int(slot[0])
            ShareMii(mode, slot, folder, file)



##GUI Setup
root = TkinterDnD.Tk()
root.title("ShareMii v" + versionStr + " GUI")
root.iconphoto(False, tk.PhotoImage(file=resourcePath("icon.png")))
root.geometry("800x500")
root.rowconfigure(6, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.resizable(True,True)
style = ttk.Style(root)

modeVar=tk.StringVar()
slotVar=tk.StringVar(value="1")
folderVar=tk.StringVar(value="Drag & drop or upload save folder here")
fileVar=tk.StringVar(value="Drag & drop or choose Mii here")

## Row 0
logo = tk.PhotoImage(file=resourcePath("logo.png"))
ttk.Label(root, image=logo).grid(row=0, column=1, padx=5, pady=5)

## Row 1
ttk.Label(root, text="Select Mode:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
modeEntry = ttk.OptionMenu(root, modeVar,"Import","Import", "Export", "Export All", "List").grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

## Row 2
ttk.Label(root, text="Select Save Folder:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
folderEntry = ttk.Entry(root, textvariable=folderVar, width=50)
folderEntry.drop_target_register(DND_FILES)
folderEntry.dnd_bind('<<Drop>>',dragndrop)
folderEntry.grid(row=2, column=1, padx=5, pady=5,sticky=tk.NSEW)
browseButton = ttk.Button(root, text="Browse...", width=12, command=browseFolder).grid(row=2, column=2, padx=3, pady=3, sticky=tk.W)

## Row 3
ttk.Label(root, text="Open/Save As Mii:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
fileEntry = ttk.Entry(root, textvariable=fileVar, width=50)
fileEntry.drop_target_register(DND_FILES)
fileEntry.dnd_bind('<<Drop>>',dragndrop)
fileEntry.grid(row=3, column=1, padx=5, pady=5,sticky=tk.NSEW)
browseButton = ttk.Button(root, text="Browse...", width=12, command=browseFile).grid(row=3, column=2, padx=3, pady=3, sticky=tk.W)

## Row 4
ttk.Label(root, text="Select Slot:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
slotEntry = ttk.Combobox(root, textvariable=slotVar, state="readonly")
slotEntry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
slotEntry["values"]=list(range(0, 71))

## Row 5
startButton = ttk.Button(root, text="Start!", command=beginProcess, width=20).grid(row=5, column=1, padx=5, pady=5)

## Row 6
guiOutput = ScrolledText(root,height=10,width=40)
guiOutput.grid(row=6, column=1,sticky=tk.NSEW)

sv_ttk.set_theme(darkdetect.theme())

def updateSlots(options):
    slotEntry["values"] = options

def getSlots(folder):

    with open(folder + "/Mii.sav", "rb") as f:
        miisav = bytearray(f.read())

    with open(folder + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())
    
    miiOffset3=399072
    miiOffset4=int("289E84",16)
    miiOffset6=int("1FE6E4",16) # Earliest offset for Mii data
    persOffsetP1=int("F414",16) # Personality Values

    if sum(playersav[miiOffset3:miiOffset3+156]) != 152:
        filledSlots = ["0 - In-Progress Mii"]
    else:
        filledSlots = ["0 - In-Progress Mii"] # Leaving this here in case I ever want to make it so it checks for temp slot being used.

    numMii=list()
    for x in range(69):
        if miisav[persOffsetP1+4*(x)] != 0:
            numMii.append(miisav[persOffsetP1+4*(x)])
    numMii = len(numMii)
    
    miinames = miiOffset4 + (numMii - 1) * 296

    for x in range(69):
        miiindex = miiOffset6 + ((numMii - 1) * 280) + 156 * (x)
        miilistname = miisav[miinames+((x)*64):miinames+((x)*64)+64]
        if sum(miisav[miiindex:miiindex+156]) != 152:
            printName = miilistname[:miilistname.find(bytes.fromhex("00 00 00"))]
            if len(printName) % 2 == 1:
                printName.append(0)
            filledSlots.append(str(x+1) + " - " + str(printName.decode("utf-16")))
    updateSlots(filledSlots)

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
    ShareMii(modeVar,args.slot,args.save,fileVar)
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
            slot = int(slot[0])
            ShareMii(modeVar,slot,args.save,fileVar)
    sys.exit(0)
else:
    sys.stdout = TextRedirector(guiOutput)
    sys.stderr = TextRedirector(guiOutput)
    root.mainloop()