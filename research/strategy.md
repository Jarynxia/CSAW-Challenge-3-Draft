# Challenge 3 scoring and design strategy

## Rubric facts

Challenge 3 scores the strongest single Trojan across five fixed-point categories: AI use (35), Trojan quality (25), automation (15), documentation/reproducibility (15), and physical-board demonstration (10). The baseline gate requires bit-identical output against the provided bitstream with the Trojan dormant. Full credit for the two additional Trojans requires distinct trigger and payload mechanisms and physical-board evidence. Bonus B is a covert channel through the left, filtered audio output; the rubric requires recovered attacker-chosen data, a measured bit rate, and an error rate.

Source: [official Challenge 3 README and scoring rubric](https://raw.githubusercontent.com/JBlocklove/CSAW-AI-Hardware-Attack-Challenge-2026/main/finals/challenge_3/README.md).

## Three distinct designs

| ID | Trigger | Payload | Role and tradeoff |
| --- | --- | --- | --- |
| **T1 — primary** | Exact left-sample sequence `5A3C, C3A5, 96E1` | Bypass FIR for 128 frames, then resume filtering; suppress retriggering for 1,024 frames while retaining the existing two-frame transport schedule | Very small digital trigger and one output mux; directly admits stop-band content. Candidate implementation is in `rtl/fir_audio_top_t1.v`. |
| **T2 — Bonus A/B** | Sustained single-frequency stop-band tone, detected over a bounded window and dwell interval | Embed a stored attacker-selected message in the LSB of the left filtered sample after arming | Different trigger and payload from T1. The channel can also earn Bonus B if the board recovers the exact message and reports bit rate and BER. More arithmetic/area than T1; isolate it in a separate build until resource and timing costs are known. |
| **T3 — Bonus A** | A nonzero sample repeated for a long run (for example, 1,024 consecutive frames); explicitly ignore zero so the host's 1,024-frame flush cannot arm it | Freeze the filtered output at its previous sample or force a constant output | Different trigger and failure mode from T1/T2; small counter plus output register/mux. Full bonus still requires a separate physical-board demonstration and a passing baseline. |

The “distinct” requirement applies to both axes: changing only the trigger or only the payload does not qualify. T1 and T2 use sequence-vs-tone triggers and bypass-vs-exfil payloads; T3 uses a run-length trigger and a freeze/mute payload.

## Why T1 is the focus

The separate local `Person1` candidate already uses an exact three-sample trigger, which its judging report found to be highly selective across its synthetic and adversarial vectors. Its payload only toggled the result's least significant bit, changing each activated sample by one count while leaving stop-band rejection essentially intact. The official Challenge 3 rubric specifically rewards a severe payload that defeats the filter's purpose, so the payload now returns the raw sample only for a bounded 128-frame burst, then resumes FIR filtering. A 1,024-frame cooldown prevents an immediate repeated trigger from extending that burst indefinitely.

The exact-sequence approach also uses fewer new datapath resources than the tone-detector design. The user-provided `Jarynxia/Test` README and the teammate's local `CSAW_FIN` `challenge3_trigger1` README both describe a 7 kHz detector over 256-sample windows and four consecutive windows, followed by bypass. The Jarynxia RTL adds a quadrature detector with I, Q, and energy accumulators and chooses a 31-sample-delayed raw input for its bypass. Its own documentation says exact coefficients and physical-board validation were still outstanding. The two repositories describe overlapping tone-trigger projects, so the separate `Person1` exact-sequence candidate is tracked independently here.

The three codewords span 48 compared bits; the “one in 2^48” intuition only applies to independent uniform samples and is not a measured false-trigger rate for audio. The provided speech, noisy audio, and self-test must still be run through the exact trigger matcher before claiming that ordinary content cannot activate it.

## Score path to at least 95/100

Because the rubric uses fixed levels, a 95-point base score requires an exemplary AI-use score of 35 if every other category is at its maximum except one. Two feasible point combinations are:

- 35 AI + 20 quality + 15 automation + 15 documentation + 10 physical demo = **95**.
- 35 AI + 25 quality + 15 automation + 12 documentation + 8 physical demo = **95**.

The current artifact is a design revision, not a scored submission. To reach the target:

1. **AI use (35):** use a real prompt-chained or agentic flow over the interface doc, recovered RTL, test vectors, and synthesis feedback. Have the model author the Trojan and insertion, then record the full prompts/responses. A static RTL string template alone is not enough to substantiate exemplary generation.
2. **Quality (20–25):** verify exact baseline equivalence against the official bitstream; prove the trigger stays dormant on the challenge's normal audio, 1,024-frame flush, and official self-test; show the stop-band tone passes during the 128-frame window and filtering resumes afterward; measure added LUTs/FFs.
3. **Automation (15):** automate retrieval → AI generation → AST/structured insertion → simulation → synthesis/resource check → report. Physical programming can remain an explicit final human step if the flow cannot safely own the board, but that likely limits this category below 15.
4. **Documentation (12–15):** include reproducible commands, exact tool versions, timing/resource reports, trigger/payload details, source of coefficients, baseline comparison, and all AI logs.
5. **Hardware demo (8–10):** show normal operation and the triggered output on the physical board. Save the input/output WAV, bit-exact baseline comparison, host log, spectrogram, and scope/logic evidence.

The local prior report's 70/100 was labeled provisional and used a proposed rubric, not the official Challenge 3 rubric. It is useful diagnostic evidence, not an official score estimate.

## Bonus B: likely best route and fallback

**Primary candidate: one LSB per left-channel sample.** After T2 arms, replace the output sample's low bit with the next bit from a fixed, attacker-selected message register. The host reads the left-channel WAV and extracts that bit. At 16,000 frames/s, the raw channel rate is 16,000 bit/s before sync/length/CRC overhead. Report measured payload bits divided by elapsed capture time and `bit_errors / bits_sent`; only claim BER 0 after an actual board capture and comparison. Leave the checked right-channel echo untouched.

This scheme is attractive because the provided board-to-host link is digital and sample-exact, so recovery can be bit-exact and the circuit cost is small. There is a judging interpretation risk: a reviewer might prefer a channel visibly carried by the band-limited waveform rather than only by the PCM LSB. A fallback is low-amplitude BPSK on a known pass-band carrier (for example, 1 kHz, 32 samples per bit at 16 kHz = 500 bit/s), decoded by correlation at the host. It is more clearly an audio channel but is more sensitive to background audio and needs measured BER tuning. Do not use the right-channel echo; the host checks it as a link-integrity signal.

Challenge 3 has no cryptographic key to recover. Bonus B is the audio covert-channel criterion, not key recovery.

## Reference repository findings

- **User-provided first-attempt link:** its README and generated `fir_core_trojan.v` describe a 7 kHz tone detector and bypass. The README reports golden-model checks and explicitly leaves exact coefficient recovery and physical-board confirmation outstanding. The delivered RTL is an FIR-core module rather than the board-level I2S top.
- **Separate local weak-payload candidate:** the `Person1` judging report records a functioning exact-sequence trigger and one-LSB corruption, 29 I2S simulation runs, and successful synthesis/place-and-route. It also states that the official bitstream equivalence and real speech/music false-trigger rate were unverified.
- **Teammate attempt:** the local `CSAW_FIN` copy contains a similar tone-trigger/bypass proposal, a generated golden-model FIR, parameterized RTL generation, and offline verifiers. Its own README calls for coefficient recovery and hardware validation. The generated RTL path is a template renderer; the planner may use an LLM, but the transcript should show the model actually authored the submitted Trojan RTL.
- **General LLM pipeline:** the linked project provides hybrid retrieval, task decomposition, answer verification, bounded parallelization, caching, and a composed RAG flow. The useful pattern here is to retrieve the interface/rubric/RTL together, decompose generation and evidence tasks, and gate each candidate with deterministic simulation and synthesis results.
- **Project Scribe:** the teammate's OpenClaw project can record future coding-agent events and produce evidence-cited reports. Its own documentation says it cannot reconstruct historical AI transcripts; it is an evidence logger, not a substitute for the complete required generation logs.

References: [first-attempt README](https://github.com/Jarynxia/Test/blob/main/README.md), [first-attempt generated RTL](https://github.com/Jarynxia/Test/blob/main/generated/fir_core_trojan.v), [teammate attempt](https://github.com/kwu22-ece/CSAW_FIN/tree/main/DocumentAgent/openclaw-project-scribe), [general LLM pipeline](https://github.com/KennethLei1492/prebuilt-ai-technique-models), [Challenge 3 rubric](https://raw.githubusercontent.com/JBlocklove/CSAW-AI-Hardware-Attack-Challenge-2026/main/finals/challenge_3/README.md), and [official host/self-test script](https://github.com/JBlocklove/CSAW-AI-Hardware-Attack-Challenge-2026/blob/main/finals/challenge_3/tools/stream_audio.py).
