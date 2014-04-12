from ZP_Prediction import ZP_Prediction
import re
import time

if __name__ == "__main__":
    dat = []
    file = open('aprs.xml','r')
    for line in file:
        r = re.findall(r'(.+) (.+) (.+) (.+)\r',line)
        if r:
            dat.append((r[0][1],r[0][2],r[0][3]))
    file.close()
    while True:
        if dat:
            zp = ZP_Prediction(dat[-1][0],dat[-1][1],dat[-1][2], 301, 10800)
        else:
            zp = ZP_Prediction(41.9439, -85.6325, 301, 10800)

        zp.set_params(2, 10.59, 6.0, 113.267, 2830.42)

        zp.mainloop()

        time.sleep(120)
