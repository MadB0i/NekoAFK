from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent
im=Image.new('RGB',(1440,1792),(24,27,35));d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',20)
for i in range(16):
 frame=i*12;p=R/'runtime-frames'/f'frame-{frame:04d}.png';a=Image.open(p).convert('RGB');a.resize((360,432),Image.Resampling.LANCZOS)
 x=i%4*360;y=i//4*448;im.paste(a.resize((360,432),Image.Resampling.LANCZOS),(x,y));d.text((x+12,y+8),f'{frame/24:.1f}s',font=font,fill='#ffe4b1')
im.save(R/'audit/motion-contact-sheet.jpg',quality=92)
print(R/'audit/motion-contact-sheet.jpg')
