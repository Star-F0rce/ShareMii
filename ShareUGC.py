import struct
import os
import re
from pathlib import Path

def offsetLocator(file, hashStr):
    hash = bytes.fromhex(hashStr)
    littleHash = hash[::-1]

    index = file.find(littleHash)
    if index == -1:
        return None
    offsetBytes = file[index + 4:index + 8]
    offset = struct.unpack('<I', offsetBytes)[0]
    
    return offset

ugcTypeString = list(["Food","Clothing"])
ugcTypeIndex = list(["Food","Cloth"])

def ShareFood(mode: str, slot: int, save: str, ugcpath:str):

    ugcKind=0

    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())
    
    if mode == "Import":
        with open(ugcpath, "rb") as f:
            ugc = bytearray(f.read())
        if ugc[0] != 0:
            raise RuntimeError(str("Incorrect ugcType found. Expected " + ugcTypeString[0] +", got " + ugcTypeString[ugc[0]]))

    slot -= 1

    ## Offsets
    fOffset1=offsetLocator(playersav,"307FEEFA") + 4 # UGC.Food.AttrTaste
    fOffset2=offsetLocator(playersav,"6F93FFBD") + 4 # UGC.Food.AttrType
    fOffset3=offsetLocator(playersav,"5CA9336E") + 4 # UGC.Food.Temperature
    fOffset4=offsetLocator(playersav,"F768620A") + 4 # UGC.Food.BaseScale
    fOffset5=offsetLocator(playersav,"5AF04BEB") + 4 # UGC.Food.EmissionIntensity
    fOffset6=offsetLocator(playersav,"2DB168C5") + 4 # UGC.Food.EmissionPattern
    fOffset7=offsetLocator(playersav,"634800AE") + 4 # UGC.Food.IsEmissionNightOnly
    fOffset8=offsetLocator(playersav,"DD8D6C5A") + 4 # UGC.Food.WordAttrCount
    fOffset9=offsetLocator(playersav,"AF1186CF") + 4 # UGC.Food.WordAttrGrammaticality
    fOffset10=offsetLocator(playersav,"58E6AAD3") + 4 # UGC.Food.Price
    nOffset1=offsetLocator(playersav,"408494F5") + 4 # UGC.Food.Name
    nOffset2=offsetLocator(playersav,"BA0F4BAF") + 4 # UGC.Food.HowToCallName
    ugcOffsets=list([fOffset1,fOffset2,fOffset3,fOffset4,fOffset5,fOffset6,fOffset7,fOffset8,fOffset9,fOffset10])
    nOffsets=list([nOffset1,nOffset2])
    shareUGC(mode, slot, save, ugcpath, ugcKind, ugcOffsets,nOffsets)
    return()

def ShareCloth(mode: str, slot: int, save: str, ugcpath:str):

    ugcKind=1

    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())
    
    if mode == "Import":
        with open(ugcpath, "rb") as f:
            ugc = bytearray(f.read())
        if ugc[0] != ugcKind:
            raise RuntimeError(str("Incorrect ugcType found. Expected " + ugcTypeString[ugcKind] +", got " + ugcTypeString[ugc[0]]))

    slot -= 1

    ## Offsets
    fOffset1=offsetLocator(playersav,"C81545FE") + 4 # UGC.Cloth.UgcClothType
    fOffset2=offsetLocator(playersav,"2FB9146D") + 4 # UGC.Cloth.ClothSeasonType
    fOffset3=offsetLocator(playersav,"7A31EF97") + 4 # UGC.Cloth.UgcClothGenreType
    fOffset4=offsetLocator(playersav,"7EEC35E9") + 4 # UGC.Cloth.ClothGender
    lOffset1=offsetLocator(playersav,"5E32FD3F") + 4 # UGC.Cloth.EmissionIntensity
    lOffset2=offsetLocator(playersav,"0DBABE27") + 4 # UGC.Cloth.EmissionPattern
    lOffset3=offsetLocator(playersav,"71621C98") + 4 # UGC.Cloth.IsEmissionNightOnly
    lOffset4=offsetLocator(playersav,"2D271339") + 4 # UGC.Cloth.WordAttrCount
    lOffset5=offsetLocator(playersav,"CDF31EB5") + 4 # UGC.Cloth.WordAttrGrammaticality
    lOffset6=offsetLocator(playersav,"2823DBD3") + 4 # UGC.Cloth.Price
    nOffset1=offsetLocator(playersav,"40710642") + 4 # UGC.Cloth.Name
    nOffset2=offsetLocator(playersav,"CF9A13EA") + 4 # UGC.Cloth.HowToCallName
    ugcOffsets=list([fOffset1,fOffset2,fOffset3,fOffset4,lOffset1,lOffset2,lOffset3,lOffset4,lOffset5,lOffset6])
    nOffsets=list([nOffset1,nOffset2])
    shareUGC(mode, slot, save, ugcpath, ugcKind, ugcOffsets,nOffsets)
    return()

def shareUGC(mode: str, slot: int, save: str, ugcpath:str, ugcKind:int, ugcOffsets:list, nOffsets:list):
    ugcType= ugcTypeIndex[ugcKind]
    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())
    ## LIST MODE ###################################################################
    if mode == "List":
        for x in range(99):
            if x < 10:
                ugcFile = "/Ugc"+ ugcType + "00" + str(x) + ".canvas.zs"
            else:
                ugcFile = "/Ugc"+ ugcType + "0" + str(x) + ".canvas.zs"
            ugcName = playersav[nOffsets[0]+((x)*128):nOffsets[0]+((x)*128)+128]
            if os.path.isfile(save + "/Ugc" + ugcFile):
                ugcPrintName = ugcName[:ugcName.find(bytes.fromhex("00 00 00"))]
                if len(ugcPrintName) % 2 == 1:
                    ugcPrintName.append(0)
                print(str(x+1) + " - " + ugcPrintName.decode("utf-16"))
        return()
    
    ## IMPORT MODE #################################################################
    if mode == "Import":
        # Import the args
        with open(ugcpath, "rb") as f:
            ugc = bytearray(f.read())

        #Find where block files begin
        nameStart = ugc.find(bytes.fromhex("A2 A2 A2 A2")) + 4
        canvasStart = ugc.find(bytes.fromhex("A3 A3 A3 A3")) + 4
        ugcStart = ugc.find(bytes.fromhex("A4 A4 A4 A4")) + 4
        thumbStart = ugc.find(bytes.fromhex("A5 A5 A5 A5")) + 4

        ## TEXTURES ##

        if slot < 10:
            ugcFile = ugcType + "00" + str(slot)
        else:
            ugcFile = ugcType + "0" + str(slot)
        #Copying the textures.
        with open(save + "/Ugc/Ugc" + ugcFile + ".canvas.zs", "wb") as f:
            f.write(ugc[canvasStart:ugcStart - 4])
        with open(save + "/Ugc/Ugc" + ugcFile + ".ugctex.zs", "wb") as f:
            f.write(ugc[ugcStart:thumbStart - 4])
        with open(save + "/Ugc/Ugc" + ugcFile + "_Thumb.ugctex.zs", "wb") as f:
            f.write(ugc[thumbStart:])
        print("UGC successfully copied to " + save + "/Ugc/UgcFood" + ugcFile)

        ## TEXTURES END ##

        ## UGC data ##
        print("Replacing UGC data...")
        # Apply personality changes
        for x in range(len(ugcOffsets)):
            playersav[ugcOffsets[x]+(slot)*4:ugcOffsets[x]+(slot)*4+4] = ugc[4+x*4:4+x*4+4]


        playersav[nOffsets[0]+((slot)*128):nOffsets[0]+((slot)*128)+128] = ugc[nameStart:nameStart+128]
        playersav[nOffsets[1]+((slot)*128):nOffsets[1]+((slot)*128)+128] = ugc[nameStart+128:nameStart+(128*2)]
        print("Personal data replaced!")

        with open(save + "/Player.sav", "wb") as f:
            f.write(playersav)
        print("Item successfully imported.")
    ## EXPORT MODE #################################################################
    if mode == "Export":
        
        print("Exporting " + ugcType + " to file...")

        ### PERSONALITY ###
        ugcData=bytearray()
        # This loop grabs nearly all personality aspects from a Mii
        for x in range(10):
            CurrentUGCV=playersav[ugcOffsets[x]+(slot)*4:ugcOffsets[x]+(slot)*4+4]
            ugcData.extend(CurrentUGCV)
        
        ltdData = bytearray([ugcKind, 0, 0, 0])
        name = playersav[nOffsets[0]+((slot)*128):nOffsets[0]+((slot)*128)+128]
        pronounce = playersav[nOffsets[1]+((slot)*128):nOffsets[1]+((slot)*128)+128]
        nameSection = bytearray.fromhex('A2 A2 A2 A2')
        canvasSection = bytearray.fromhex('A3 A3 A3 A3')
        ugcSection = bytearray.fromhex('A4 A4 A4 A4')
        thumbSection = bytearray.fromhex('A5 A5 A5 A5')

        printName = name[:name.find(bytes.fromhex("00 00 00"))]
        if len(printName) % 2 == 1:
            printName.append(0)

        sanitName = printName.decode("utf-16")
        sanitName = re.sub(r'[^\w.-]', '_', sanitName)

        print("Exporting " + printName.decode("utf-16") + " to file...")

        if slot < 10:
            ugcFile = ugcType + "00" + str(slot)
        else:
            ugcFile = ugcType + "0" + str(slot)

        with open(save + "/Ugc/Ugc" + ugcFile + ".canvas.zs", "rb") as f:
            canvastex = bytearray(f.read())
        with open(save + "/Ugc/Ugc" + ugcFile + ".ugctex.zs", "rb") as f:
            ugctex = bytearray(f.read())
        with open(save + "/Ugc/Ugc" + ugcFile + "_Thumb.ugctex.zs", "rb") as f:
            thumbtex = bytearray(f.read())

        output = ltdData + ugcData + nameSection + name + pronounce + canvasSection + canvastex + ugcSection + ugctex + thumbSection + thumbtex

        ## If user didn't give a name, we'll just set the name to their Mii name
        if (ugcpath[-4:] == "auto"):
                ugcpath = ugcpath[:-4] + sanitName

        if ".ltdc" not in ugcpath:
            ugcpath += ".ltdc"

        with open(ugcpath, "wb") as f:
            f.write(output)

        print("Success! " + printName.decode("utf-16") + " written to " + ugcpath)