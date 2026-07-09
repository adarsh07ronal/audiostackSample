# AudioStack Sample — Mini Automotive Audio Stack

A small, self-contained Python simulation of how an in-vehicle infotainment (IVI)
system — like Android Automotive — manages three competing audio streams
(**music**, **navigation prompts**, **phone calls**) with a Hardware Abstraction
Layer, a priority router, and a PCM mixer.

There's no real music here — each stream is a synthetic sine-wave tone (different
pitch per stream, generated with `sox`) so you can tell them apart by ear while the
router switches between them.

> A full interactive docs site with a live router demo also lives in this repo —
> open [`index.html`](./index.html) in a browser.

## Quick start

```bash
pip install -r requirements.txt
# macOS only, PyAudio needs the native PortAudio lib:
brew install portaudio

python main.py        # cross-platform (PyAudio)
python main_alsa.py   # Linux only (ALSA directly)
```

## Files

| File | Role |
|---|---|
| [`hal.py`](./hal.py) | **Hardware Abstraction Layer.** Wraps a WAV file and guarantees every `read()` returns an exact, fixed-size PCM buffer — looping and silence-padding at end of stream. |
| [`router.py`](./router.py) | **Policy.** A tiny state machine (`music` / `nav` / `call`) that decides mixing weights based on a frame counter — simulating a nav prompt firing, then a call coming in. |
| [`mixer.py`](./mixer.py) | **Mixer.** Combines the three PCM streams using weighted sums in float32 (to avoid int16 overflow), normalizes gain, clips, and converts back to int16 PCM bytes. |
| [`main.py`](./main.py) | **Entry point (cross-platform).** Wires HAL → router → mixer → PyAudio output in a real-time loop. |
| [`main_alsa.py`](./main_alsa.py) | **Entry point (Linux/ALSA).** Same pipeline, targets ALSA's PCM API directly with an explicit `S16_LE` format. |
| [`requirements.txt`](./requirements.txt) | `numpy` (vectorized mixing math) + `PyAudio` (audio output). |
| `streams/*.wav` | Synthetic 16-bit mono WAV tones: `music_16.wav` (440Hz), `nav_16.wav` (1000Hz), `call_16.wav` (220Hz). |
| [`index.html`](./index.html) / [`DESIGN.md`](./DESIGN.md) | An interactive documentation site for this project (design tokens + rendered docs). |

## Architecture

```
music.wav  ──┐
nav.wav    ──┼─► hal.py ─► router.py ─► mixer.py ─► hal.py output / PyAudio ─► 🔈 speakers
call.wav   ──┘  (read)    (weights)     (mix)
```

- **`hal.py`** reads fixed-size PCM chunks from each WAV file.
- **`router.py`** looks at the current loop index and decides which stream(s) should be audible, returning volume weights `(wm, wn, wc)`.
- **`mixer.py`** applies those weights to combine the three chunks into one output buffer.
- **`main.py`** / **`main_alsa.py`** run the loop and write the mixed buffer to the audio device.

## Priority rules

| Mode | Music weight | Nav weight | Call weight | Behavior |
|---|---|---|---|---|
| `music` (default) | 1.0 | 0.0 | 0.0 | Music plays at full volume. |
| `nav` (frames 50–150) | 0.3 | 1.0 | 0.0 | Nav plays at full volume; music **ducked** to 30% (still audible, quieter). |
| `call` (frames 200–350) | 0.0 | 0.0 | 1.0 | Call takes over completely; music and nav are muted. |

This mirrors Android's `AudioFocus` system: `AUDIOFOCUS_GAIN` (full volume),
`AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK` (lower volume, keep playing — nav), and
`AUDIOFOCUS_LOSS` (stop entirely — call overriding music/nav).

## Function flow (per loop iteration)

```
1. hal.read(CHUNK)          → get next chunk of PCM bytes from each of 3 WAV files
2. router.update_mode(i)    → update mode based on loop index i
   router.get_weights()     → turn mode into (wm, wn, wc)
3. mixer.mix3(...)          → combine 3 chunks into 1, using the weights
4. pad/trim buffer          → enforce exact expected byte size (safety)
5. stream.write(out)        → send final bytes to the audio device
```

## Data flow (byte level)

```
WAV file
  │ wave.readframes()
  ▼
raw PCM bytes (int16)                    ← hal.py
  │ np.frombuffer + astype(float32)
  ▼
float32 array (overflow-safe)            ← mixer.py
  │ a1*wm + a2*wn + a3*wc
  ▼
weighted sum
  │ if total_weight > 1.0: divide by total_weight
  ▼
normalized float32
  │ np.clip(-32768, 32767) + astype(int16)
  ▼
int16 PCM bytes → padded/trimmed to exact size → stream.write() → speakers
```

`int16 → float32 → int16` matters because two full-volume `int16` samples added
together (32767 + 32767 = 65534) would overflow and wrap into noise. Doing the
math in float32 and only quantizing back to `int16` at the very end avoids that.

## Sample trace

Given one instant where the three streams happen to have sample values
`music=1000`, `nav=2000`, `call=3000` (illustrative numbers), here's what happens
at three different points in the 1000-iteration loop:

| Loop `i` | Mode | Weights `(wm, wn, wc)` | Math | Output sample |
|---|---|---|---|---|
| `i=0` | `music` | `(1.0, 0.0, 0.0)` | `1000*1.0 = 1000`; total=1.0, no normalize | **1000** — pure music |
| `i=100` | `nav` | `(0.3, 1.0, 0.0)` | `1000*0.3 + 2000*1.0 = 2300`; total=1.3 → `2300/1.3` | **1769** — mostly nav, faint music underneath |
| `i=250` | `call` | `(0.0, 0.0, 1.0)` | `3000*1.0 = 3000`; total=1.0, no normalize | **3000** — pure call |

Every sample in a 1024-frame chunk goes through this same per-sample math at once
(vectorized with NumPy), once per loop iteration, in real time.

## Concepts this project demonstrates

- **Hardware Abstraction Layer (HAL)** — caller never touches the WAV file directly, only `read()`/`get_params()`.
- **Strategy pattern** — the mixer has no idea what "music", "nav", or "call" mean; it just applies whatever weights the router gives it.
- **Finite state machine** — `router.update_mode()` transitions between 3 states based on a frame counter.
- **Buffer contract / invariant** — every stage guarantees a fixed-size buffer, avoiding underruns/glitches downstream.
- **Fixed-to-float-to-fixed mixing** — standard technique to avoid integer overflow when summing PCM samples.
- **Audio ducking** — lowering (not muting) a stream's volume to make room for a higher-priority one.
