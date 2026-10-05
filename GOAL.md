# Open challenge: Ontario wildfires

Build a reproducible wildfire analysis and prediction project for Qiskit Fall Fest using **Agency Reported Wildfires in Canada**, **ECCC Monthly Climate Summaries**, and **NRCan annual forest land cover**. Start with Ontario (`agency_code=ON`) and target **1985–2025**, recording source gaps rather than filling them with invented data. The prediction target and quantum component remain to be selected after the data audit.

1. Download all pages and record source, retrieval time, hashes and coverage.
2. Separate fire identities from status updates. Audit reporting gaps, dates, coordinates and revisions before defining labels.
3. Choose a target the feed can support: reported-fire activity, control-status transitions or reported-size changes. Ignition risk requires exposure/predictor data and justified negative labels; the present feed alone does not supply those.
4. Establish simple classical baselines with chronological holdouts. Use only information available at prediction time; do not use final sizes, extinguishment dates or future revisions as inputs.
5. Test a small, motivated Qiskit component against matched classical controls. Report accuracy, uncertainty and computational cost without assuming quantum advantage.

The operational history begins in 2010; 2026 is incomplete. Suspected Ontario gaps in 2013–2014 require investigation. Missing rows are not evidence of no fire, and blank response categories remain unspecified. The selected fire history cannot supply 1985–2009; annual woodland maps end in 2022. These are explicit source gaps, not zero-fire/zero-vegetation years. CNFDB and other replacement datasets remain outside the input scope until selected. See [source mapping](docs/DATA_SCHEMA.md).

The fly/connectome experiment and explorer have been retired and deleted. SQD teaching material and independent quantum-model utilities remain reusable resources, not additional challenge deliverables.
