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

ugcTypeString = list(["Food","Clothing","Treasure","Interior","Exterior","Objects","Landscaping"])
ugcTypeIndex = list(["Food","Cloth","Goods","Interior","Exterior","MapObject","MapFloor"])

def ugcStart(mode: str, slot: int, save: str, ugcpath:str, isAdding:bool, ugcKind:int):

    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())

    slot -= 1

    if mode == "Import":
        with open(ugcpath, "rb") as f:
            ugc = bytearray(f.read())
        if ugc[0] != ugcKind:
            raise RuntimeError(str("Incorrect ugcType found. Expected " + ugcTypeString[ugcKind] +", got " + ugcTypeString[ugc[0]]))
    if ugcKind == 0: # Food
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
        vOffset=0
    if ugcKind == 1: # Clothes
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
        vOffset=0
        v2Offset=0
    if ugcKind == 2: # Goods
        ## Anything
        fOffset1=offsetLocator(playersav,"3FAA2222") + 4 # UGC.Goods.UgcGoodsType
        fOffset2=offsetLocator(playersav,"823F8297") + 4 # UGC.Goods.UgcGoodsFeature
        fOffset3=offsetLocator(playersav,"7ECC8A60") + 4 # UGC.Goods.OtherEffect
        ## Book
        vOffset=offsetLocator(playersav,"F36C4E28") + 4 # UGC.Goods.BaseColor
        fOffset7=offsetLocator(playersav,"88DC1D43") + 4 # UGC.Goods.BookType
        ## CD
        fOffset8=offsetLocator(playersav,"8896DDD6") + 4 # UGC.Goods.CDSound
        ## DVD
        fOffset9=offsetLocator(playersav,"BFF29472") + 4 # UGC.Goods.DVDSound
        ## Game
        fOffset10=offsetLocator(playersav,"5D965762") + 4 # UGC.Goods.GameSound
        ## Pet
        fOffset11=offsetLocator(playersav,"78D39208") + 4 # UGC.Goods.PetBehavior
        fOffset12=offsetLocator(playersav,"53C762B0") + 4 # UGC.Goods.PetDirection
        fOffset13=offsetLocator(playersav,"40D2C6FE") + 4 # UGC.Goods.PetVoiceEffectType
        fOffset14=offsetLocator(playersav,"C0A6C046") + 4 # UGC.Goods.PetVoiceType
        ## Everything
        lOffset1=offsetLocator(playersav,"AE373B0D") + 4 # UGC.Goods.EmissionIntensity
        lOffset2=offsetLocator(playersav,"7D5FFBB7") + 4 # UGC.Goods.EmissionPattern
        lOffset3=offsetLocator(playersav,"9E978F5E") + 4 # UGC.Goods.IsEmissionNightOnly
        lOffset4=offsetLocator(playersav,"F6349929") + 4 # UGC.Goods.WordAttrCount
        lOffset5=offsetLocator(playersav,"9038CDD0") + 4 # UGC.Goods.WordAttrGrammaticality
        lOffset6=offsetLocator(playersav,"9A59F58A") + 4 # UGC.Goods.Price
        nOffset1=offsetLocator(playersav,"2F793EB1") + 4 # UGC.Goods.Name
        nOffset2=offsetLocator(playersav,"F655B33A") + 4 # UGC.Goods.HowToCallName
        nOffset3=offsetLocator(playersav,"F36A5A0B") + 4 # UGC.Goods.GoodsText
        nOffset4=offsetLocator(playersav,"A66367EB") + 4 # UGC.Goods.HowToCallGoodsText
        ugcOffsets=list([fOffset1,fOffset2,fOffset3,fOffset7,fOffset8,fOffset9,fOffset10,fOffset11,fOffset12,fOffset13,fOffset14,lOffset1,lOffset2,lOffset3,lOffset4,lOffset5,lOffset6])
        nOffsets=list([nOffset1,nOffset2,nOffset3,nOffset4])
        v2Offset=0
    if ugcKind == 3: # Interior
        fOffset1=offsetLocator(playersav,"A9116402") + 4 # UGC.Interior.UgcInteriorMaterialType
        fOffset2=offsetLocator(playersav,"835114C1") + 4 # UGC.Interior.UgcImpressionType
        lOffset1=offsetLocator(playersav,"EC65E2E4") + 4 # UGC.Interior.EmissionIntensity
        lOffset2=offsetLocator(playersav,"0A7CF2C5") + 4 # UGC.Interior.EmissionPattern
        lOffset3=offsetLocator(playersav,"60E280FB") + 4 # UGC.Interior.IsEmissionNightOnly
        lOffset4=offsetLocator(playersav,"01B3661E") + 4 # UGC.Interior.WordAttrCount
        lOffset5=offsetLocator(playersav,"5AF4A09F") + 4 # UGC.Interior.WordAttrGrammaticality
        lOffset6=offsetLocator(playersav,"41FF2201") + 4 # UGC.Interior.Price
        nOffset1=offsetLocator(playersav,"3DE2C5DD") + 4 # UGC.Interior.Name
        nOffset2=offsetLocator(playersav,"85A37B90") + 4 # UGC.Interior.HowToCallName
        ugcOffsets=list([fOffset1,fOffset2,lOffset1,lOffset2,lOffset3,lOffset4,lOffset5,lOffset6])
        nOffsets=list([nOffset1,nOffset2])
        vOffset=0
        v2Offset=0
    if ugcKind == 4: # Exterior
        fOffset1=offsetLocator(playersav,"ED95CF0F") + 4 # UGC.Exterior.UgcMaterialType
        fOffset2=offsetLocator(playersav,"43F509BA") + 4 # UGC.Exterior.UgcImpressionType
        fOffset3=offsetLocator(playersav,"A7A0773C") + 4 # UGC.Exterior.UgcMapObjectType
        fOffset4=offsetLocator(playersav,"A7A0773C") + 4 # UGC.Exterior.Size
        fOffset5=offsetLocator(playersav,"34BA6119") + 4 # UGC.Exterior.UvPatternIdx
        lOffset1=offsetLocator(playersav,"5E6E9F8C") + 4 # UGC.Exterior.EmissionIntensity
        lOffset2=offsetLocator(playersav,"2907C040") + 4 # UGC.Exterior.EmissionPattern
        lOffset3=offsetLocator(playersav,"97865D6B") + 4 # UGC.Exterior.IsEmissionNightOnly
        lOffset4=offsetLocator(playersav,"609F197D") + 4 # UGC.Exterior.WordAttrCount
        lOffset5=offsetLocator(playersav,"47A50525") + 4 # UGC.Exterior.WordAttrGrammaticality
        lOffset6=offsetLocator(playersav,"71EA7734") + 4 # UGC.Exterior.Price
        nOffset1=offsetLocator(playersav,"27C875D6") + 4 # UGC.Exterior.Name
        nOffset2=offsetLocator(playersav,"0E15E3F8") + 4 # UGC.Exterior.HowToCallName
        ugcOffsets=list([fOffset1,fOffset2,fOffset3,fOffset4,fOffset5,lOffset1,lOffset2,lOffset3,lOffset4,lOffset5,lOffset6])
        nOffsets=list([nOffset1,nOffset2])
        vOffset=offsetLocator(playersav,"3C14025E") + 4 # UGC.Goods.BaseColor
        v2Offset=offsetLocator(playersav,"B9D21B4F") + 4 # UGC.Exterior.MaterialTexScale
    shareUGC(mode, slot, save, ugcpath, ugcKind, ugcOffsets,nOffsets, vOffset, v2Offset, isAdding)
    return()

def shareUGC(mode: str, slot: int, save: str, ugcpath:str, ugcKind:int, ugcOffsets:list, nOffsets:list, vOffset:int,v2Offset:int, isAdding:bool):
    ugcType= ugcTypeIndex[ugcKind]
    with open(save + "/Player.sav", "rb") as f:
        playersav = bytearray(f.read())

    EOffset1=offsetLocator(playersav,"F4A39965") + 4 # Food
    EOffset2=offsetLocator(playersav,"AF129C33") + 4 # Cloth
    EOffset3=offsetLocator(playersav,"1A9C00FE") + 4 # Goods
    EOffset4=offsetLocator(playersav,"A39744E9") + 4 # Interior
    EOffset5=offsetLocator(playersav,"F4BEADC2") + 4 # Exterior
    EOffset6=offsetLocator(playersav,"5951050B") + 4 # MapObject
    EOffset7=offsetLocator(playersav,"A1126D32") + 4 # MapFloor
    ugcEnableOffsets= list([EOffset1,EOffset2,EOffset3,EOffset4,EOffset5,EOffset6,EOffset7])
    TOffset1=offsetLocator(playersav,"3558B77F") + 4 # Food
    TOffset2=offsetLocator(playersav,"59BFA9D3") + 4 # Cloth
    TOffset3=offsetLocator(playersav,"70D10A48") + 4 # Goods
    TOffset4=offsetLocator(playersav,"E7F9D439") + 4 # Interior
    TOffset5=offsetLocator(playersav,"16227C50") + 4 # Exterior
    TOffset6=offsetLocator(playersav,"A9C5CFB8") + 4 # MapObject
    TOffset7=offsetLocator(playersav,"06A7A14C") + 4 # MapFloor
    ugcTexOffsets = list([TOffset1,TOffset2,TOffset3,TOffset4,TOffset5,TOffset6,TOffset7])
    HOffset1=offsetLocator(playersav,"6D48F8E2") + 4 # Food
    HOffset2=offsetLocator(playersav,"89F25CAC") + 4 # Cloth
    HOffset3=offsetLocator(playersav,"56202100") + 4 # Goods
    HOffset4=offsetLocator(playersav,"7FEF7F7D") + 4 # Interior
    HOffset5=offsetLocator(playersav,"38D72795") + 4 # Exterior
    HOffset6=offsetLocator(playersav,"1B28B170") + 4 # MapObject
    HOffset7=offsetLocator(playersav,"816D50A3") + 4 # MapFloor
    ugcHashOffsets = list([HOffset1,HOffset2,HOffset3,HOffset4,HOffset5,HOffset6,HOffset7])
    ugcHashIndex = list([1,3,2,6,7])

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

        if (ugcKind in range(1,2)) & (isAdding == False):
            if playersav[ugcOffsets[0]+(slot)*4:ugcOffsets[0]+(slot)*4+4] != ugc[4:4+4]:
                raise RuntimeError("This item is not the same subtype as what you're importing! Find the same type or add the item.")

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
        print("UGC successfully copied to " + save + "/Ugc/Ugc" + ugcFile)

        ## TEXTURES END ##

        ## UGC data ##
        print("Replacing UGC data...")
        # Apply personality changes
        for x in range(len(ugcOffsets)):
            playersav[ugcOffsets[x]+(slot)*4:ugcOffsets[x]+(slot)*4+4] = ugc[4+x*4:4+x*4+4]

        if isAdding:
            playersav[ugcEnableOffsets[ugcKind]+(slot)*4:ugcEnableOffsets[ugcKind]+(slot)*4+4] = bytearray.fromhex("F4 AD 7F 1D")
            playersav[ugcTexOffsets[ugcKind]+(slot)*4:ugcTexOffsets[ugcKind]+(slot)*4+4] = bytearray.fromhex("41 49 93 56")
            playersav[ugcHashOffsets[ugcKind]+(slot)*4:ugcHashOffsets[ugcKind]+(slot)*4+4] = bytearray([slot, 0, int(ugcHashIndex[ugcKind]), 0])

        playersav[nOffsets[0]+((slot)*128):nOffsets[0]+((slot)*128)+128] = ugc[nameStart:nameStart+128]
        playersav[nOffsets[1]+((slot)*128):nOffsets[1]+((slot)*128)+128] = ugc[nameStart+128:nameStart+(128*2)]
        if ugcKind == 2:
            playersav[nOffsets[2]+((slot)*64):nOffsets[2]+((slot)*64)+64] = ugc[nameStart+(128*2):nameStart+(128*2)+64]
            playersav[nOffsets[3]+((slot)*128):nOffsets[3]+((slot)*128)+128] = ugc[nameStart+(128*2)+64:nameStart+(128*3)+64]
        if vOffset:
            playersav[vOffset+((slot)*12):vOffset+((slot)*12)+12] = ugc[nameStart-24:nameStart-12]
        if v2Offset:
            playersav[vOffset+((slot)*8):vOffset+((slot)*8)+8] = ugc[nameStart-12:nameStart-4]
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
        for x in range(len(ugcOffsets)):
            CurrentUGCV=playersav[ugcOffsets[x]+(slot)*4:ugcOffsets[x]+(slot)*4+4]
            ugcData.extend(CurrentUGCV)
        
        ltdData = bytearray([ugcKind, 0, 0, 0])
        name = playersav[nOffsets[0]+((slot)*128):nOffsets[0]+((slot)*128)+128]
        pronounce = playersav[nOffsets[1]+((slot)*128):nOffsets[1]+((slot)*128)+128]
        if ugcKind ==2:
            goodsText = playersav[nOffsets[2]+((slot)*64):nOffsets[2]+((slot)*64)+64]
            goodsPronounce = playersav[nOffsets[3]+((slot)*128):nOffsets[3]+((slot)*128)+128]
            pronounce.extend(goodsText)
            pronounce.extend(goodsPronounce)
        if vOffset:
            vector = playersav[vOffset+((slot)*12):vOffset+((slot)*12)+12]
        else:
            vector = bytearray(12)
        if v2Offset:
            vector2 = playersav[vOffset+((slot)*8):vOffset+((slot)*8)+8]
        else:
            vector2 = bytearray(8)
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

        output = ltdData + ugcData + vector + vector2 + nameSection + name + pronounce + canvasSection + canvastex + ugcSection + ugctex + thumbSection + thumbtex

        ## If user didn't give a name, we'll just set the name to their Mii name
        if (ugcpath[-4:] == "auto"):
                ugcpath = ugcpath[:-4] + sanitName

        if ".ltdc" not in ugcpath:
            ugcpath += ".ltdc"

        with open(ugcpath, "wb") as f:
            f.write(output)

        print("Success! " + printName.decode("utf-16") + " written to " + ugcpath)