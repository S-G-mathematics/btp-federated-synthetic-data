# Scientific figures

Run `python scripts/reproduce_repository.py --figures` in the pinned environment. It rebuilds the 15 saved-result PNG panels with the original report builder and regenerates PNG/PDF/SVG versions of the three headline Adult/Bank paired-difference figures from their canonical author CSVs. The Bank labels use real line breaks. The outputs are in `figures/main/`; the dated editorial originals and captions remain in `AUTHOR_READY/PAPER_FIGURES/`.

The plotted bars are saved-result slice means, not independent-cohort confidence intervals. The dashed line is the registered -0.005 practical margin. No new fitting or official-test selection occurs.
