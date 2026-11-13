"""Independent integer FIR oracle + pin-level I2S tests. Python stdlib only.

Run from any directory with Python 3, Icarus Verilog, and vvp on PATH, or set
IVERILOG / VVP to their executable paths. The coefficients come from the
candidate RTL, not yet from a bit-exact comparison with the official bitstream.
"""
import csv, hashlib, json, math, os, pathlib, random, re, subprocess

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parent / 'rtl' / 'fir_audio_top_t1.v'
ADAPTER = HERE / 'phase4_dut_adapter.sv'
OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)
coeffs = [int(v) for _, v in sorted(
    ((int(i), v) for i,v in re.findall(r'COEF\[(\d+)\]\s*=\s*(-?\d+)', SOURCE.read_text())),
    key=lambda item:item[0])]
assert len(coeffs)==63
MAGIC = [0x5a3c, 0xc3a5-65536, 0x96e1-65536]

def signed(x):
    return (x+32768)%65536-32768

BYPASS_FRAMES = 128
COOLDOWN_FRAMES = 1024

def expected(samples):
    hist=[0]*63; y=[]; active=False; state=0; activations=[]; states=[]
    bypass_remaining=0; cooldown_remaining=0
    for i,x in enumerate(samples):
        bypass_this_sample=False
        if active:
            if bypass_remaining <= 1:
                active=False
                bypass_remaining=0
                cooldown_remaining=COOLDOWN_FRAMES
                state=0
            else:
                bypass_this_sample=True
                bypass_remaining-=1
        elif cooldown_remaining:
            cooldown_remaining-=1
            state=0
        else:
            # Independent suffix/prefix recognizer for the literal sequence.
            if i>=2 and samples[i-2:i+1]==MAGIC:
                active=True; state=3; bypass_remaining=BYPASS_FRAMES
                bypass_this_sample=True; activations.append(i)
            elif i>=1 and samples[i-1:i+1]==MAGIC[:2]: state=2
            elif x==MAGIC[0]: state=1
            else: state=0
        hist=[x]+hist[:-1]
        val=max(-32768,min(32767,(sum(a*b for a,b in zip(hist,coeffs))+16384)//32768))
        # Only the trigger-completing sample and the next 127 samples bypass.
        y.append(x if bypass_this_sample else signed(val))
        states.append((int(active),state))
    return y,states,activations
def tone(f, n=2048, amplitude=12000):
    return [round(amplitude*math.sin(2*math.pi*f*i)) for i in range(n)]

rng=random.Random(20261112)
normal=[0]*96+[16384]+[0]*96+[-16384]+[0]*96
normal += [12000]*128+[-12000]*128+[32767]*128+[-32768]*128
normal += [32767,-32768]*128
normal += [rng.randint(-32768,32767) for _ in range(8192)]
# Drive every individual 16-bit sample value; no magic triplet in this ordering.
normal += list(range(-32768,32768))
# Coefficient-sign-aligned windows exercise both saturation limits.
normal += [0]*64+[32767 if c>=0 else -32768 for c in reversed(coeffs)]+[0]*80
normal += [-32768 if c>=0 else 32767 for c in reversed(coeffs)]+[0]*80
near=[0]*80
for bit in range(48):
    seq=MAGIC[:]; word=bit//16; seq[word]=signed((seq[word]&65535)^(1<<(bit%16)))
    near += seq+[0]*4
near += [MAGIC[0],0,MAGIC[1],MAGIC[2],0]+MAGIC[::-1]+[0]*5
near += [MAGIC[0],MAGIC[1],0,MAGIC[2]]+[0]*80
selftest_rng = random.Random(2026)
selftest = [v for _ in range(8) for v in [-32768, 32767, 0, -1, 1, 0x5555, -0x5556]]
selftest += [selftest_rng.randint(-32768, 32767) for _ in range(4000)]
cases={
  'normal':(normal,None),
  'near_misses':(near,None),
  'flush_plus_official_selftest':([0]*1024+selftest,None),
  'right_only_trigger':([0]*80+tone(.1,1024),([0]*80+MAGIC*342)[:1104]),
  'trigger':([0]*80+MAGIC+tone(.3,512)+[0]*256,None),
  'overlap_trigger':([0]*80+[MAGIC[0],MAGIC[0],MAGIC[1],MAGIC[0]]+MAGIC+[0]*128,None),
  'interrupted_then_trigger':([0]*80+[MAGIC[0],MAGIC[1],0,MAGIC[2]]+[0]*16+MAGIC+[0]*128,None),
  'retrigger_during_cooldown':([0]*80+MAGIC+[0]*512+MAGIC+tone(.3,512)+[0]*128,None),
  'retrigger_after_cooldown':([0]*80+MAGIC+[0]*1152+MAGIC+tone(.3,512)+[0]*128,None),
}for freq in [.01,.05,.1,.15,.18,.2,.2125,.23,.25,.3,.4,.49]:
    cases[f'tone_{freq}']=(tone(freq),None)
cases['triggered_stopband']=([0]*80+MAGIC+tone(.3)+[0]*128,None)
cases['music_like']=([round(3500*math.sin(2*math.pi*.013*i)+2500*math.sin(2*math.pi*.047*i)+1800*math.sin(2*math.pi*.11*i)) for i in range(4096)],None)

iverilog=os.environ.get('IVERILOG','iverilog'); vvp=os.environ.get('VVP','vvp')
cmd=[iverilog]
if os.environ.get('IVERILOG_BASE'): cmd+=['-B',os.environ['IVERILOG_BASE']]
cmd+=['-g2012','-Wall','-s','tb_i2s','-o',str(OUT/'sim.vvp'),str(SOURCE),str(ADAPTER),str(HERE/'tb_i2s.sv')]
compile_result=subprocess.run(cmd,text=True,capture_output=True)
(OUT/'compile.log').write_text(compile_result.stdout+compile_result.stderr)
compile_result.check_returncode()
results=[]
for name,(data,right) in cases.items():
    samples=data+[0]*4
    right=(right if right is not None else [rng.randint(-32768,32767) for _ in data])+[0]*4
    y,states,activations=expected(samples)
    vec=OUT/f'{name}.txt'
    with vec.open('w') as fh:
        fh.write(str(len(samples))+'\n')
        for i,(x,r) in enumerate(zip(samples,right)):
            ey=y[i-2] if i>=2 else 0; ee=samples[i-2] if i>=2 else 0
            fh.write(f'{x&65535:04x} {r&65535:04x} {ey&65535:04x} {ee&65535:04x} {states[i][0]} {states[i][1]}\n')
    # Nominal maximum BCLK; slower and asynchronous BCLK are exercised separately.
    timings=[(500,17)]
    if name in ['near_misses','trigger','overlap_trigger','retrigger_during_cooldown','retrigger_after_cooldown']: timings += [(1000,0),(703,49),(500,83)]
    for half,offset in timings:
        label=f'{name}_h{half}_p{offset}'
        log=OUT/f'{label}.csv'
        p=subprocess.run([vvp,str(OUT/'sim.vvp'),f'+VECTORS={vec}',f'+LOG={log}',f'+HALF={half}',f'+OFFSET={offset}'],capture_output=True,text=True,timeout=240)
        (OUT/f'{label}.log').write_text(p.stdout+p.stderr)
        item={'name':name,'half_period_ns':half,'offset_ns':offset,'frames':len(samples),'passed':p.returncode==0,'activations':activations,'output':p.stdout.strip()}
        if name.startswith('tone_') and p.returncode==0:
            rows=list(csv.reader(log.open()))
            output=[int(r[2]) for r in rows][258:-4]
            input_=samples[256:-6]
            # RMS over a long, settled interval. Boundary-phase error is small.
            rms=lambda a: math.sqrt(sum(x*x for x in a)/len(a))
            item['gain_db']=20*math.log10(max(rms(output),1e-12)/rms(input_))
        results.append(item)
        print(json.dumps(item),flush=True)
summary={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
         'adapter_sha256':hashlib.sha256(ADAPTER.read_bytes()).hexdigest(),
         'coefficient_sum':sum(coeffs),'symmetric':coeffs==coeffs[::-1],
         'total_frames':sum(x['frames'] for x in results),
         'all_passed':all(x['passed'] for x in results),'tests':results}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print('SUMMARY',json.dumps({k:v for k,v in summary.items() if k!='tests'}),flush=True)
raise SystemExit(0 if summary['all_passed'] else 1)
