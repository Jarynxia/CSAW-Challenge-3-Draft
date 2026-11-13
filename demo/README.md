# T1 hardware evidence checklist

No physical-board evidence has been captured for this draft.

For the final demo, keep the following in this folder:

1. `t1_trigger.wav` from `tb/make_t1_wav.py`.
2. The output WAV captured with the official Challenge 3 `stream_audio.py` after programming `fir_audio_top_t1.v`.
3. A run using the provided normal/noisy audio through both the original bitstream and T1 build, plus the exact byte-for-byte comparison result.
4. A spectrogram showing the normal 440 Hz segment passed by both designs, the 4.8 kHz tone passes for 127 samples after the trigger-completing sample, then FIR rejection resumes.
5. A host log showing frame count, link echo status, and capture rate.
6. A logic analyzer/oscilloscope capture of `ICE_LED` or the relevant output pin during the trigger/output interval.

Record the board revision, bitstream hash, build tool versions, sample rate, BCLK rate, and exact commands used. The Challenge 3 scoring sheet gives full demonstration points only for physical-board evidence of both normal operation and the triggered payload.
