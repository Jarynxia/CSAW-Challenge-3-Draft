# Challenge 3 — T1 draft

This is a new, isolated working copy. It does not modify the local weak-payload candidate or teammate folders.

## Primary Trojan

T1 uses the separate local weak-payload candidate's exact three-sample trigger on completed left-channel I2S samples:

`0x5A3C → 0xC3A5 → 0x96E1`

After the final trigger sample, T1 bypasses the FIR for a bounded 128 left-channel frames (the trigger-completing frame plus the next 127). At 16 kframes/s that is an 8 ms burst. It then automatically returns to the normal FIR output. A 1,024-frame cooldown (64 ms at 16 kframes/s) blocks immediate retriggering and returns the trigger matcher to idle. The existing two-frame I2S output schedule and right-channel echo remain unchanged. Outside the short payload window, the FIR output path is unchanged.

The trigger reuses the existing left-sample strobe and adds three 16-bit comparisons, a small state register, two short counters, and an output selection. At the documented maximum 1 MHz BCLK, the 63-cycle FIR MAC finishes within the 320 `ICE_CLK` cycles between frames, so `left_sample` remains associated with the in-flight result. This timing argument still needs simulation and board confirmation.

## Files

- `rtl/fir_audio_top_t1.v` — new AI-authored T1 variant.
- `rtl/fir_audio_top_hackster.pcf` — copied pin constraints for the Hackster UP5K/SG48 board; the audio pins are documented as verified in the source notes, while LED role assignments remain tentative.
- `tb/tb_i2s.sv` and `tb/phase4_dut_adapter.sv` — pin-level I2S harness copied into this new deliverable.
- `tb/run_tests.py` — independent integer oracle and case generator, updated for the bypass payload and the official flush/self-test vector.
- `tb/check_trigger_wavs.py` — checks speech/music WAVs for accidental exact trigger sequences before using them as normal-operation evidence.
- `tb/make_t1_wav.py` — repeatable host WAV with pass-band audio, the trigger, then a stop-band tone.
- `research/strategy.md` — three distinct Trojan options, score targets, and Bonus B plan.
- `ai/` — generation record and submission-log checklist.

## Local simulation

The current machine does not expose Icarus Verilog, Yosys, or nextpnr on `PATH`, so these commands are prepared but have not been run here:

```powershell
python tb/run_tests.py
```

The runner expects `iverilog` and `vvp`, or `IVERILOG` and `VVP` environment variables pointing to them. It checks pin-level receive/output behavior, echo, trigger state, normal untriggered FIR behavior, trigger near-misses, the 1,024-zero-frame flush, the official seeded self-test, the exact bypass-window expiry, cooldown suppression, re-arming, and a stop-band tone that is filtered again after the pulse.

Before treating a real speech/music file as a normal-operation vector, run `python tb/check_trigger_wavs.py path/to/noisy_test_audio.wav path/to/filtered_test_audio.wav`. The official challenge WAVs still need this scan and a board-side baseline comparison.

With Yosys, nextpnr-ice40, and icepack installed, the prepared build flow runs simulation, synthesizes for UP5K, places/routes for SG48 at 10 MHz, and packs a `.bin`:

```powershell
.\build_t1.ps1
```

Use `-SkipSimulation` only if the simulator is unavailable. This script does not program the FPGA.

The software oracle uses the coefficients in the candidate file. It does **not** prove bit-for-bit equivalence with the official `fir_audio_top.bin`. Before claiming baseline preservation, stream the official reference audio through both the provided bitstream and this build, then compare against `filtered_test_audio.wav` exactly as the challenge README specifies.

## Host demonstration

Generate the trigger input:

```powershell
python tb/make_t1_wav.py demo/t1_trigger.wav
```

After building and programming this RTL on the Hackster board, use the official Challenge 3 `tools/stream_audio.py` to capture the output. Keep the host log, input WAV, output WAV, spectrogram, and a scope/logic capture of the activity pin in `demo/`. The example WAV is not hardware evidence; no physical-board run has been performed in this session.

## Current evidence status

The prior `Person1` judging report records 29 simulation runs over 115,882 frames with zero failures for the one-LSB payload, and a successful UP5K synthesis/place-and-route. That report used a candidate-derived model rather than the official bitstream output. The new bypass payload has not yet been compiled, simulated, synthesized, or demonstrated on hardware. This draft therefore does not claim a 95/100 score.

The Challenge 3 rules require AI transcripts for the Trojan and exploit logic. `ai/SESSION_LOG.md` records this revision; include the full Codex conversation export and any original AI logs for the copied baseline/Trojan before final submission.
