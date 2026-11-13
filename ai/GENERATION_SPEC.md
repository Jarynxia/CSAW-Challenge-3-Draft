# T1 bounded-payload revision specification

This iteration responds to judge feedback that a permanent bypass is conspicuous and degrades normal filtering after activation.

> Preserve the existing FIR, I2S deserializer/serializer, output timing, rounding/saturation behavior, echo path, and dormant behavior. Use the exact three-sample left-channel trigger 16'h5A3C, 16'hC3A5, 16'h96E1. When the final word is received, return the raw input sample at MAC completion for exactly 128 consecutive left-channel frames, counting the trigger-completing frame as frame one. On the next frame, resume the rounded/saturated FIR result. Ignore trigger input during the pulse. Then hold the matcher in idle for a 1,024-frame cooldown before allowing another trigger. Preserve the existing two-frame transport latency and right-channel echo. Generate a pin-level testbench/oracle that checks dormant behavior, trigger and near misses, exact pulse length, stop-band recovery, ignored retrigger during cooldown, successful re-arm after cooldown, right-channel isolation, the 1,024-zero host flush, and official seeded self-test traffic.

At 16 kframes/s, the pulse is 8 ms and the lockout is 64 ms. These times scale with the host frame rate. The pulse is intentionally finite: this revision must not leave the output bypassed after the trigger.

The initial iteration latched activation permanently; that version is superseded by the bounded pulse and cooldown in rtl/fir_audio_top_t1.v. No simulation or physical-board result is claimed until the included checks are run.