# Challenge 3 evidence scorecard

This is a planning scorecard against the official fixed-level rubric, not a predicted judge score. The current T1 files have not been simulated, synthesized, built, or run on a board, so no implementation category is claimed as earned.

## Current evidence

| Category | Maximum | Evidence in this draft | Current status |
| --- | ---: | --- | --- |
| Creative use of generative AI | 35 | This Codex session used retrieved challenge/reference material to specify and author T1 RTL and supporting test/build artifacts. `ai/SESSION_LOG.md` records the design response. | Incomplete: no autonomous generation/insertion/evaluation loop and no complete conversation export or prior-source provenance logs. |
| Trojan quality | 25 | T1 uses an exact three-sample left-channel sequence and selects the raw input at MAC completion for a 128-frame window, then returns to FIR filtering and enforces a 1,024-frame cooldown. | Unverified: no RTL simulation, synthesis, official-bitstream baseline comparison, or real-audio false-trigger scan. |
| System automation | 15 | A PowerShell build wrapper and a pin-level test runner are prepared. | Incomplete: the machine has no runnable Python/Icarus/Yosys/nextpnr toolchain; AI generation/insertion and board programming are not automated. |
| Documentation and reproducibility | 15 | Strategy, interface assumptions, trigger, payload, build commands, test intent, and evidence checklist are recorded. | Incomplete: exact coefficient provenance, official baseline comparison, tool versions, full AI logs, and board reproduction evidence are missing. |
| Hardware demonstration | 10 | A host-side trigger WAV generator and evidence checklist are prepared. | Not demonstrated: no board capture or normal-operation baseline run exists. |

## 95-point base target

The official categories use fixed score levels. One viable 95-point combination is:

| Category | Target | Required evidence before submission |
| --- | ---: | --- |
| Creative AI use | 35 | Preserve complete transcripts showing an AI-driven loop that retrieves the interface/recovered design, authors the Trojan and insertion, and iterates using tool feedback. |
| Trojan quality | 20 | Pass the official bit-for-bit dormant baseline; show the trigger avoids the supplied speech/noisy/self-test traffic; demonstrate the out-of-band bypass; report negligible resource/timing cost. |
| Automation | 15 | One reproducible command from AI generation/insertion through build and verification, with only the explicitly permitted physical-board action left to an operator. |
| Documentation | 15 | Explain bitstream recovery, coefficient/filter behavior, I2S, AI method, trigger/payload, exact commands and versions, and board reproduction steps without guesswork. |
| Hardware demonstration | 10 | Capture both the exact normal-operation baseline and the triggered payload on the physical board, with host logs and interpretable audio/scope evidence. |
| **Base total** | **95** | **All five rows require evidence; none is currently complete.** |

Another 95-point combination is 35 AI + 25 quality + 15 automation + 12 documentation + 8 hardware, but it still requires the 35-point AI level and a clear physical-board payload demo.

## Bonus B evidence gate

The T2 concept can carry a fixed attacker-selected message in the filtered left-channel LSB after its independent tone trigger arms. At 16 kframes/s, one bit per sample gives a nominal raw rate of 16 kbit/s before framing overhead. Bonus B's full credit requires a physical-board capture that recovers the exact message and reports a measured rate and BER. The LSB approach is compact and bit-exact; keep the pass-band BPSK option documented as a fallback if judges expect a channel visible in the audio waveform. Do not report a bit rate or BER as measured until captured on the board.

## Release gates

1. Obtain the official baseline audio and reference bitstream run; make the T1 dormant output bit-identical.
2. Run all trigger, near-miss, right-channel-only, flush, self-test, stop-band, 128-frame expiry, 1,024-frame cooldown/re-arm, timing, and resource checks with the final candidate RTL.
3. Scan the official speech/noisy audio for the exact trigger before claiming normal-use selectivity.
4. Complete AI-generated T2 and T3 as separate designs with distinct triggers and payloads; only claim Bonus A points after separate physical demos and baseline checks.
5. Program the Hackster board and capture the normal baseline, T1 payload, host/link logs, WAVs, spectrogram, and timing evidence.
6. Bundle full AI transcripts, original-source provenance, tool versions, and an unambiguous rebuild/run guide.

The official rubric assigns zero hardware-demonstration points when no payload is shown on hardware and requires physical-board bit-exact recovery for full Bonus B credit. See the [Challenge 3 scoring and submission rules](https://raw.githubusercontent.com/JBlocklove/CSAW-AI-Hardware-Attack-Challenge-2026/main/finals/challenge_3/README.md).
