import sys
import glob
import os

font_header = sys.argv[1]
font_list = sys.argv[2:]

with open(font_header, "w", encoding="utf-8") as g:

    g.write("/* THIS FILE IS GENERATED DO NOT EDIT */\n")
    g.write("#ifndef _EDITOR_FONTS_H\n")
    g.write("#define _EDITOR_FONTS_H\n")

    # Saving uncompressed, since FreeType will reference from memory pointer.
    for i in range(len(font_list)):
        with open(font_list[i], "rb") as f:
            buf = f.read()

        name = os.path.splitext(os.path.basename(font_list[i]))[0]

        g.write("static const int _font_" + name + "_size = " + str(len(buf)) + ";\n")
        g.write("static const unsigned char _font_" + name + "[] = {\n")
        for j in range(len(buf)):
            g.write("\t" + str(buf[j]) + ",\n")

        g.write("};\n")

    g.write("#endif\n")
