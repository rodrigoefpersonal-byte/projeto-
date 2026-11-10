# Gera a trilha (batida + efeitos sincronizados com cena.html) -> trilha.wav
import numpy as np, wave
SR = 44100; DUR = 16.0
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

# --- música: 120 bpm, progressão Lá menor - Fá - Dó - Sol (1 compasso cada = 2s)
BEAT = 0.5
mid = lambda m: 440*2**((m-69)/12)
prog = [(57,[69,72,76]), (53,[69,72,77]), (48,[67,72,76]), (55,[67,71,74])]
for bar in range(8):
    t0 = bar*2.0
    root, chord = prog[bar % 4]
    # pad
    for m in chord:
        add(tone(mid(m), 2.0, 0.035, a=.15), t0)
    # baixo em colcheias
    for k in range(4):
        add(tone(mid(root-12), .45, .18, a=.005, d=.25), t0 + k*BEAT)
    for b in range(4):
        tb = t0 + b*BEAT
        if tb >= 0.36: add(kick(), tb, .8)
        add(hat(), tb + BEAT/2, 1)
        if b in (1,3) and tb > 3.2: add(clap(), tb, .55)

# --- efeitos sincronizados com as animações
add(whoosh(.4), 0.0, .5)
add(kick(), 0.36, 1.0)                                   # cubo cai
for at in (0.95, 1.25): add(pop(), at, .5)
add(stamp(), 1.6, .8)
add(whoosh(.3), 2.2, .35)                                # pulinho do cubo
B = [3.25, 6.5, 10.0, 13.0]
for b in B: add(whoosh(), b-0.27, .9)                    # transições
S2, S3, S4, S5 = B
for at in (.15, .25, .4): add(pop(1200,500,.08), S2+at, .35)
for i in range(5): add(pop(700+120*i, 250, .1), S2+0.95+i*0.2+0.12, .45)  # clipes
add(pop(), S2+1.9, .4)
for at in (.15, .25, .4): add(pop(1200,500,.08), S3+at, .35)
for i in range(5): add(pop(500+150*i, 200, .12), S3+0.55+i*0.22, .5)    # barras
add(pop(), S3+1.2, .4)
add(whoosh(.7), S3+1.9, .6)                              # seta
add(pop(1600,800,.15), S3+2.55, .6)                      # alvo
for at in (.25, .6, 1.25, 1.6): add(stamp(), S4+at, .85)
add(whoosh(1.0), S5+0.1, .6)                             # moeda girando
add(stamp(), S5+1.2, .85)
add(pop(), S5+1.6, .5); add(pop(), S5+1.95, .4)

# fade final e normalização
fade = np.ones(N); fn = int(1.2*SR); fade[-fn:] = np.linspace(1,0,fn)
mix *= fade
mix = np.tanh(mix*1.2)
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix*32767).astype(np.int16)
with wave.open('trilha.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
