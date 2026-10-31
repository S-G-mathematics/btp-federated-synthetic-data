# Primary sources and implementation status

- UCI Adult: https://archive.ics.uci.edu/dataset/2/adult ; DOI https://doi.org/10.24432/C5XW20 ; official archive https://archive.ics.uci.edu/static/public/2/adult.zip ; CC BY 4.0. Raw archive and all included originals are hashed.
- Fed-TGAN: https://arxiv.org/abs/2108.07927 ; similarity-aware **parameter aggregation**, not the same as weighting independently released distributions.
- FedTabDiff: https://arxiv.org/abs/2401.06263 ; neural parameter-averaging prior art, excluded from our non-neural generator implementation.
- FedGMM: https://proceedings.mlr.press/v202/wu23z.html ; shared latent density/predictor components and learned personal mixture proportions; not simply client-index weights.
- FedEM: https://arxiv.org/abs/2108.10252 ; EM personalized component weights.
- Multiple-source adaptation: https://arxiv.org/abs/1805.08727 ; density-sensitive prediction prior art.
- FedGO: https://proceedings.mlr.press/v267/jang25b.html ; learned density-sensitive prediction weighting, not our claimed invention.
- Stacking/pseudo-BMA/BMA distinctions: Yao et al. https://doi.org/10.1214/17-BA1091 ; author PDF https://sites.stat.columbia.edu/gelman/research/published/stacking.pdf . Our fixed fitted-model evidence score is labeled a conditional predictive-evidence comparator, not integrated model training evidence.
- Entropy balancing: Hainmueller https://doi.org/10.1093/pan/mpr025 ; author PDF https://www.mit.edu/~jhainm/Paper/eb.pdf . Original problem reweights observations; generator-weight adaptation is explicitly an adaptation.
- Kernel mean matching: Huang et al. https://papers.nips.cc/paper_files/paper/2006/hash/a2186aa7c086b46ad4e8bf81e2a3a19b-Abstract.html . Here we calibrate generator-level kernel mean embeddings rather than claiming a faithful row-level reproduction.
- Agnostic FL: https://proceedings.mlr.press/v97/mohri19a.html . Our robust-query calibration uses a different generator-reconstruction uncertainty objective; it is not a reproduction of predictive AFL.
- Logarithmic pooling: Heskes https://proceedings.neurips.cc/paper_files/paper/1997/hash/59f51fd6937412b7e56ded1ea2470c25-Abstract.html . Current implementation is finite candidate support restricted.
- Transport barycenters: Agueh & Carlier https://doi.org/10.1137/100805741 ; author PDF https://www.ceremade.dauphine.fr/~carlier/AC_bary_Aug11_10.pdf . Current implementation is finite empirical entropic transport with a declared mixed-feature cost.
- Private-PGM: https://proceedings.mlr.press/v97/mckenna19a.html ; AIM https://arxiv.org/abs/2201.12677 ; FLAIM https://arxiv.org/abs/2310.03447 ; HeteroFedSyn https://arxiv.org/abs/2603.08832 . Measurement-based private fitting, workload awareness and heterogeneity correction are prior art.
- DP foundations: https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf ; mechanisms, postprocessing and composition in our baseline are standard mathematics, not novelty claims.

Audit exact equations, assumptions, publication versions and released code before writing the final related-work section. No model here is labeled a faithful reproduction of a neural paper merely because a related weighting idea is adapted.
