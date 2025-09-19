from pathlib import Path
import numpy as np
import soundfile as sf

SOUND_DIR = Path('assets/sounds')
SOUND_DIR.mkdir(parents=True, exist_ok=True)
SR = 44100

def envelope(length, attack=0.01, release=0.1):
    samples = max(1, int(length * SR))
    env = np.ones(samples, dtype=np.float32)
    attack_samples = max(1, int(min(attack, length) * SR))
    release_samples = max(1, int(min(release, length) * SR))
    env[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, dtype=np.float32)
    env[-release_samples:] = np.linspace(1.0, 0.0, release_samples, dtype=np.float32)
    return env

def white_noise(length, color=1.0):
    samples = max(1, int(length * SR))
    noise = np.random.uniform(-1.0, 1.0, samples).astype(np.float32)
    if color != 1.0:
        spectrum = np.fft.rfft(noise.astype(np.float64))
        freqs = np.fft.rfftfreq(samples, d=1.0 / SR)
        spectrum *= np.power(np.maximum(freqs, 1.0), -color)
        noise = np.fft.irfft(spectrum).astype(np.float32)
    return noise

def sine_wave(freq, length, phase=0.0):
    t = np.linspace(0, length, int(length * SR), endpoint=False, dtype=np.float32)
    return np.sin(2 * np.pi * freq * t + phase)

def normalize(samples, peak=0.9):
    max_val = float(np.max(np.abs(samples)))
    if max_val == 0:
        return samples
    return samples * (peak / max_val)

def save_sound(name, data):
    path = SOUND_DIR / name
    data32 = np.asarray(data, dtype=np.float32)
    sf.write(path, data32, SR, format='OGG', subtype='VORBIS')
    print(f'Wrote {path}')

def make_hit():
    length = 0.18
    noise = white_noise(length, color=0.2)
    click = sine_wave(880, length)
    env = envelope(length, attack=0.005, release=0.12) * np.linspace(1.0, 0.2, len(noise), dtype=np.float32)
    sound = (0.6 * noise + 0.4 * click) * env
    save_sound('sfx_hit.ogg', normalize(sound, 0.75))

def make_levelup():
    notes = [392, 523.25, 659.25]
    segment = 0.22
    pause = 0.04
    total_len = int((segment + pause) * len(notes) * SR)
    sound = np.zeros(total_len, dtype=np.float32)
    cursor = 0
    for idx, freq in enumerate(notes):
        wave = sine_wave(freq, segment) + 0.3 * sine_wave(freq * 2, segment)
        env = envelope(segment, attack=0.01, release=0.08)
        block = wave * env * (1.0 + 0.1 * idx)
        end = cursor + len(block)
        sound[cursor:end] += block
        cursor = end + int(pause * SR)
    save_sound('sfx_levelup.ogg', normalize(sound, 0.8))

def make_start():
    pattern = [261.63, 329.63, 392.0, 523.25]
    durations = [0.18, 0.18, 0.18, 0.32]
    pause = 0.03
    total_samples = int((sum(durations) + pause * (len(pattern) - 1)) * SR)
    sound = np.zeros(total_samples, dtype=np.float32)
    cursor = 0
    for freq, dur in zip(pattern, durations):
        wave = sine_wave(freq, dur) + 0.4 * sine_wave(freq * 1.5, dur)
        env = envelope(dur, attack=0.015, release=0.1)
        block = wave * env
        sound[cursor:cursor + len(block)] += block
        cursor += len(block) + int(pause * SR)
    shimmer = 0.2 * sine_wave(196.0, total_samples / SR)
    save_sound('sfx_start.ogg', normalize(sound + shimmer, 0.85))

def make_gameover():
    length = 1.4
    base = sine_wave(174.61, length)
    minor = 0.5 * sine_wave(207.65, length)
    low = 0.4 * sine_wave(130.81, length)
    env = envelope(length, attack=0.02, release=0.8)
    fade = np.linspace(1.0, 0.0, len(env), dtype=np.float32) ** 1.5
    sound = (base + minor + low) * env * fade
    save_sound('sfx_gameover.ogg', normalize(sound, 0.8))

def make_bgm():
    bpm = 90
    beats = 16
    seconds = beats * 60 / bpm
    t = np.linspace(0, seconds, int(seconds * SR), endpoint=False, dtype=np.float32)
    bass = 0.22 * np.sin(2 * np.pi * 110 * t)
    lead = np.zeros_like(t)
    beat_length = int((60 / bpm) * SR)
    sequence = [261.63, 293.66, 329.63, 349.23, 392.0, 349.23, 329.63, 293.66]
    for i in range(beats):
        freq = sequence[i % len(sequence)]
        phase_t = np.linspace(0, beat_length / SR, beat_length, endpoint=False, dtype=np.float32)
        env = envelope(beat_length / SR, attack=0.01, release=0.2)
        start = i * beat_length
        end = start + beat_length
        osc1 = np.sin(2 * np.pi * freq * phase_t)
        osc2 = np.sin(2 * np.pi * freq * 2 * phase_t)
        lead[start:end] += (0.18 * osc1 + 0.1 * osc2) * env
    pad = 0.16 * np.sin(2 * np.pi * 440 * t) * envelope(seconds, attack=0.3, release=1.0)
    rhythm = 0.08 * np.sign(np.sin(2 * np.pi * bpm / 60 * t * 2)).astype(np.float32)
    mix = normalize(bass + lead + pad + rhythm, 0.6)
    save_sound('bgm_loop.ogg', mix)

def main():
    np.random.seed(42)
    make_hit()
    make_levelup()
    make_start()
    make_gameover()
    make_bgm()

if __name__ == '__main__':
    main()
