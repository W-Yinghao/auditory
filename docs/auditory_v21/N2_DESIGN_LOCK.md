> GitHub发布副本：本轮验收后，用户明确要求发布代码与聚合结果。文内“未发布／未push”及早期进行中表述是历史状态；当前以v2.1最终科学报告和final_001为准。个体数据、预测、模型与详细日志仍在服务器。见[发布范围](../../PUBLICATION.md)。

# N2 v2.1 design lock

This lock defines the bounded metadata-only N2 design. It is a new exploratory
design and does not modify or reinterpret the frozen v2 N2 result.

## Inputs and scope

The implementation reads the immutable `full_event_history.parquet` from the
support freeze. It retains the complete event ledger while selecting source
rows with the saved accepted, boundary-eligible, binary class, and half
metadata. It does not read EEG arrays, model outputs, clinical fields, or
effect estimates. The saved legacy k=8 bag file is read separately only to
materialize the original H_BAG metadata ablation input; it is never changed.

The new-design cohort is restricted to candidate identifiers present in the
immutable old saved k=8 bags. That old-bag candidate set is crossed with both
halves; candidates outside it in the complete history are excluded from this
new cohort. Missing support remains in the denominator and is reported as
missing.

## Matched bag rule

For each candidate and half, compute the exact intersection of
`previous_code × previous_run_bin` cells observed in class 0 and class 1.
Every intersection cell is assessed. A cell is not removed after inspecting
coverage or an effect. Each class draws independently within the same exact
cell, without replacement, using a deterministic SHA-256 trial order.

The two classes receive the same number of bags for every eligible exact cell,
equal to the smaller feasible count produced by the two class pools. A
candidate-half is retained only when every eligible common cell yields at least
one paired bag and the total reaches the fixed minimum of two paired bags per
class/half. Common cells below the predeclared support threshold are recorded
as fixed exclusions. The halves remain separate. Physical block identity is
retained on every member and checked in every bag.

Every bag has k=8 members, spans at least two physical blocks, and has no more
than four members from one physical block. A common exact cell is eligible
only when both classes have at least 16 eligible trials and at least three
physical source blocks. Bags are formed within a common record/segment pair,
so a bag never combines those physical streams. The resulting matched bag set
has equal class budgets and unique trial membership within each class.

All remaining eligible common cells participate. If no eligible common cell
exists, or an eligible cell cannot satisfy the fixed bag/block rule, the
candidate-half is not retained. A candidate enters the real-design scope only
when both halves are retained. The output status is
`OBSERVATIONAL_SUPPORT_LIMITED` when that full candidate support is absent.
This is a necessary-support result: imbalance in the old saved bags does not
establish that a newly constructed balanced bag design is impossible.

## Outputs and audit evidence

Identifier-bearing matched bags, candidate-half detail, exact-cell detail,
original H_BAG metadata, and the 25-row diagnostic catalog stay private. The
public aggregate records candidate, candidate-half, class, bag, and trial
denominators/numerators, quota checks, input SHA-256 evidence, and the support
status. No individual rows are published.

The design manifest freezes 16 H_BAG columns, required MU and VAR dimensions
of 8 each, k=8, no replacement, separated halves, two paired bags per
class/half, 16 eligible trials per class/cell, three source blocks, and the
four-members-per-block limit. The deterministic design seed is 21201.

## Metadata diagnostic plan

The original saved bags are summarized into the frozen H_BAG metadata columns.
The diagnostic has exactly 25 heads: five old outer folds crossed with five
views. The views are `all_metadata`, `history`, `gap`, `position`, and
`block_span`. Each head uses candidate-equal training weights, a transform fit
on outer-training identities only, one low-complexity logistic regression
specification with L2 lambda 0.01 and a 200-iteration budget, and raw fixed-OOF
candidate-cluster bootstrap CE/bAcc. There is no calibration, view selection,
or strong-column deletion. Predictions and fit receipts remain private. This
metadata diagnostic does not alter the old N2 primary comparison.
