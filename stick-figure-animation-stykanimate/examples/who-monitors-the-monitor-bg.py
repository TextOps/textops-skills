from PIL import Image, ImageDraw, ImageFont
W,H,FLOOR=1080,1350,1150
F='/usr/share/fonts/opentype/inter/InterDisplay-'
BG=(250,248,242); INK=(17,17,17); RED=(226,35,38)
def base(tagline):
    img=Image.new('RGBA',(W,H),BG+(255,)); d=ImageDraw.Draw(img)
    reg=ImageFont.truetype(F+'Medium.otf',104); bold=ImageFont.truetype(F+'Black.otf',104)
    x,y=72,170
    d.text((x,y),'Who monitors',font=reg,fill=INK)
    y2=y+122; d.text((x,y2),'the ',font=reg,fill=INK); w=d.textlength('the ',font=reg)
    d.text((x+w,y2),'monitor',font=bold,fill=INK); w2=d.textlength('monitor',font=bold)
    d.text((x+w+w2,y2),'?',font=bold,fill=RED)
    # wall bracket for the camera (pivot at 950,430)
    d.rounded_rectangle((1000,370,1024,500),6,fill=INK)
    d.line((1004,435,950,430),fill=INK,width=22)
    # cable from the camera down into the glass box
    pts=[]
    import math
    for i in range(41):
        t=i/40; x=(1-t)**3*958+3*(1-t)**2*t*1010+3*(1-t)*t*t*830+t**3*890; y=(1-t)**3*445+3*(1-t)**2*t*560+3*(1-t)*t*t*560+t**3*700
        pts.append((x,y))
    d.line(pts,fill=INK,width=8,joint='curve')
    # outlet + plug
    d.rounded_rectangle((850,700,930,780),10,fill=(236,233,226),outline=(170,166,158),width=3)
    d.rounded_rectangle((866,716,914,764),8,fill=(225,221,212))
    d.rounded_rectangle((872,722,908,758),7,fill=INK)       # plug body
    d.line((890,700,890,722),fill=INK,width=8)
    # floor shadow
    d.ellipse((200,FLOOR-6,980,FLOOR+10),fill=(222,219,212))
    # glass box (translucent) with padlock
    glass=Image.new('RGBA',(W,H),(0,0,0,0)); g=ImageDraw.Draw(glass)
    g.rounded_rectangle((820,650,960,800),8,fill=(160,200,230,70),outline=(110,150,185,220),width=4)
    g.line((838,668,866,668),fill=(255,255,255,200),width=5); g.line((838,668,838,700),fill=(255,255,255,200),width=5)
    g.line((930,760,946,744),fill=(255,255,255,160),width=4)
    img=Image.alpha_composite(img,glass); d=ImageDraw.Draw(img)
    d.arc((872,788,908,830),180,360,fill=INK,width=8)       # shackle
    d.rounded_rectangle((864,806,916,850),7,fill=RED)
    d.ellipse((885,818,895,828),fill=INK); d.line((890,826,890,838),fill=INK,width=4)
    if tagline:
        b=ImageFont.truetype(F+'Black.otf',78); m=ImageFont.truetype(F+'Medium.otf',38)
        t='Not the guard'; tw=d.textlength(t+'.',font=b); x=(W-tw)/2
        d.text((x,1182),t,font=b,fill=INK); d.text((x+d.textlength(t,font=b),1182),'.',font=b,fill=RED)
        s='Keep the monitor out of the agent’s reach.'; d.text(((W-d.textlength(s,font=m))/2,1280),s,font=m,fill=(90,90,90))
    return img.convert('RGB')
base(False).save('mon_bg1.png'); base(True).save('mon_bg2.png')
