import subprocess, numpy as np, json
SR=44100
cuts={"bit":[5.24,12.86,23.79,31.87,35.51,40.36,46.98,53.88,61.3],
      "narrator":[7.5,11.26,17.67],
      "vague":[9.51,14.19,17.34,23.07]}
def load(f,filt=None):
    cmd=["ffmpeg","-v","error","-i",f+".mp3"]+(["-af",filt] if filt else [])+["-f","s16le","-ac","1","-ar",str(SR),"-"]
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.int16).astype(np.float32)/32768
out={}
for f,c in cuts.items():
    x=load(f)
    b=[0]+c+[len(x)/SR]
    segs=[]
    for i in range(len(b)-1):
        s=x[int(b[i]*SR):int(b[i+1]*SR)]
        # trim silence
        a=np.abs(s); idx=np.where(a>0.01)[0]
        if len(idx): s=s[max(0,idx[0]-int(0.05*SR)):min(len(s),idx[-1]+int(0.12*SR))]
        segs.append(s)
    out[f]=segs
# vague one: pitch down + echo
import wave
def wr(name,s):
    with wave.open(name,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(s,-1,1)*32767).astype(np.int16).tobytes())
for k,segs in out.items():
    for i,s in enumerate(segs):
        wr(f"seg_{k}{i+1}.wav",s)
        if k=="vague":
            subprocess.run(["ffmpeg","-y","-v","error","-i",f"seg_{k}{i+1}.wav","-af","asetrate=44100*0.9,aresample=44100,atempo=1.08,aecho=0.8:0.6:90|180:0.35|0.2,volume=1.1",f"segfx_{k}{i+1}.wav"])
print({k:[round(len(s)/SR,2) for s in v] for k,v in out.items()})
