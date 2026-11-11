# Gera a trilha (batida + efeitos sincronizados com cena.html) -> trilha.wav
import numpy as np, wave
SR = 44100; DUR = 20.0
N = int(SR*DUR); mix = np.zeros(N)
rng = np.random.default_rng(7)
t_all = np.arange(N)/SR

def add(sig, at, gain=1.0):
    i = int(at*SR); j = min(N, i+len(sig))
    if i < N: mix[i:j] += sig[:j-i]*gain

def env(n, a=0.005, d=0.2):
    t = np.arange(n)/SR
    return np.minimum(1, t/a) * np.exp(-t/d)

def kick():
    n = int(.45*SR); t = np.arange(n)/SR
    f = 45 + 110*np.exp(-t/0.04)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env(n, .002, .16)

def hat():
    n = int(.08*SR); x = rng.standard_normal(n); x = np.diff(x, prepend=0)
    return x*env(n, .001, .02)*0.35

def clap():
    n = int(.25*SR); x = rng.standard_normal(n); x = np.diff(x, prepend=0)
    e = env(n, .002, .07)
    return x*e*0.5

def pop(f0=900, f1=300, dur=.12):
    n = int(dur*SR); t = np.arange(n)/SR
    f = f1 + (f0-f1)*np.exp(-t/0.025)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.001,dur/3)

def stamp():
    out = kick()*0.9
    for x in (pop(500,120,.2)*0.6, clap()*0.6): out[:len(x)] += x
    return out

def whoosh(dur=.55):
    n = int(dur*SR); t = np.arange(n)/SR
    x = rng.standard_normal(n)
    # suaviza (passa-baixa simples por média móvel variável)
    out = np.zeros(n); k = 1
    sm = np.convolve(x, np.ones(6)/6, mode='same')
    hi = np.diff(x, prepend=0)
    w = np.sin(np.pi*t/dur)**2
    mixw = t/dur
    return (sm*(1-mixw) + hi*mixw*0.5) * w * 0.9

def tone(freq, dur, vol, a=.02, d=None):
    n = int(dur*SR); t = np.arange(n)/SR
    s = np.sin(2*np.pi*freq*t) + 0.3*np.sin(2*np.pi*freq*2*t) + 0.12*np.sin(2*np.pi*freq*3*t)
    e = np.minimum(1, t/a) * np.minimum(1, (dur-t)/0.08)
    if d: e *= np.exp(-t/d)
    return s*e*vol

# --- música: 120 bpm, progressão Mi menor - Dó - Sol - Ré
BEAT = 0.5
mid = lambda m: 440*2**((m-69)/12)
prog = [(52,[67,71,76]), (48,[67,72,76]), (55,[67,71,74]), (50,[66,69,74])]
for bar in range(10):
    t0 = bar*2.0
    root, chord = prog[bar % 4]
    for m in chord: add(tone(mid(m), 2.0, 0.035, a=.15), t0)
    for k in range(4): add(tone(mid(root-12), .45, .18, a=.005, d=.25), t0 + k*BEAT)
    for b in range(4):
        tb = t0 + b*BEAT
        if tb >= 0.4: add(kick(), tb, .8)
        add(hat(), tb + BEAT/2, 1)
        if b in (1,3) and tb > 2.9: add(clap(), tb, .55)

# --- efeitos sincronizados com cena2.html
add(whoosh(.4), 0.0, .5)
add(kick(), 0.35, 1.0)                                   # celular cai
add(stamp(), 0.8, .7); add(stamp(), 1.15, .85)
for k in range(4): add(pop(300, 120, .08), 1.9 + k*0.12, .5)   # celular treme
add(pop(), 2.0, .45)
B = [3.0, 7.5, 12.0, 16.5]
for b in B: add(whoosh(), b-0.27, .9)
for S in B[:3]:                                          # cenas de erro
    add(pop(1200,500,.08), S+0.1, .35)
    add(kick(), S+0.2+0.75*0.364*0.55/0.55, .9)          # número cai
    add(pop(1000,400,.08), S+0.45, .35); add(pop(1000,400,.08), S+0.6, .35)
    add(pop(800,300,.1), S+0.85, .45)                    # visual entra
    add(pop(1500,900,.15), S+2.9, .55); add(pop(1900,1200,.12), S+3.0, .4)   # solução (✔)
S1, S2, S3, S5 = B[0], B[1], B[2], B[3]
for k in range(3): add(pop(1300,1300,.06), S1+1.2+k*0.4, .6)   # tique do cronômetro
add(stamp(), S1+2.4, .7)                                 # chega no 0
add(whoosh(.5), S1+2.45, .6)                             # rolou o feed
for i in range(24): add(pop(600+40*(i%6),300,.05), S2+1.0+(i%6)*0.06+(i//6)*0.05, .12)  # multidão
add(whoosh(.5), S2+1.5, .5); add(pop(1600,800,.15), S2+1.95, .6)     # alvo
for at in (1.5, 1.8, 2.1): add(pop(900,400,.1), S3+at, .5)           # legendas
add(whoosh(.9), S5+0.1, .6)
add(stamp(), S5+0.6, .8); add(stamp(), S5+0.95, .85)
add(pop(), S5+1.5, .5); add(pop(), S5+1.9, .4)
# fade final e normalização
fade = np.ones(N); fn = int(1.2*SR); fade[-fn:] = np.linspace(1,0,fn)
mix *= fade
mix = np.tanh(mix*1.2)
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix*32767).astype(np.int16)
with wave.open('trilha2.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
