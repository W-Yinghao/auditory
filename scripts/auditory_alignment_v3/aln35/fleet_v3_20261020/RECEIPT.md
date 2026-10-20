# Fleet v3 handover receipt (Claude Code, 2026-10-20)

User request: "你看看后续有没有要提交的GPU task，我现在看到服务器上没啥排队的了".

## Finding (09:35 CEST)

- 6/10 project runfill GPUs running, 0 pending. Remaining registered work: DTU budget 54/150,
  DTU curves 225/440, breadth budget 16/75, breadth curves ~101/300; no failure markers.
- Every remaining lane was at its slot limit (1+1+2+2 = 6), so fleet v2 had nothing to submit.
  DTU budget/curves slots (1) are hard-coded in `aln34/maintain_fleet_v14.CONFIG`; `fleet_runtime.json`
  can only change `breadth_*` lanes.
- Last-6 h completion rate: DTU budget 4 (1 worker), DTU curves 22 (1 A30 worker), breadth budget 8,
  breadth curves 52 (2 workers each). The DTU lanes were the bottleneck (~60–80 h at one worker).

## Safety of more DTU workers

- `aln34/priority_rotation_worker.py` claims each unit with a per-unit `flock`; the same worker and claim
  path already ran the breadth lanes at 2 workers (Codex check, CODEX_HANDOFF §0.26) with 0 failures.
- `data_inner.py` / `learning_budget_v2.py` differ from their breadth twins (`breadth_inner.py` /
  `breadth_budget.py`) only in dataset, plan and family names; outputs/checkpoints are per experiment id
  with tmp+replace writes. No shared refresh like the matched lane's `selection_policy.refresh()`.
- Budget/curves have no V100 receipt, so routing stays on A100/L40S/A40/A30.

## Change (operational only)

`aln35/maintain_fleet_v3.py` imports v2 unchanged and keeps the same lock, journal, routing, V100 and
pending-fallback logic. Differences:

1. DTU budget/curves base slots 3; breadth lanes keep their runtime slots (2).
2. Base slots of all lanes are filled before any lane uses extended slots (DTU budget/curves up to 6),
   so the DTU tails absorb capacity only after breadth work no longer needs it.
3. Cap counts project runfill GPUs running **plus pending** (v2's launch path only asserted running).
4. A lane never holds more workers than unfinished units (avoids empty rotations at the tail).
5. Renewal submits `slurm/aln35_maintain_fleet_v3.sbatch` under state key `renewal_v3`; stop marker
   `aln35/STOP_fleet_maintenance_v3`.

No scientific source, plan, row, hold, checkpoint or running job was edited or cancelled.

## Check

Normal-QoS count was 28 (>27, mostly other projects), so no new CPU batch was submitted for the check;
it ran as a short `srun --overlap` step inside evidence allocation 1047358.
Receipt `check_1047358.json`: v2 SHA unchanged (`311bcc8b…`), v3 SHA `907167c2…`; synthetic tier/cap tests
and 2,000 randomized states never exceeded 10; live no-submit dry run would add 2 budget + 2 curves
workers (6 → 10).

## Handover

- 09:42:00 wrote `aln35/STOP_fleet_maintenance_v2` (v2 exits at its next loop check, releasing the lock).
- 09:42:39 job 1050940 absent from squeue (log `STOP ALN35 v2`; node clock skew makes its stamp read 09:40:49).
  Lock `aln34/.fleet_maintenance.lock` verified free; normal-QoS count 27 (≤27) before submission.
- **Fleet v3 = job 1051045** (`c3_aln35keep3`, CPU normal, 4-day limit, log `aln35/fleet.log`).
  First pass 09:44:15 submitted budget 1051049/1051051 and curves 1051050/1051052; all four started on A100
  within a minute and claimed distinct units (budget 2d79ba22…, e567cbc9…; curves d6950440…, 5a273306…),
  distinct from 1050924 (budget f1a83e85…) and long A30 worker 1044076 (curves b1898856…), which uses the
  same `data_inner_v1/claims/<id>.lock` files.
- Second heartbeat 09:45:36: committed 10, pending 0, no further submission.
- To stop v3: create `aln35/STOP_fleet_maintenance_v3`. `STOP_fleet_maintenance_v2` must stay in place
  while v3 runs (otherwise a later v2 start would contend for the lock and fail).
