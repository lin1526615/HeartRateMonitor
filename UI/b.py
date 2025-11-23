if  __name__ == '__main__':
    with open(r'_oldfiles\HR-icon_min.png', 'rb') as f:
        data = f.read()
        with open('UI/heartratepng.py', 'w') as g:
            g.write('img = "')
            g.write(data.hex())
            g.write('"')
            g.write("\n")
            g.write("heart_rate_png = bytes.fromhex(img)")
            g.write("\n")
            g.write("""from PyQt5.QtGui import QIcon, QPixmap
def get_icon():
    global HR_ICON
    if not 'HR_ICON' in globals():
        pixmap = QPixmap()
        pixmap.loadFromData(heart_rate_png)
        HR_ICON = QIcon(pixmap)
    return HR_ICON
__all__ = ['get_icon']
"""
            )