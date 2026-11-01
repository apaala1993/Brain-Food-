"""Trixie, Purpur, and Gundus: a procedural animated portrait of three cats.
Trixie: blue-eyed Ragdoll. Purpur: green-eyed calico Maine Coon mix.
Gundus: green-eyed fluffy tuxedo. Stylized coats, generated without photos.
Install: python -m pip install numpy pillow matplotlib
Run:     python animated_cat_trio.py
GIF:     python animated_cat_trio.py --save three_cats.gif
Solo:    python animated_cat_trio.py --cat purpur
Still:   python animated_cat_trio.py --still portrait.png
"""
import argparse
import math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

SECONDS=6
BG=(9,14,24)
CREAM=(238,229,216)
WHITE=(255,249,236)
POINT=(101,85,82)
TAU=math.tau


def mix(a,b,t):
    return tuple(round(x*(1-t)+y*t) for x,y in zip(a,b))


class Brush:
    def __init__(self,im,scale=2):
        self.im=im; self.d=ImageDraw.Draw(im); self.s=scale
    def points(self,p):return [(float(x)*self.s,float(y)*self.s) for x,y in p]
    def ellipse(self,box,col):self.d.ellipse(tuple(float(v)*self.s for v in box),fill=col)
    def poly(self,p,col):self.d.polygon(self.points(p),fill=col)
    def line(self,p,col,w=1):
        self.d.line(self.points(p),fill=col,width=max(1,round(w*self.s)),joint='curve')
    def curve(self,p,col,w=1):
        p=np.array(p,float); u=np.linspace(0,1,75)[:,None]
        q=(1-u)**3*p[0]+3*(1-u)**2*u*p[1]+3*(1-u)*u*u*p[2]+u**3*p[3]
        self.line(q,col,w)
        return q
    def shaded(self,box,outer,inner,steps=38):
        x0,y0,x1,y1=box
        for k in range(steps):
            t=k/steps
            # Nested off-center ellipses produce a soft highlight.
            shrink=.45*t
            cx=(x0+x1)/2-5*t; cy=(y0+y1)/2-10*t
            rx=(x1-x0)/2*(1-shrink);ry=(y1-y0)/2*(1-shrink)
            self.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),mix(outer,inner,t))


def blink(t):
    # Two smooth blinks per loop; zero indicates fully open eyes.
    return max(math.exp(-((t-1.4)/.11)**2),math.exp(-((t-4.6)/.14)**2))


def draw_cat(time,width=640,cat="trixie"):
    t=time%SECONDS
    im=Image.new('RGB',(640,720),BG)
    b=Brush(im,1)
    tux=cat=='gundus'
    calico=cat=='purpur'
    coat_outer=(38,40,47) if tux else (159,148,141)
    coat_inner=(68,71,78) if tux else (233,222,205)
    breath=2.2*math.sin(TAU*t/SECONDS)
    # Soft pool of light below the cat.
    for k in range(35):
        r=1-k/50
        b.ellipse((320-180*r,641-17*r,320+180*r,641+17*r),mix(BG,(24,33,44),k/35))
    # Long, feathery tail behind the body; endpoints join smoothly each loop.
    swish=math.sin(TAU*t/SECONDS)
    path=[(413,565),(529,646),(581,514),(520+22*swish,434+20*math.cos(TAU*t/SECONDS))]
    q=b.curve(path,((28,30,36) if tux else (71,61,63)),47)
    b.curve([(x-3,y-3) for x,y in path],((45,48,55) if tux else ((159,103,63) if calico else (117,101,94))),37)
    b.curve([(x-6,y-5) for x,y in path],((60,64,72) if tux else ((189,132,78) if calico else (148,130,117))),23)
    for k in range(3,len(q)-2,2):
        x,y=q[k]; tangent=q[k+1]-q[k-1]
        normal=np.array([-tangent[1],tangent[0]])
        normal/=np.linalg.norm(normal)
        for side in [-1,1]:
            a=np.array([x,y])+side*normal*11
            end=np.array([x,y])+side*normal*(23+2*math.sin(k))-.8*tangent
            b.line([a,end],((70,74,82) if tux else ((180,122,72) if calico else (138,120,108))),1)
    # Haunches and pear-shaped torso.
    b.shaded((190,365+breath,450,631),coat_outer,coat_inner)
    b.shaded((214,350+breath,427,604),((48,50,56) if tux else (189,177,163)),((76,79,85) if tux else CREAM))
    b.shaded((204,489,283,625),((40,42,48) if tux else (185,174,163)),((66,69,76) if tux else (236,224,206)))
    b.shaded((369,483,442,625),((37,39,44) if tux else (176,164,154)),((62,64,70) if tux else (222,209,191)))
    if calico:
        # Irregular ginger and charcoal patches, behind the white chest.
        for box,outer,inner in [((194,392,275,507),(168,95,47),(212,151,82)),
                                 ((375,374,438,495),(45,43,43),(73,67,61)),
                                 ((389,512,442,607),(159,90,45),(209,144,76)),
                                 ((205,551,251,614),(48,44,43),(76,68,60))]:
            b.shaded(box,outer,inner)
    # Chest ruff, drawn with a rippled, fluffy outline.
    p=[]
    for a in np.linspace(0,TAU,190):
        r=1+(.055 if calico else .042)*math.sin(23*a)+.020*math.sin(37*a)
        p.append((320+105*math.cos(a)*r,444+breath+137*math.sin(a)*r))
    b.poly(p,(239,231,215))
    b.shaded((237,349+breath,403,550+breath),(231,222,206),(255,249,233))
    # Fine strands follow the chest's fur direction.
    rng=np.random.default_rng(12)
    for _ in range(100):
        x=rng.uniform(242,398);y=rng.uniform(407,549)+breath
        if ((x-320)/90)**2+((y-468-breath)/100)**2<1:
            b.curve([(x,y),(x-2,y+5),(x+(x-320)*.04,y+10),(x+(x-320)*.08,y+14)],
                    (221,211,193),.6)
    # Forelegs and rounded white mittens, with a tiny alternating knead.
    for side in [-1,1]:
        x=320+side*47
        lift=2.6*math.sin(TAU*t/3+(0 if side<0 else math.pi))
        b.shaded((x-28,501+breath,x+28,622+lift),(214,205,190),WHITE)
        b.shaded((x-35,597+lift,x+34,641+lift),(213,202,186),WHITE)
        for off in [-10,6]:
            b.curve([(x+off,625+lift),(x+off-2,629+lift),(x+off-1,635+lift),(x+off,638+lift)],
                    (202,191,177),1)
    # Build the head on its own transparent layer, then tilt it slightly.
    layer=Image.new('RGBA',(640,720),(0,0,0,0)); h=Brush(layer,1)
    hy=breath
    twitch=3*math.sin(TAU*t/SECONDS)**7
    # Dark ears, pink inner ears, and pale edge tufts.
    for side in [-1,1]:
        ex=320+side*91
        tipx=ex+side*(20+twitch)
        eartip=126 if calico else 151
        earcolor=(34,36,42) if tux else ((172,107,57) if calico and side<0 else (68,61,59))
        h.poly([(ex-side*44,263+hy),(tipx,eartip+hy),(ex+side*48,297+hy)],earcolor)
        h.poly([(ex-side*24,254+hy),(tipx-side*5,176+hy),(ex+side*28,266+hy)],(184,138,139))
        h.poly([(ex-side*12,249+hy),(tipx-side*7,190+hy),(ex+side*19,258+hy)],(211,169,162))
        if calico or tux:
            # Long lynx-like ear tufts are strongest for the Maine Coon mix.
            for j in range(7):
                tx=tipx+(j-3)*1.5
                length=(21 if calico else 9)-abs(j-3)*2
                h.line([(tx,eartip+8+hy),(tx+side*4,eartip-length+hy)],
                       (106,97,84) if calico else (91,93,99),1)
        for k in range(9):
            h.line([(ex+side*(17+k*2),240+hy),(ex+side*(30+k*1.9),221+hy+k*3)],(205,190,172),1)
    h.shaded((178,221+hy,462,422+hy),((39,41,47) if tux else (194,181,164)),((65,68,75) if tux else (244,234,215)))
    # Seal-colored mask around the eyes.
    h.shaded((190,236+hy,323,371+hy),((42,44,51) if tux else ((172,101,49) if calico else (128,108,100))),((68,71,80) if tux else ((222,158,91) if calico else (156,132,117))))
    h.shaded((317,236+hy,450,371+hy),((35,37,43) if tux else ((42,40,41) if calico else (120,100,94))),((57,61,69) if tux else ((78,69,60) if calico else (153,127,113))))
    if calico:
        h.poly([(275,240+hy),(300,227+hy),(318,236+hy),(303,279+hy),(286,290+hy)],(194,129,66))
    # Inverted-V white blaze, characteristic of a bicolor Ragdoll.
    h.poly([(320,259+hy if tux else 236+hy),(310 if tux else 299,288+hy),(292 if tux else 269,333+hy),(251 if tux else 236,368+hy),
            (267,399+hy),(320,418+hy),(374,397+hy),(405,367+hy),
            (348 if tux else 372,333+hy),(330 if tux else 342,289+hy)],(250,242,224))
    h.shaded((225,338+hy,415,423+hy),(225,212,193),(255,249,232))
    # Fur along cheeks.
    for side in [-1,1]:
        for k in range(23 if calico or tux else 17):
            y=307+k*4+hy if calico or tux else 318+k*4+hy
            x=320+side*(130-abs(k-8)*1.1)
            h.line([(x-side*15,y-3),(x+side*(8+3*math.sin(k)),y+8)],((104,105,108) if tux else (224,213,193)),1)
    # Large sapphire eyes. Eyelids squash into relaxed curves during a blink.
    closing=blink(t)
    gaze=2*math.sin(TAU*t/SECONDS)
    for side in [-1,1]:
        x=320+side*65;y=310+hy
        ey=Image.new('RGBA',(640,720),(0,0,0,0)); e=Brush(ey,1)
        openness=max(.025,1-closing)
        upper=[];lower=[]
        for u in np.linspace(0,1,45):
            xx=x-30+60*u
            arch=math.sin(math.pi*u)**.8
            upper.append((xx,y-18*openness*arch))
            lower.append((xx,y+17*openness*arch))
        mask=Image.new('L',ey.size,0)
        ImageDraw.Draw(mask).polygon(e.points(upper+lower[::-1]),fill=255)
        e.ellipse((x-31,y-21,x+31,y+21),((189,220,157) if tux or calico else (176,219,237)))
        e.shaded((x-19+gaze,y-20,x+19+gaze,y+20),((50,111,56) if tux or calico else (41,103,152)),((149,211,103) if tux or calico else (97,189,230)))
        for a in np.linspace(0,TAU,48):
            e.line([(x+gaze+9*math.cos(a),y+10*math.sin(a)),
                    (x+gaze+17*math.cos(a),y+18*math.sin(a))],((83,154,65) if tux or calico else (54,127,173)),.6)
        e.ellipse((x-6+gaze,y-17,x+6+gaze,y+17),(12,28,43))
        e.ellipse((x-10+gaze,y-12,x-2+gaze,y-4),(255,255,250))
        e.ellipse((x+7+gaze,y+7,x+10+gaze,y+10),(216,244,255))
        layer.paste(ey,(0,0),mask)
        h=Brush(layer,1)
        h.line(upper,(59,53,57),2)
        h.line(lower,(115,91,88),1)
        # Small eyebrow fur marks.
        for j in range(3):
            h.line([(x-13+j*9,y-35),(x-9+j*9,y-39)],(195,174,150),1)
    # Muzzle, rosy nose and mouth.
    h.shaded((265,345+hy,322,386+hy),(235,224,205),(255,249,232))
    h.shaded((318,345+hy,375,386+hy),(235,224,205),(255,249,232))
    h.poly([(308,352+hy),(332,352+hy),(320,364+hy)],(192,128,132))
    h.line([(313,354+hy),(327,354+hy)],(231,165,165),1)
    h.line([(320,364+hy),(320,375+hy)],(115,91,86),1)
    h.curve([(320,375+hy),(315,383+hy),(307,383+hy),(302,378+hy)],(115,91,86),1)
    h.curve([(320,375+hy),(325,383+hy),(333,383+hy),(338,378+hy)],(115,91,86),1)
    for side in [-1,1]:
        for j in range(3):
            x=320+side*(27+j*6);y=362+j*5+hy
            h.ellipse((x-1,y-1,x+1,y+1),(159,141,127))
        for j in range(4):
            y=363+j*8+hy
            h.curve([(320+side*37,y),(320+side*76,y-8+j*2),
                     (320+side*126,y-12+j*3),(320+side*160,y-15+j*5)],(211,215,212),1)
    tilt=1.6*math.sin(TAU*t/SECONDS)
    layer=layer.rotate(tilt,resample=Image.Resampling.BICUBIC,center=(320,345))
    im.paste(layer,(0,0),layer)
    return im.resize((width,round(width*720/640)),Image.Resampling.LANCZOS)



NAMES={'trixie':('Trixie','Ragdoll', (150,196,235)),
       'purpur':('Purpur','Calico Maine Coon mix',(233,181,120)),
       'gundus':('Gundus','Fluffy tuxedo',(151,212,145))}


def get_font(size,bold=False):
    from PIL import ImageFont
    for name in [('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
                 ('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'),
                 ('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf')]:
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default()


def render(time,width=1440,selection='all'):
    choices=list(NAMES) if selection=='all' else [selection]
    panels=[]
    for cat in choices:
        index=list(NAMES).index(cat)
        # Offset the animations so they blink and move independently.
        cat_image=draw_cat(time+[0,1.9,3.7][index],640,cat)
        panel=Image.new('RGB',(640,815),BG)
        panel.paste(cat_image,(0,0))
        d=ImageDraw.Draw(panel)
        name,breed,color=NAMES[cat]
        for text,y,size,bold,col in [(name,716,37,True,color),(breed,768,21,False,(168,177,190))]:
            f=get_font(size,bold)
            box=d.textbbox((0,0),text,font=f)
            d.text(((640-(box[2]-box[0]))/2,y),text,font=f,fill=col)
        panels.append(panel)
    canvas=Image.new('RGB',(640*len(panels),815),BG)
    for i,panel in enumerate(panels):canvas.paste(panel,(i*640,0))
    return canvas.resize((width,round(width*815/(640*len(panels)))),Image.Resampling.LANCZOS)


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cat',choices=('all','trixie','purpur','gundus'),default='all')
    out=parser.add_mutually_exclusive_group()
    out.add_argument('--save',type=Path)
    out.add_argument('--still',type=Path)
    parser.add_argument('--width',type=int,default=1440)
    parser.add_argument('--fps',type=int,default=18)
    args=parser.parse_args()
    if args.width<200 or args.fps<1:parser.error('width must be >= 200 and fps >= 1')
    if args.still:
        render(.25,args.width,args.cat).save(args.still)
        print(f'Saved {args.still}')
    elif args.save:
        if args.save.suffix.lower()!='.gif':parser.error('--save requires a .gif filename')
        frames=[]
        for i in range(SECONDS*args.fps):
            frames.append(render(i/args.fps,args.width,args.cat))
            if i%args.fps==0:print(f'Rendering {i/args.fps:g}/{SECONDS} sec',flush=True)
        frames[0].save(args.save,save_all=True,append_images=frames[1:],
                       duration=round(1000/args.fps),loop=0,disposal=2)
        print(f'Saved {args.save}')
    else:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
        im=render(0,args.width,args.cat)
        fig,ax=plt.subplots(figsize=(13,5.6) if args.cat=='all' else (5.5,7),facecolor=np.array(BG)/255)
        fig.subplots_adjust(0,0,1,1);ax.axis('off')
        artist=ax.imshow(im)
        def update(i):
            artist.set_data(render(i/args.fps,args.width,args.cat))
            return (artist,)
        animation=FuncAnimation(fig,update,frames=SECONDS*args.fps,
                                interval=1000/args.fps,blit=True,cache_frame_data=False)
        plt.show()

if __name__=='__main__':main()
