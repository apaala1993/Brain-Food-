import argparse
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TAU = 2 * math.pi
BACKGROUND = (3, 6, 10)
KINDS = ('tulip', 'rose', 'lily', 'daisy', 'sunflower')


def ease(x):
    x = max(0.0, min(1.0, float(x)))
    return x*x*(3-2*x)


def blend(a, b, t):
    return tuple(int(x*(1-t)+y*t) for x,y in zip(a,b))


class Brush:
    """Draw in a fixed design coordinate system, with antialiasing."""
    def __init__(self, image, design_size):
        self.image = image
        self.d = ImageDraw.Draw(image)
        self.scale = image.width / design_size

    def pts(self, points):
        s = self.scale
        return [(float(x)*s, float(y)*s) for x,y in points]

    def polygon(self, points, color):
        self.d.polygon(self.pts(points), fill=color)

    def line(self, points, color, width=1):
        self.d.line(self.pts(points), fill=color,
                    width=max(1, round(width*self.scale)), joint='curve')

    def ellipse(self, box, color):
        self.d.ellipse(tuple(float(v)*self.scale for v in box), fill=color)

    def dot(self, x,y,r,color):
        self.ellipse((x-r,y-r,x+r,y+r),color)


def petal(b, center, angle, length, width, base, tip,
          curl=0, pointiness=.7, speckles=False, seed=1):
    """A curved parametric petal with a shaded pink/gold center."""
    cx,cy = center
    ca,sa = math.cos(angle),math.sin(angle)
    def xy(u,v):
        radius = length*u
        half = width*max(0,math.sin(math.pi*u))**pointiness
        side = half*v + curl*math.sin(math.pi*u)
        return cx+radius*ca-side*sa, cy+radius*sa+side*ca
    for j in range(26):
        u0,u1 = j/26,(j+1)/26
        for k in range(8):
            v0,v1 = -1+k/4,-1+(k+1)/4
            u,v = (u0+u1)/2,(v0+v1)/2
            tint = ease(u*.95+abs(v)*.4)
            color = blend(base,tip,tint)
            shade = .91+.09*math.cos(v*math.pi/2)
            color = tuple(round(c*shade) for c in color)
            b.polygon([xy(u0,v0),xy(u1,v0),xy(u1,v1),xy(u0,v1)],color)
    if speckles:
        rng = np.random.default_rng(seed)
        for _ in range(47):
            u,v = rng.uniform(.16,.68),rng.uniform(-.75,.75)
            x,y = xy(u,v)
            b.dot(x,y,rng.uniform(.55,1.15),(125,28,72))
    b.line([xy(u,0) for u in np.linspace(.12,.90,24)],blend(base,tip,.65),.65)


@lru_cache(maxsize=300)
def flower_sprite(kind, step):
    """Cache bloom stages so repeated screen frames render quickly."""
    opening = step/48
    image = Image.new('RGBA',(480,480),(0,0,0,0))
    b = Brush(image,320)
    cx,cy = 160,160
    if kind == 'lily':
        for k in [0,2,4,1,3,5]:
            a = -1.72+k*TAU/6
            petal(b,(cx,cy),a,122*(.38+.62*opening),
                  41*(.12+.88*opening),(213,91,146),(255,250,231),
                  curl=7*math.sin(k),speckles=True,seed=100+k)
        b.dot(cx,cy,5,(136,157,54))
        for k in range(6):
            a=-1.8+k*TAU/6
            u=np.linspace(0,1,25)
            xx=cx+math.cos(a)*53*opening*u+5*np.sin(math.pi*u)
            yy=cy+math.sin(a)*53*opening*u-8*u
            b.line(zip(xx,yy),(231,231,157),1.8)
            b.line([(xx[-1]-3,yy[-1]-2),(xx[-1]+3,yy[-1]+2)],(165,91,44),3.5)
    elif kind in ('daisy','sunflower'):
        count = 19 if kind=='daisy' else 23
        for layer in range(2):
            for k in range(count):
                a = k*TAU/count+layer*.12
                sunflower=kind=='sunflower'
                base=(231,148,27) if sunflower else (204,205,191)
                tip=(255,213,62) if sunflower else (255,253,241)
                petal(b,(cx,cy),a,(111-layer*10)*(.34+.66*opening),
                      (13 if sunflower else 10)*(.15+.85*opening),
                      base,tip,curl=2*math.sin(k),pointiness=.65)
        radius=(43 if kind=='sunflower' else 26)*(.55+.45*opening)
        b.dot(cx,cy,radius,(70,44,28) if kind=='sunflower' else (198,123,26))
        # A phyllotactic seed arrangement, using the golden angle.
        count=320 if kind=='sunflower' else 130
        for k in range(count):
            r=radius*.96*math.sqrt((k+.5)/count)
            a=k*math.pi*(3-math.sqrt(5))
            color=blend((94,54,29),(211,157,61),.5+.4*math.sin(k*1.7))
            if kind=='daisy': color=blend((220,142,28),(255,221,88),(k%7)/7)
            b.dot(cx+r*math.cos(a),cy+r*math.sin(a),1.3,color)
    elif kind == 'tulip':
        # Overlapping upright cup petals, opening outward at their tips.
        for index in [0,1,2,3,4]:
            offset=[0,-.7,.7,-.34,.34][index]
            angle=-math.pi/2+offset*(.2+.8*opening)
            petal(b,(cx,230),angle,142,
                  (38 if index<3 else 37)*(.58+.42*opening),
                  (173,43,98) if index<3 else (214,71,122),
                  (255,158,173),curl=offset*18*opening,pointiness=.29)
        b.line([(cx-9,235),(cx,217),(cx+10,235)],(53,118,65),2)
    elif kind == 'rose':
        # Overlapping cupped petals arranged in concentric whorls.
        for ring,count in [(0,7),(1,6),(2,5),(3,4),(4,3)]:
            radius=(101-ring*18)*(.37+.63*opening)
            for k in range(count):
                a=k*TAU/count+ring*.68
                span=TAU/count*.95
                # Oval lobes extend from the center to a scalloped outer edge.
                pts=[]
                for u in np.linspace(0,1,40):
                    theta=a-span+2*span*u
                    r=radius*(.53+.47*math.sin(math.pi*u)**.55)
                    pts.append((cx+r*math.cos(theta),cy+r*math.sin(theta)*.9))
                pts.extend([(cx+radius*.16*math.cos(a+.5),cy+radius*.16*math.sin(a+.5))])
                color=blend((139,27,69),(243,120,150),.30+ring*.12+(k%3)*.06)
                b.polygon(pts,color)
                # Thin highlights define each folded rim.
                rim=[]
                for u in np.linspace(.05,.95,32):
                    theta=a-span+2*span*u
                    r=radius*(.53+.47*math.sin(math.pi*u)**.55)
                    rim.append((cx+r*math.cos(theta),cy+r*math.sin(theta)*.9))
                b.line(rim,blend(color,(255,188,185),.42),1.2)
        spiral=[]
        for a in np.linspace(0,TAU*1.6,90):
            r=1.0+a*1.25*(.5+.5*opening)
            spiral.append((cx+r*math.cos(a),cy+r*math.sin(a)*.8))
        b.line(spiral,(255,163,168),1.6)
    return image


def layout(selection):
    # x, y: flower attachment; size: sprite width; delay: bloom start.
    if selection != 'bouquet':
        return [(selection,350,330,470,0)]
    return [('rose',238,245,250,0),
            ('tulip',439,258,252,.45),
            ('sunflower',468,410,265,1.05),
            ('lily',250,432,300,1.55),
            ('daisy',365,551,240,2.1)]


def render(time, width=700, selection='bouquet'):
    height=round(width*9/7)
    image=Image.new('RGB',(width*2,height*2),BACKGROUND)
    b=Brush(image,700)
    flowers=layout(selection)
    base=(350,821)
    def sway(y,phase=0):
        return 5*math.sin(time*.8+phase)*(821-y)/600
    for i,(kind,x,y,size,delay) in enumerate(flowers):
        # Tulips attach at the base of their cup, below sprite center.
        end_y=y+(70/320*size if kind=='tulip' else 0)
        u=np.linspace(0,1,70)
        xx=base[0]+(x-base[0])*u+sway(y,i*.3)*u*u
        yy=base[1]+(end_y-base[1])*u
        b.line(zip(xx,yy),(17,62,37),8)
        b.line(zip(xx-1,yy),(45,112,62),4)
        b.line(zip(xx-2,yy),(92,147,78),1)
    # Lanceolate leaves with a central vein and diagonal secondary veins.
    for i,(x,y,dx,dy,w) in enumerate([(346,740,-155,-66,22),(355,701,143,-73,27),
                                      (319,622,-135,-37,21),(386,600,127,-34,24),
                                      (350,782,108,-33,17)]):
        u=np.linspace(0,1,50)
        xx=x+dx*u+sway(y)*u
        yy=y+dy*u-21*np.sin(math.pi*u)
        ww=w*np.sin(math.pi*u)**.9
        b.polygon(list(zip(xx,yy-ww))+list(zip(xx[::-1],(yy+ww)[::-1])),(24,82,45))
        b.polygon(list(zip(xx,yy))+list(zip(xx[::-1],(yy+ww)[::-1])),(18,65,37))
        b.line(zip(xx,yy),(96,146,78),1.2)
        for k in [12,20,28,36,43]:
            b.line([(xx[k-6],yy[k-6]),(xx[k],yy[k]-ww[k]*.85)],(48,109,59),.7)
            b.line([(xx[k-6],yy[k-6]),(xx[k],yy[k]+ww[k]*.85)],(42,99,53),.7)
    for i,(kind,x,y,size,delay) in enumerate(flowers):
        bloom=ease((time-delay)/3)
        stage=round(48*bloom)
        sprite=flower_sprite(kind,stage)
        target=max(1,round(size*b.scale))
        sprite=sprite.resize((target,target),Image.Resampling.LANCZOS)
        # Flower and stem tips move together.
        px=round((x+sway(y,i*.3))*b.scale-target/2)
        py=round(y*b.scale-target/2)
        image.paste(sprite,(px,py),sprite)
    # A few floating pollen grains; positions are deterministic.
    rng=np.random.default_rng(27)
    for x,y,phase in rng.uniform([150,190,0],[550,770,TAU],(16,3)):
        yy=190+(y-190-time*6)%580
        b.dot(x+5*math.sin(time*.6+phase),yy,.8,(133,116,77))
    return image.resize((width,height),Image.Resampling.LANCZOS)


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--flower',choices=('bouquet',)+KINDS,default='bouquet')
    output=p.add_mutually_exclusive_group()
    output.add_argument('--save',type=Path,help='Export an animated .gif')
    output.add_argument('--still',type=Path,help='Export an open-flower .png')
    p.add_argument('--width',type=int,default=700)
    p.add_argument('--fps',type=int,default=18)
    p.add_argument('--seconds',type=float,default=8)
    args=p.parse_args()
    if args.width<150 or args.fps<1 or args.seconds<=0:
        p.error('Use width >= 150, fps >= 1, and seconds > 0.')
    if args.still:
        render(6.5,args.width,args.flower).save(args.still)
        print(f'Saved {args.still}')
        return
    count=max(2,round(args.fps*args.seconds))
    if args.save:
        if args.save.suffix.lower()!='.gif':
            p.error('--save expects a .gif file name.')
        frames=[]
        for i in range(count):
            frames.append(render(i/args.fps,args.width,args.flower))
            if i%args.fps==0:
                print(f'Rendering {i/args.fps:.0f} / {args.seconds:g} seconds',flush=True)
        frames[0].save(args.save,save_all=True,append_images=frames[1:],
                       duration=round(1000/args.fps),loop=0,optimize=False,disposal=2)
        print(f'Saved {args.save}')
    else:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
        fig,ax=plt.subplots(figsize=(7,9),facecolor=np.array(BACKGROUND)/255)
        fig.subplots_adjust(0,0,1,1)
        ax.axis('off')
        artist=ax.imshow(render(0,args.width,args.flower))
        def update(i):
            artist.set_data(render(i/args.fps,args.width,args.flower))
            return (artist,)
        animation=FuncAnimation(fig,update,frames=count,interval=1000/args.fps,
                                repeat=True,blit=True,cache_frame_data=False)
        plt.show()


if __name__=='__main__':
    main()
