# References

Assembled from the literature survey run for this project. Every entry was returned with
a venue and a DOI or stable URL; entries are grouped by the role they play in the paper so
that the citation keys used in the draft resolve unambiguously.

## A. Paediatric EEG brain age (Section 4, "Paediatric EEG brain age")

[A1] R. Iyer, L. Roberts, M. Waak, S. Vanhatalo, N. J. Stevenson et al.,
"Functional brain age in the paediatric population," *eBioMedicine*, vol. 102, 105061, 2024.
doi:10.1016/j.ebiom.2024.105061. PMID 38537603.
*n = 1056, 1 month to 18 years, 18-channel sleep EEG, ResNet, weighted MAE 0.85 y.*

[A2] "Decoding brain age from sleep EEG," *Scientific Reports*, vol. 15, 2025.
doi:10.1038/s41598-025-25482-7.
*Overnight sleep EEG, 0-18 y, ResNet; MAE 0.78 y (0-2 y), 0.87 y (2-12 y), 1.55 y (12-18 y).*

[A3] Ju, Zhao, Gao et al., "EEG-based brain age prediction in children with and without
autism," *Frontiers in Neurology*, vol. 16, 1605291, 2025.
doi:10.3389/fneur.2025.1605291.
*n = 659 typically developing (772 recordings) + 98 ASD, 3-14 y, resting EEG, GRU with a
trainable filterbank; MAE 1.31 y. The closest published comparator to our cohort, and the
source of the +0.76 y ASD brain-age gap cited in Section 4.*

[A4] "EEG brain age in infants and toddlers," 2025. PMC11732522; preprint
medRxiv 2024.05.31.24308275.
*938 recordings / 457 infants, 2-38 months, aperiodic and periodic spectral features, MLP;
R-squared 0.83, MAE 91.7 days.*

[A5] "EEG estimates brain age in infants with high precision," *NeuroImage*, 2025.
doi:10.1016/j.neuroimage.2025.121140.
*n = 219, 3-14 months, short awake EEG, MAE about 1.2 months.*

[A6] D. A. Engemann, A. Mellot, R. Hoechenberger, H. Banville, D. Sabbagh, L. Gemein,
T. Ball and A. Gramfort, "A reusable benchmark of brain-age prediction from M/EEG
resting-state signals," *NeuroImage*, vol. 262, 119521, 2022.
doi:10.1016/j.neuroimage.2022.119521.
*The methodological reference for how to benchmark brain age; source of the practice of
reporting error normalised by target dispersion, which Section 4 adopts.*

[A7] "Machine learning for EEG-based brain age: a structured review," *Algorithms*, 2026.
doi:10.3390/a19010091. *21 studies since 2015.*

## B. Brain-age gap as a biomarker, and its critique (Sections 4 and 5.3)

[B1] "Brain age gap in severe-to-profound hearing loss," *Ear and Hearing*, 2026.
doi:10.1097/AUD.0000000000001824. PMID 41992392.
*MRI, adults; gap +5.86 +/- 8.94 y. The closest existing work to a deprivation brain-age
question, and adult and MRI-based rather than paediatric and EEG-based.*

[B2] "Brain age in mild-to-moderate age-related hearing loss: a null result," PMC12172823.

[B3] "Clinically altered brain activity may not look like aged brain activity:
implications for brain-age modeling," PMC13536007. PMID 42688976.
*The critique our Section 3.6 instantiates: EEG brain-age models can behave unexpectedly
in clinical groups, and gap-based inference can mislead.*

[B4] "Source-space EEG alpha brain age in MCI and dementia," PMC13226700.

## C. Non-evoked EEG markers under auditory deprivation (Section 1.3, Section 5.2)

[C1] "EEG in hard-of-hearing schoolchildren: elevated normalised delta and theta power and
reduced dominant rhythm frequency," *Neurophysiology* (Springer).
doi:10.1007/s11062-008-9022-7. See also PMID 29975829.

[C2] "Resting-state network topology in prelingually deaf children with late cochlear
implantation," *Frontiers in Pediatrics*, vol. 10, 909069, 2022. PMC9487891.
*Higher theta-band auditory-visual phase-lag index, reduced global efficiency in theta and
alpha.*

[C3] Mao, Lu, Jiang, Hu et al., "Aperiodic spectral exponent and hearing loss,"
*NeuroImage*, 2025. PMID 40976491.
*Adults; reduced central-parietal spectral exponent in bilateral hearing loss, increasing
with duration. No paediatric equivalent exists, which is why Section 3.4's ablation over
log-variance and low-frequency power is descriptive rather than confirmatory.*

[C4] "Normative aperiodic development, 2-44 months," *Nature Communications*, 2024.
doi:10.1038/s41467-024-50204-4.

[C5] "Alpha activity in congenitally hearing-impaired children," *Brain Communications*,
vol. 7, no. 2, fcaf150, 2025.

[C6] A. Sharma et al., *Frontiers in Neuroscience*, vol. 13, 469, 2019.
*Cited only to name the evoked-response and P1-latency paradigm this study deliberately
does not use (Section 1.3).*

## D. Information-theoretic tools and their limits (Sections 2.5, 4)

[D1] A. van den Oord, Y. Li and O. Vinyals, "Representation learning with contrastive
predictive coding," arXiv:1807.03748, 2018.
*The InfoNCE bound. Cited as the standard variational lower bound, and as the objective
family our relative-positioning arm belongs to.*

[D2] B. Poole, S. Ozair, A. van den Oord, A. A. Alemi and G. Tucker, "On variational
bounds of mutual information," *ICML*, 2019.
*Sample-complexity and variance limits of variational MI bounds. One of the two reasons
our information readout is an operational cross-entropy difference rather than a
point MI estimate.*

[D3] J. Song and S. Ermon, "Understanding the limitations of variational mutual
information estimators," *ICLR*, 2020. arXiv:1910.06222. *The second reason.*

[D4] M. I. Belghazi et al., "MINE: Mutual information neural estimation," *ICML*, 2018.
arXiv:1801.04062.

[D5] A. Kraskov, H. Stoegbauer and P. Grassberger, "Estimating mutual information,"
*Physical Review E*, vol. 69, 066138, 2004. doi:10.1103/PhysRevE.69.066138.

[D6] "Information capacity of EEG: theoretical and computational limits of recoverable
neural information," arXiv:2510.17841, 2025.
*The simulation-based claim that recoverable information saturates around 64-128
electrodes and that linear decoders recover far less than channel capacity. Section 3.1 is,
to our knowledge, the first empirical test of that claim on real paediatric clinical data.*

[D7] "Partial information decomposition and subsystem consistency," arXiv:2510.14864 and
arXiv:2512.16662. *Why PID is not used as a primary quantity here.*

[D8] "EEG CONNECT reporting checklist," *Epilepsia Open*, 2025. doi:10.1002/epi4.70343.

## E. Self-supervised and foundation models for EEG (Sections 3.8, 4)

[E1] H. Banville, O. Chehab, A. Hyvaerinen, D. A. Engemann and A. Gramfort,
"Uncovering the structure of clinical EEG signals with self-supervised learning,"
*Journal of Neural Engineering*, vol. 18, no. 4, 2021. doi:10.1088/1741-2552/abca18.
*The origin of the relative-positioning pretext task used in Section 3.8, and the reason
we chose a within-recording task in the first place.*

[E2] "LaBraM: Large brain model for learning generic representations," *ICLR*, 2024.

[E3] "EEGPT: Pretrained transformer for universal and reliable representation of EEG
signals," *NeurIPS*, 2024.

[E4] "CBraMod: A criss-cross brain foundation model for EEG decoding," *ICLR*, 2025.
arXiv:2412.07236.

[E5] "REVE: Representation learning for EEG across arbitrary electrode setups,"
*NeurIPS*, 2025. arXiv:2510.21585.
*The montage-agnostic approach; relevant to our two-montage transfer in Section 3.5.*

[E6] Kuruppu et al., "A review of EEG foundation models," *Journal of Neural Engineering*,
vol. 23, no. 2, 2026. doi:10.1088/1741-2552/ae4455.
*Ten models reviewed; evaluation largely in-distribution, scaling unproven, and no
systematic paediatric validation.*

[E7] "What EEG foundation models encode: dataset identity and a negative-control suite,"
arXiv:2607.24519.
*Embeddings can encode recording-site identity. The concrete reason Section 3.8 rejects a
cross-recording contrastive objective for this corpus.*

[E8] Benchmarks: EEG-FM-Bench (arXiv:2508.17742), AdaBrain-Bench (arXiv:2507.09882),
EEG-FM-Compass (arXiv:2601.17883), Brain4FMs (arXiv:2602.11558), EEG-Bench
(arXiv:2512.08959).

## F. Venue fit (Section 4, and the choice of validation standard)

[F1] Qian, Wang, Kakkos, ... Sun, "FBCPM: Filter bank connectome-based prediction modeling
for EEG," *IEEE JBHI*, 2025. *Four independent datasets, 280 subjects.*

[F2] Gallego-Vinaras, Mira-Tomas et al., "Alzheimer's disease detection in EEG sleep
signals," *IEEE JBHI*, 2025. *JBHI Best Paper, February 2025.*

[F3] "EEG-X: An integrated framework for automated quantitative EEG analysis in epilepsy
diagnosis," *IEEE JBHI*, 2026. doi:10.1109/JBHI.2026.3715842. PMID 42479527.

[F4] "Dual-branch self-supervised contrastive pre-training for sleep stage
classification," *IEEE JBHI*, 2025. PMID 41191470.

[F5] "DSleepNet: disentanglement learning for attribute-agnostic sleep staging,"
*IEEE JBHI*, 2025.

---

## Verification status

These entries come from a literature survey conducted with web search during this project.
**Before submission each one must be opened and checked**: author list, exact title, volume
and page numbers, and that the DOI resolves. Several entries above carry a venue and
identifier but an abbreviated or reconstructed title, and are marked by the absence of a
full author list. That check is a submission blocker and has not been done.
