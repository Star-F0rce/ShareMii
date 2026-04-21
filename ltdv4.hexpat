struct entry {
    u32 hash;
    u32 type;
    // value, if string have the length before
};

struct ltd {
    u8 version; // v4
    bool hasFacePaintCanvas;
    bool hasFacePaintTex;
    u8 entryCount; 

    entry entries[entryCount];
    
    if (hasFacePaintCanvas) {
      u32 canvasMagic;
      u32 canvasSize;
      u8 canvasData[canvasSize];
    }

    if (hasFacePaintTex) {
      u32 texMagic;
      u32 texSize;
      u8 texData[texSize];
    }
}