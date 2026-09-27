# G0 metadata refinement

Temporal calibration/test roles now use the complete preceding-run dependency from S1_support_004. Dependencies may cross internal blocks on the same temporal side; none may cross the calibration/test boundary. Whole-record offline QC selection is shared, so numerical dependency isolation does not imply selection isolation.

The offline bridge uses the exact common event intersection after both QC masks. Expected edge omissions do not make a record incomparable. Every shared event must match original event ordinal, sample and code. This supersedes the provisional G0_001 rule requiring all causal accepted trials to be present offline. Old metric reproduction, original supervised-head diagnostics and spatial algebra checks remain referenced without refitting.
