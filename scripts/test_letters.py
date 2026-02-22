"""Comprehensive letter + number test for HeuristicClassifier."""
from ml.heuristic_classifier import HeuristicClassifier
import numpy as np

hc = HeuristicClassifier()


def make_hand(wrist=(0.5, 0.8, 0), finger_configs=None, thumb=None, scale=1.0):
    lm = [None] * 21
    w = np.array(wrist)
    s = scale
    lm[0] = wrist

    if thumb == 'out':
        lm[1] = (w[0]-0.06*s, w[1]-0.05*s, 0)
        lm[2] = (w[0]-0.10*s, w[1]-0.10*s, 0)
        lm[3] = (w[0]-0.14*s, w[1]-0.14*s, 0)
        lm[4] = (w[0]-0.18*s, w[1]-0.16*s, 0)
    elif thumb == 'across':
        lm[1] = (w[0]-0.04*s, w[1]-0.05*s, 0)
        lm[2] = (w[0]-0.06*s, w[1]-0.08*s, 0)
        lm[3] = (w[0]-0.03*s, w[1]-0.13*s, 0)
        lm[4] = (w[0]+0.02*s, w[1]-0.14*s, -0.01)
    elif thumb == 'up':
        lm[1] = (w[0]-0.05*s, w[1]-0.05*s, 0)
        lm[2] = (w[0]-0.08*s, w[1]-0.10*s, 0)
        lm[3] = (w[0]-0.10*s, w[1]-0.18*s, 0)
        lm[4] = (w[0]-0.10*s, w[1]-0.24*s, 0)
    elif thumb == 'circle':
        lm[1] = (w[0]-0.04*s, w[1]-0.05*s, 0)
        lm[2] = (w[0]-0.06*s, w[1]-0.10*s, 0)
        lm[3] = (w[0]-0.04*s, w[1]-0.15*s, 0)
    elif thumb in ('touch_middle', 'touch_pinky', 'touch_ring', 'touch_index'):
        lm[1] = (w[0]-0.04*s, w[1]-0.05*s, 0)
        lm[2] = (w[0]-0.06*s, w[1]-0.08*s, 0)
        lm[3] = (w[0]-0.03*s, w[1]-0.13*s, 0)
        # lm[4] set after fingers are built
    else:
        lm[1] = (w[0]-0.04*s, w[1]-0.05*s, 0)
        lm[2] = (w[0]-0.06*s, w[1]-0.08*s, 0)
        lm[3] = (w[0]-0.04*s, w[1]-0.10*s, 0)
        lm[4] = (w[0]-0.02*s, w[1]-0.11*s, 0)

    fx_offsets = [-0.04, 0.0, 0.04, 0.08]
    fingers = ['index', 'middle', 'ring', 'pinky']
    bases = [5, 9, 13, 17]
    h = 0.25 * s

    for i, (fn, base, fx) in enumerate(zip(fingers, bases, fx_offsets)):
        mx = w[0] + fx * s
        my = w[1] - h
        lm[base] = (mx, my, 0)
        cfg = (finger_configs or {}).get(fn, 'down')
        if cfg == 'up':
            lm[base+1] = (mx, my-0.08*s, 0)
            lm[base+2] = (mx, my-0.14*s, 0)
            lm[base+3] = (mx, my-0.20*s, 0)
        elif cfg == 'curled':
            lm[base+1] = (mx, my-0.06*s, 0)
            lm[base+2] = (mx, my-0.02*s, 0)
            lm[base+3] = (mx, my+0.01*s, 0)
        elif cfg == 'hook':
            lm[base+1] = (mx, my-0.08*s, 0)
            lm[base+2] = (mx, my-0.04*s, 0)
            lm[base+3] = (mx, my-0.01*s, 0)
        elif cfg == 'semicurl':
            lm[base+1] = (mx, my-0.07*s, 0)
            lm[base+2] = (mx-0.01*s, my-0.04*s, 0)
            lm[base+3] = (mx-0.02*s, my-0.02*s, 0)
        elif cfg == 'sideways':
            lm[base+1] = (mx+0.06*s, my-0.01*s, 0)
            lm[base+2] = (mx+0.12*s, my-0.01*s, 0)
            lm[base+3] = (mx+0.18*s, my-0.01*s, 0)
        else:
            lm[base+1] = (mx, my-0.06*s, 0)
            lm[base+2] = (mx, my-0.02*s, 0)
            lm[base+3] = (mx, my+0.01*s, 0)

    # Post-build thumb placement for touch variants
    if thumb == 'circle':
        idx_tip = lm[8]
        lm[4] = (idx_tip[0]-0.005*s, idx_tip[1]+0.005*s, 0)
    elif thumb == 'touch_middle':
        mid_tip = lm[12]
        lm[4] = (mid_tip[0]-0.01*s, mid_tip[1]+0.01*s, 0)
    elif thumb == 'touch_pinky':
        pnk_tip = lm[20]
        lm[4] = (pnk_tip[0]-0.01*s, pnk_tip[1]+0.01*s, 0)
    elif thumb == 'touch_ring':
        rng_tip = lm[16]
        lm[4] = (rng_tip[0]-0.01*s, rng_tip[1]+0.01*s, 0)
    elif thumb == 'touch_index':
        idx_tip = lm[8]
        lm[4] = (idx_tip[0]-0.01*s, idx_tip[1]+0.01*s, 0)

    return lm


# ═══════════════════════════════════════════════════════════════
#  LETTER TESTS (A-Z)
# ═══════════════════════════════════════════════════════════════
r = {}
r['A'] = hc.predict(make_hand(thumb='up', finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'curled'}))
r['B'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'up','middle':'up','ring':'up','pinky':'up'}))
# D: index up + thumb touching middle tip
r['D'] = hc.predict(make_hand(thumb='touch_middle', finger_configs={'index':'up','middle':'curled','ring':'curled','pinky':'curled'}))
r['E'] = hc.predict(make_hand(thumb='across', finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'curled'}))
r['F'] = hc.predict(make_hand(thumb='circle', finger_configs={'index':'up','middle':'up','ring':'up','pinky':'up'}))
r['G'] = hc.predict(make_hand(thumb='out', finger_configs={'index':'sideways','middle':'curled','ring':'curled','pinky':'curled'}))
r['H'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'sideways','middle':'sideways','ring':'curled','pinky':'curled'}))
r['I'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'up'}))
r['L'] = hc.predict(make_hand(thumb='out', finger_configs={'index':'up','middle':'curled','ring':'curled','pinky':'curled'}))
# O with semi-curled index (forming circle, not tight fist)
r['O'] = hc.predict(make_hand(thumb='circle', finger_configs={'index':'semicurl','middle':'curled','ring':'curled','pinky':'curled'}))
# S: slightly looser fist (pinky slightly outward for spread > 0.55)
lm_s = list(make_hand(thumb='across', finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'curled'}))
lm_s[20] = (lm_s[20][0]+0.03, lm_s[20][1], lm_s[20][2])
r['S'] = hc.predict(lm_s)
r['U'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'up','middle':'up','ring':'curled','pinky':'curled'}))
# V: index and middle spread apart
lm_v = list(make_hand(thumb=None, finger_configs={'index':'up','middle':'up','ring':'curled','pinky':'curled'}))
lm_v[8] = (lm_v[8][0]-0.06, lm_v[8][1], lm_v[8][2])
lm_v[12] = (lm_v[12][0]+0.06, lm_v[12][1], lm_v[12][2])
r['V'] = hc.predict(lm_v)
r['W'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'up','middle':'up','ring':'up','pinky':'curled'}))
r['X'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'hook','middle':'curled','ring':'curled','pinky':'curled'}))
r['Y'] = hc.predict(make_hand(thumb='out', finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'up'}))
r['5'] = hc.predict(make_hand(thumb='out', finger_configs={'index':'up','middle':'up','ring':'up','pinky':'up'}))
r['3'] = hc.predict(make_hand(thumb='out', finger_configs={'index':'up','middle':'up','ring':'curled','pinky':'curled'}))

# Q: pointing down
lm_q = [None]*21
lm_q[0] = (0.5,0.2,0)
lm_q[1] = (0.44,0.25,0); lm_q[2] = (0.40,0.30,0); lm_q[3] = (0.38,0.36,0); lm_q[4] = (0.36,0.40,0)
lm_q[5] = (0.46,0.45,0); lm_q[6] = (0.46,0.53,0); lm_q[7] = (0.46,0.59,0); lm_q[8] = (0.46,0.65,0)
lm_q[9] = (0.50,0.45,0); lm_q[10] = (0.50,0.51,0); lm_q[11] = (0.50,0.48,0); lm_q[12] = (0.50,0.46,0)
lm_q[13] = (0.54,0.45,0); lm_q[14] = (0.54,0.51,0); lm_q[15] = (0.54,0.48,0); lm_q[16] = (0.54,0.46,0)
lm_q[17] = (0.58,0.45,0); lm_q[18] = (0.58,0.51,0); lm_q[19] = (0.58,0.48,0); lm_q[20] = (0.58,0.46,0)
r['Q'] = hc.predict(lm_q)

# P: pointing down, index+middle extended
lm_p = [None]*21
lm_p[0] = (0.5,0.2,0)
lm_p[1] = (0.44,0.22,0); lm_p[2] = (0.42,0.24,0); lm_p[3] = (0.42,0.26,0); lm_p[4] = (0.42,0.28,0)
lm_p[5] = (0.46,0.45,0); lm_p[6] = (0.46,0.53,0); lm_p[7] = (0.46,0.59,0); lm_p[8] = (0.46,0.65,0)
lm_p[9] = (0.50,0.45,0); lm_p[10] = (0.50,0.53,0); lm_p[11] = (0.50,0.59,0); lm_p[12] = (0.50,0.65,0)
lm_p[13] = (0.54,0.45,0); lm_p[14] = (0.54,0.51,0); lm_p[15] = (0.54,0.48,0); lm_p[16] = (0.54,0.46,0)
lm_p[17] = (0.58,0.45,0); lm_p[18] = (0.58,0.51,0); lm_p[19] = (0.58,0.48,0); lm_p[20] = (0.58,0.46,0)
r['P'] = hc.predict(lm_p)

# R: index crosses over middle
lm_r = list(make_hand(thumb=None, finger_configs={'index':'up','middle':'up','ring':'curled','pinky':'curled'}))
mid_mcp = lm_r[9]
lm_r[8] = (mid_mcp[0]+0.01, mid_mcp[1]-0.16, 0)
r['R'] = hc.predict(lm_r)


# ═══════════════════════════════════════════════════════════════
#  NUMBER TESTS (unique shapes: 1, 6, 7, 8, 9)
# ═══════════════════════════════════════════════════════════════
n = {}
# 1: index up + thumb NOT touching middle (fist-style, not D)
n['1'] = hc.predict(make_hand(thumb=None, finger_configs={'index':'up','middle':'curled','ring':'curled','pinky':'curled'}))
# 6: index+middle+ring up, thumb touches pinky
n['6'] = hc.predict(make_hand(thumb='touch_pinky', finger_configs={'index':'up','middle':'up','ring':'up','pinky':'curled'}))
# 7: index+middle+pinky up, ring curled to touch thumb
n['7'] = hc.predict(make_hand(thumb='touch_ring', finger_configs={'index':'up','middle':'up','ring':'curled','pinky':'up'}))
# 8: index+ring+pinky up, middle curled to touch thumb
n['8'] = hc.predict(make_hand(thumb='touch_middle', finger_configs={'index':'up','middle':'curled','ring':'up','pinky':'up'}))
# 9: middle+ring+pinky up, index curled to touch thumb
n['9'] = hc.predict(make_hand(thumb='touch_index', finger_configs={'index':'curled','middle':'up','ring':'up','pinky':'up'}))


# ═══════════════════════════════════════════════════════════════
#  RESULTS
# ═══════════════════════════════════════════════════════════════
print('=== LETTER DETECTION RESULTS ===')
p = 0; f = 0
for l in sorted(r.keys()):
    lb, c = r[l]
    ok = 'OK' if lb == l else 'FAIL'
    if ok == 'OK': p += 1
    else: f += 1
    print(f'  {l}: detected={lb} conf={c:.2f} [{ok}]')
print(f'\nLetters passed: {p}/{p+f}, Failed: {f}')

print('\n=== NUMBER DETECTION RESULTS ===')
np2 = 0; nf = 0
for num in sorted(n.keys()):
    lb, c = n[num]
    ok = 'OK' if lb == num else 'FAIL'
    if ok == 'OK': np2 += 1
    else: nf += 1
    print(f'  {num}: detected={lb} conf={c:.2f} [{ok}]')
print(f'\nNumbers passed: {np2}/{np2+nf}, Failed: {nf}')

print('\n=== NUMBER/LETTER OVERLAPS (same shape) ===')
print('  0 = O (thumb-index circle)')
print('  2 = V (index+middle spread)')
print('  4 = B (four fingers up)')
print('  9 ~ F (thumb-index circle + 3 fingers up)')

print('\n=== SCALE INDEPENDENCE TEST ===')
for sc in [0.3, 0.5, 1.5, 2.5]:
    fails = []
    for letter, cfg in [
        ('B', dict(thumb=None, finger_configs={'index':'up','middle':'up','ring':'up','pinky':'up'})),
        ('D', dict(thumb='touch_middle', finger_configs={'index':'up','middle':'curled','ring':'curled','pinky':'curled'})),
        ('L', dict(thumb='out', finger_configs={'index':'up','middle':'curled','ring':'curled','pinky':'curled'})),
        ('I', dict(thumb=None, finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'up'})),
        ('W', dict(thumb=None, finger_configs={'index':'up','middle':'up','ring':'up','pinky':'curled'})),
        ('Y', dict(thumb='out', finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'up'})),
        ('A', dict(thumb='up', finger_configs={'index':'curled','middle':'curled','ring':'curled','pinky':'curled'})),
        ('1', dict(thumb=None, finger_configs={'index':'up','middle':'curled','ring':'curled','pinky':'curled'})),
    ]:
        cfg['scale'] = sc
        lb, _ = hc.predict(make_hand(**cfg))
        if lb != letter:
            fails.append(f'{letter}->{lb}')
    print(f'  Scale {sc}x: {"ALL OK" if not fails else f"FAILS: {fails}"}')

total_pass = p + np2
total_tests = p + f + np2 + nf
print(f'\n=== TOTAL: {total_pass}/{total_tests} ===')
