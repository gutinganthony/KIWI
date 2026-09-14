import pymupdf, sys, os
def render(svg_path, png_path, dpi=200):
    d = pymupdf.open(svg_path)
    doc = pymupdf.open("pdf", d.convert_to_pdf())
    pix = doc[0].get_pixmap(dpi=dpi)
    pix.save(png_path)
    return pix.width, pix.height
if __name__ == "__main__":
    for f in sys.argv[1:]:
        png = f.replace(".svg", ".png")
        w,h = render(f, png)
        print(f"{os.path.basename(png)}  {w}x{h}")
