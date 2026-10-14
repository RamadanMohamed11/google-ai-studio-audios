import json,math,os,random,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from faster_whisper import WhisperModel
# PyAV 19 removed 'metadata_errors'; faster-whisper 1.2.x still passes it.
# Keep the newest decoder compatible without suppressing any other arguments.
import av
_av_open = av.open
def _compatible_av_open(*args, **kwargs):
 kwargs.pop('metadata_errors', None)
 return _av_open(*args, **kwargs)
av.open = _compatible_av_open
A=Path('black-box-charon-voiceover.wav')
O=Path('output/charon-short');O.mkdir(parents=True,exist_ok=True)
def run(*args):
 print('RUN',args,flush=True);subprocess.run(list(map(str,args)),check=True)
def dur(p):
 return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(p)],text=True))
D=dur(A)
segments,info=WhisperModel('base',device='cpu',compute_type='int8').transcribe(str(A),language='ar',word_timestamps=True,vad_filter=True,beam_size=5)
words=[{'start':w.start,'end':w.end,'word':w.word.strip()} for s in segments for w in (s.words or []) if w.word.strip()]
if not words:raise RuntimeError('No audio transcript; render aborted')
cut=min(D,59.5)
if D>59.5:
 endings=[w['end'] for w in words if 40<w['end']<59.4 and any(w['word'].endswith(p) for p in ('.','؟','!','،'))]
 if endings:cut=max(endings)+.1
 else:cut=min(59.5,max(w['end'] for w in words if w['end']<=59.5))
cuts=[0.]
while cuts[-1]<cut-.2:
 target=min(cut,cuts[-1]+5)
 candidates=[w['end'] for w in words if cuts[-1]+3.5<=w['end']<=min(cut,cuts[-1]+6)]
 end=min(candidates,key=lambda x:abs(x-target)) if candidates else target
 cuts.append(min(cut,max(end,cuts[-1]+.5)))
if cuts[-1]!=cut:cuts[-1]=cut
beats=[]
for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
 phrase=' '.join(w['word'] for w in words if w['end']>a and w['start']<b)
 beats.append({'start':a,'end':b,'phrase':phrase})
(O/'transcript.txt').write_text(' '.join(w['word'] for w in words),encoding='utf-8')
(O/'word_timings.json').write_text(json.dumps(words,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'storyboard.json').write_text(json.dumps(beats,ensure_ascii=False,indent=2),encoding='utf-8')
font='/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf'
latin='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
print('Audio seconds:',round(D,2),'Transcript words:',len(words),'Scenes:',len(beats),flush=True)
f=ImageFont.truetype(font,37);small=ImageFont.truetype(font,25);en=ImageFont.truetype(latin,16)
def theme(t):
 if any(x in t for x in ('شارون','بلوتو','كوكب','فضا','الشمس','قمر','المجرة')):return 'orbital'
 if any(x in t for x in ('حاسوب','شبكة','بيانات','إنترنت','تكنولوجيا')):return 'network'
 if any(x in t for x in ('سر','صندوق','غامض','الأسود','لغز')):return 'mystery'
 return 'editorial'
scenes=O/'scenes';scenes.mkdir(exist_ok=True)
videos=[]
for i,beat in enumerate(beats):
 im=Image.new('RGB',(720,1280));p=im.load()
 for y in range(1280):
  for x in range(720):
   g=max(0,1-math.hypot((x-400)/750,(y-530)/1600)*1.5)
   p[x,y]=(int(7+9*g),int(16+21*g),int(32+31*g))
 d=ImageDraw.Draw(im)
 rng=random.Random(i+43)
 for j in range(70):
  x,y=rng.randrange(720),rng.randrange(1280);d.ellipse((x,y,x+2,y+2),fill=(23,65,90))
 d.rounded_rectangle((32,35,690,116),radius=19,fill=(14,31,50),outline=(50,92,115),width=2)
 d.text((664,45),'من أولها',font=f,fill='white',anchor='ra',direction='rtl')
 d.text((47,73),'SHORTS / DOCUMENTARY',font=en,fill=(56,222,235))
 mode=theme(beat['phrase']);cx,cy=360,640
 if mode=='orbital':
  for r in (105,155,220,275):
   d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(35,90,125),width=3)
  d.ellipse((cx-120,cy-120,cx+120,cy+120),fill=(21,45,75),outline=(62,230,240),width=6)
  d.ellipse((535,405,577,447),fill=(255,190,85))
 elif mode=='network':
  pts=[(80+j*115,rng.randint(390,820)) for j in range(6)]
  for k in range(5):d.line((pts[k],pts[k+1]),fill=(55,125,166),width=5)
  for x,y in pts:d.ellipse((x-17,y-17,x+17,y+17),fill=(57,221,230))
 elif mode=='mystery':
  for r in (145,183,215,255):d.arc((cx-r,cy-r,cx+r,cy+r),20,320,fill=(45,117,146),width=4)
  d.rounded_rectangle((240,515,480,755),radius=22,fill=(11,25,39),outline=(53,227,238),width=5)
  d.ellipse((330,605,390,665),outline=(254,189,79),width=6)
 else:
  for k in range(7):
   y=430+k*82;d.rounded_rectangle((120,y,605-k*23,y+48),radius=12,outline=(38+k*7,111+k*8,133+k*9),width=3)
 d.rounded_rectangle((35,950,685,1130),radius=22,fill=(11,26,45),outline=(46,91,116),width=2)
 d.text((632,957),'القصة من أولها',font=small,fill=(255,190,85),anchor='ra',direction='rtl')
 line=' '.join(beat['phrase'].split()[:7]) or 'من أولها'
 while len(line)>37 and len(line.split())>2:line=' '.join(line.split()[:-1])
 d.text((634,1014),line,font=f,fill='white',anchor='ra',direction='rtl')
 d.rectangle((36,1171,684,1176),fill=(34,76,96))
 d.rectangle((36,1171,36+int(648*(i+1)/len(beats)),1176),fill=(53,220,232))
 d.text((37,1201),f'MIN AWWALHA / SHOT {i+1:02d}',font=en,fill=(155,178,200))
 jpg=scenes/f'{i:02d}.png';im.save(jpg)
 mp4=scenes/f'{i:02d}.mp4';length=beat['end']-beat['start']
 vf="scale=1080:1920,zoompan=z='min(zoom+0.0001,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p"
 run('ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','30','-i',jpg,'-t',f'{length:.3f}','-vf',vf,'-an','-c:v','libx264','-preset','ultrafast','-crf','23','-pix_fmt','yuv420p',mp4)
 videos.append(mp4)
(O/'clips.txt').write_text(''.join("file '"+str(p.resolve())+"'\n" for p in videos))
def ts(t):return f'{int(t//3600)}:{int(t//60)%60:02d}:{int(t)%60:02d}.{int(t*100)%100:02d}'
ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Arabic,Noto Sans Arabic,57,&H00FFFFFF,&H0000E7F4,&H000E1326,&H96061019,-1,0,0,0,100,100,0,0,1,5,1,2,62,62,135,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
groups=[words[i:i+5] for i in range(0,len(words),5)]
for group in groups:
 if group[0]['start']>=cut:break
 for j,w in enumerate(group):
  if w['start']>=cut:break
  s=' '.join(('{\\c&H0056BEFF&}'+x['word']+'{\\c&H00FFFFFF&}') if k==j else x['word'] for k,x in enumerate(group))
  s=s.replace('{\\c&H0056BEFF&}', '{\\c&H0056BEFF&}')
  ass.append(f"Dialogue: 0,{ts(w['start'])},{ts(min(cut,w['end']))},Arabic,,0,0,0,,{s}")
(O/'captions.ass').write_text('\n'.join(ass),encoding='utf-8-sig')
target=O/'MIN_AWWALHA_SHORT_1080x1920.mp4'
run('ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',O/'clips.txt','-i',A,'-vf',f'ass={O/"captions.ass"}','-map','0:v:0','-map','1:a:0','-t',f'{cut:.3f}','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',target)
actual=dur(target)
if abs(actual-cut)>.7 or target.stat().st_size<50000:raise RuntimeError('Output validation failed')
(O/'report.json').write_text(json.dumps({'status':'success','duration_seconds':actual,'fps':30,'resolution':'1080x1920','source_sha':'9f25bacaa8db42945ff9167022cfa83d3689e5f0','scene_count':len(beats)},ensure_ascii=False,indent=2))
print('RENDER_OK',target)