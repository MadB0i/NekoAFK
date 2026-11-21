"""Contact sheet of unretouched Blender renders, scaled uniformly for comparison."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent/'renders';width=1200;rowh=520
im=Image.new('RGB',(width,4*rowh+100),(22,25,33));d=ImageDraw.Draw(im)
try:font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24);small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
except OSError:font=small=ImageFont.load_default()
d.text((34,22),'NEKO / v001 BEFORE',font=font,fill='#c6bdaf');d.text((634,22),'NEKO / v002 AFTER',font=font,fill='#e8bd71')
for row,(name,label) in enumerate([('fullbody','Seated composition'),('face','Face and hair'),('nails','Acrylic nails'),('seated-feet','Seated feet')]):
 y=80+row*rowh
 for col,prefix in enumerate(['before','after']):
  img=Image.open(R/f'{prefix}-{name}.png').convert('RGB');img.thumbnail((570,470),Image.Resampling.LANCZOS);x=col*600+(600-img.width)//2;im.paste(img,(x,y));d.text((col*600+25,y+475),label,font=small,fill='#c6bdaf')
im.save(R/'before-after.png')
print(R/'before-after.png')
