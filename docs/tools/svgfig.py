"""
svgfig.py  -  a small SVG figure writer for the wiki pictures, standard library only: a bold title, a grey subtitle,
framed panels with numbered badges, callout boxes with a leader line that ends in a dot, dimension lines with
their value in a box, and a bold caption with grey text under each panel.  Text widths are estimated (DejaVu
Sans), so the boxes fit any common sans-serif font.  The same input always gives the same bytes.
"""

import html

FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"
INK, GREY, FRAME, BOX_EDGE = "#1a1a1a", "#555555", "#c4c4c4", "#bdbdbd"
CHAR = 0.6          # a character's width for a box, in em: a little more than DejaVu Sans (0.55) or Arial needs
CHAR_WRAP = 0.56    # for wrapping a paragraph, which has room to spare at the end of each line


def text_width(s, size, bold=False, char=CHAR):
    return len(s) * size * (char + (0.04 if bold else 0.0))


def wrap(text, size, width, bold=False):
    """The lines of `text` that fit `width` px at `size` px."""
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if line and text_width(trial, size, bold, CHAR_WRAP) > width:
            out.append(line)
            line = word
        else:
            line = trial
    if line:
        out.append(line)
    return out


def n(v):
    """A number for the SVG text: at most 2 decimals, no trailing zeros."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Figure:
    def __init__(self, width, title):
        self.w = width
        self.name = title
        self.items = []
        self.y = 0.0

    # --------------------------------------------------------------------------------------------- primitives
    def rect(self, x, y, w, h, fill, stroke="none", sw=1.0, dash=None, rx=0.0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{n(rx)}"' if rx else ""
        self.items.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"{r} fill="{fill}" '
                          f'stroke="{stroke}" stroke-width="{n(sw)}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" stroke="{stroke}" '
                          f'stroke-width="{n(sw)}"{d}/>')

    def circle(self, x, y, r, fill=INK):
        self.items.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{fill}"/>')

    def text(self, x, y, s, size=13, fill=INK, bold=False, anchor="start"):
        b = ' font-weight="bold"' if bold else ""
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.items.append(f'<text x="{n(x)}" y="{n(y)}" font-size="{n(size)}"{b}{a} fill="{fill}">'
                          f'{html.escape(s, quote=False)}</text>')

    # --------------------------------------------------------------------------------------------- composites
    def title(self, title, subtitle, margin=24, size=24, sub=15):
        self.y = margin + size
        self.text(margin, self.y, title, size, INK, bold=True)
        self.y += 8
        for line in wrap(subtitle, sub, self.w - 2 * margin):
            self.y += sub + 6
            self.text(margin, self.y, line, sub, GREY)
        self.y += 18

    def caption(self, x, width, head, body, size=15):
        self.y += 28
        self.text(x, self.y, head, size + 2, INK, bold=True)
        self.y += 4
        for line in wrap(body, size, width):
            self.y += size + 6
            self.text(x, self.y, line, size, GREY)
        self.y += 18

    def badge(self, x, y, label):
        self.circle(x, y, 12)
        self.text(x, y + 5, str(label), 15, "#ffffff", bold=True, anchor="middle")

    def box(self, x, y, lines, size=13, fill="#ffffff", edge=BOX_EDGE, ink=INK):
        """A rounded box with `lines` at (x, y) (top left).  Returns (width, height)."""
        w = max(text_width(s, size) for s in lines) + 16
        h = len(lines) * (size + 5) + 9
        self.rect(x, y, w, h, fill, edge, 1.0, rx=3)
        for i, s in enumerate(lines):
            self.text(x + 8, y + 6 + (i + 1) * (size + 5) - 4, s, size, ink)
        return w, h

    def leader(self, bx, by, w, h, tx, ty):
        """A leader from the edge of the box (bx, by, w, h) nearest the target to a dot at (tx, ty)."""
        sx = min(max(tx, bx), bx + w)
        sy = by + h if ty > by + h else by if ty < by else ty
        self.line(sx, sy, tx, ty, INK, 0.9)
        self.circle(tx, ty, 2.6)

    def svg(self, height=None):
        h = self.y + 8 if height is None else height
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{n(self.w)}" height="{n(h)}" '
                f'viewBox="0 0 {n(self.w)} {n(h)}" font-family="{FONT}">\n'
                f'<title>{html.escape(self.name, quote=False)}</title>\n'
                f'<rect width="100%" height="100%" fill="#ffffff"/>\n' + "\n".join(self.items) + "\n</svg>\n")
