#!/usr/bin/env python3
"""Generate original UI accents and locally tint observed APK sprite sheets."""
from pathlib import Path
import hashlib
import json
import math
import os
import io
import zipfile
try:
    from PIL import Image, ImageDraw, ImageOps, ImageChops
except ImportError:
    raise SystemExit("Texture generation needs Pillow. On Mint run: sudo apt install python3-pil")

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'generated' / 'overlay'
SPECS = [
 ('ExtraContent/textures/ui/LuaApp/9-slice/gr-loading-indicator.png',4,4,'fill'),
 ('ExtraContent/textures/ui/LuaApp/9-slice/gr-loading-indicator@2x.png',8,8,'fill'),
 ('ExtraContent/textures/ui/LuaApp/9-slice/gr-loading-indicator@3x.png',12,12,'fill'),
 ('ExtraContent/textures/ui/LuaApp/graphic/Auth/FPSBackground.png',1024,1024,'auth'),
 ('ExtraContent/textures/ui/LuaApp/graphic/Auth/GridBackground_05202026.jpg',1920,1920,'auth'),
 ('content/textures/ui/Emotes/TenFoot/CircleBackground.png',640,640,'circle'),
 ('content/textures/ui/Emotes/TenFoot/CircleBackground@2x.png',1280,1280,'circle'),
 ('content/textures/ui/Emotes/TenFoot/CircleBackground@3x.png',1920,1920,'circle'),
 ('content/textures/ui/Emotes/TenFoot/SelectedGradient.png',292,225,'selection'),
 ('content/textures/ui/InGameMenu/BackgroundGlow.png',256,256,'glow'),
 ('content/textures/ui/InGameMenu/BackgroundGlow@2x.png',512,512,'glow'),
 ('content/textures/ui/LoadingScreen/LoadingSpinner.png',100,100,'spinner'),
]


ATLASES = [
    f'ExtraContent/LuaPackages/Packages/_Index/FoundationImages/FoundationImages/SpriteSheets/img_set_1x_{n}.png'
    for n in range(1, 6)
] + ['ExtraContent/textures/ui/ImageSet/LuaApp/img_set_1x_2.png']


def source_apk():
    explicit = os.environ.get('LILAC_THEME_APK')
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise SystemExit('LILAC_THEME_APK must name your Roblox base.apk.')
        return p
    state = Path(os.environ.get('LILAC_RUNTIME_STATE', str(Path.home()/'.local/share/lilac-runtime-dev')))
    store = state/'data/cordial/builds'
    candidates = sorted(store.rglob('base.apk')) if store.exists() else []
    if len(candidates) != 1:
        raise SystemExit('Could not select one Roblox base.apk from the runtime store. Run with LILAC_THEME_APK="/absolute/path/to/base.apk" before the launch command.')
    return candidates[0].resolve()


def tint_atlas(image):
    image = image.convert('RGBA')
    r,g,b,alpha = image.split()
    maximum = ImageChops.lighter(ImageChops.lighter(r,g),b)
    minimum = ImageChops.darker(ImageChops.darker(r,g),b)
    neutral = ImageChops.subtract(maximum,minimum).point(lambda v:255 if v<=12 else 0)
    lilac = ImageOps.colorize(ImageOps.grayscale(image), black='#000000', white='#d7b3ff')
    result = Image.composite(lilac,image.convert('RGB'),neutral).convert('RGBA')
    result.putalpha(alpha)
    return result


def texture(w,h,kind):
    if kind == 'fill':
        return Image.new('RGBA',(w,h),'#c5a3ef')
    # All geometry and colours below are original; no APK artwork is read.
    radial = ImageOps.invert(Image.radial_gradient('L')).resize((w,h))
    if kind == 'auth':
        im=Image.composite(Image.new('RGB',(w,h),'#684384'),Image.new('RGB',(w,h),'#171020'),radial)
        draw=ImageDraw.Draw(im)
        step=max(24,w//32)
        for y in range(step//2,h,step):
            for x in range(step//2,w,step):
                draw.ellipse((x-1,y-1,x+1,y+1),fill='#9671b6')
        return im
    if kind == 'spinner':
        scale=4;im=Image.new('RGBA',(w*scale,h*scale));draw=ImageDraw.Draw(im)
        for n in range(12):
            angle=2*math.pi*n/12
            x=w*scale/2+math.cos(angle)*w*scale*.34
            y=h*scale/2+math.sin(angle)*h*scale*.34
            r=w*scale*.035
            draw.ellipse((x-r,y-r,x+r,y+r),fill=(204,171,246,40+int(n*215/11)))
        return im.resize((w,h),Image.Resampling.LANCZOS)
    if kind == 'circle':
        # Transparent outside the radial menu, with a softly lit lilac centre.
        alpha=radial.point(lambda x: min(230,max(0,(x-38)*2)))
        im=Image.composite(Image.new('RGBA',(w,h),'#a37ac9'),Image.new('RGBA',(w,h),'#30203f'),radial)
        im.putalpha(alpha);return im
    im=Image.new('RGBA',(w,h),(187,145,235,0))
    im.putalpha(radial.point(lambda x:int((x/255)**2*(160 if kind=='glow' else 210))))
    return im


def generate():
    apk = source_apk()
    # Read-only, named UI atlas entries. Never extract code or rewrite the APK.
    atlases = []
    with zipfile.ZipFile(apk) as archive:
        for name in ATLASES:
            try:
                info = archive.getinfo('assets/'+name)
            except KeyError:
                raise SystemExit('This APK lacks an observed UI atlas: '+name)
            if info.file_size > 16*1024*1024:
                raise SystemExit('Unexpectedly large UI atlas; generation stopped.')
            original = Image.open(io.BytesIO(archive.read(info))).convert('RGBA')
            if original.size != (512,512):
                raise SystemExit('Atlas layout differs from the tested build: '+name)
            atlases.append((name,tint_atlas(original)))
    manifest=[]
    for name,w,h,kind in SPECS:
        p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
        im=texture(w,h,kind)
        if p.suffix=='.jpg':im.convert('RGB').save(p,quality=90,optimize=True)
        else:
            # RGBA keeps subtle alpha gradients smooth; palette quantisation
            # creates visible rings in the menu glows.
            im.save(p,optimize=True)
        manifest.append({'path':name,'size':[w,h],'kind':kind,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    for name,im in atlases:
        p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        manifest.append({'path':name,'size':list(im.size),'kind':'ui-atlas','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    stat=apk.stat()
    (OUT.parent/'manifest.json').write_text(json.dumps({'version':2,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_apk':str(apk),'source_apk_bytes':stat.st_size,'source_apk_mtime_ns':stat.st_mtime_ns,'textures':manifest},indent=2)+'\n')
    print(f'Generated {len(SPECS)} original accents and {len(atlases)} locally tinted UI atlases.')


if __name__=='__main__':generate()
