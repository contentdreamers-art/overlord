"""Generate original tileable color maps for Soulwood with Python's standard library."""
import math
import os
import random
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_textures')
os.makedirs(OUT, exist_ok=True)
SIZE = 512


def smooth(t):
    return t*t*(3-2*t)


def noise(x, y, period, seed):
    gx = x*period/SIZE
    gy = y*period/SIZE
    ix, iy = math.floor(gx), math.floor(gy)
    fx, fy = smooth(gx-ix), smooth(gy-iy)
    def value(a,b):
        a%=period; b%=period
        n=(a*374761393+b*668265263+seed*1442695041)&0xffffffff
        n=(n^(n>>13))*1274126177&0xffffffff
        return ((n^(n>>16))&65535)/65535
    low=value(ix,iy)*(1-fx)+value(ix+1,iy)*fx
    high=value(ix,iy+1)*(1-fx)+value(ix+1,iy+1)*fx
    return low*(1-fy)+high*fy


def channel(v):
    return max(0,min(255,int(v)))


def png(name, pixels):
    raw=bytearray()
    for y in range(SIZE):
        raw.append(0)
        raw.extend(pixels[y*SIZE*3:(y+1)*SIZE*3])
    def chunk(tag, data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    out=b'\x89PNG\r\n\x1a\n'
    out+=chunk(b'IHDR',struct.pack('>IIBBBBB',SIZE,SIZE,8,2,0,0,0))
    out+=chunk(b'IDAT',zlib.compress(bytes(raw),7))
    out+=chunk(b'IEND',b'')
    with open(os.path.join(OUT,name+'.png'),'wb') as f:
        f.write(out)


for name in ('T_ForestFloor','T_ForestPath','T_WeatheredStone'):
    data=bytearray(SIZE*SIZE*3)
    for y in range(SIZE):
        for x in range(SIZE):
            broad=noise(x,y,4,10)
            medium=noise(x,y,12,22)
            fine=noise(x,y,48,48)
            grain=noise(x,y,128,71)
            blend=.42*broad+.31*medium+.19*fine+.08*grain
            if name=='T_ForestFloor':
                moss=noise(x,y,9,31)*.5+medium*.5
                base=(56,70,36) if moss>.49 else (75,63,40)
                speck= 38 if fine>.79 else -16 if fine<.24 else 0
                rgb=(base[0]+(blend-.5)*66+speck*.45,
                     base[1]+(blend-.5)*74+speck*.55,
                     base[2]+(blend-.5)*53+speck*.23)
            elif name=='T_ForestPath':
                pebble= 52 if fine>.83 and grain>.60 else 0
                leaf= (medium>.69 and fine<.35)
                rgb=(94+(blend-.5)*83+pebble*.55+(32 if leaf else 0),
                     73+(blend-.5)*66+pebble*.51+(19 if leaf else 0),
                     47+(blend-.5)*48+pebble*.49+(7 if leaf else 0))
            else:
                seam=noise(x,y,15,94)
                dark=-34 if seam<.22 else 0
                rgb=(107+(blend-.5)*93+dark,
                     111+(blend-.5)*92+dark,
                     105+(blend-.5)*87+dark)
            index=(y*SIZE+x)*3
            data[index:index+3]=bytes(channel(c) for c in rgb)
    png(name,data)
    print('GENERATED',name)
