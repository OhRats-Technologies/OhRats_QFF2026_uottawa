"""Create the sprint report with bundled or uv-provided ReportLab; no credential access."""

import argparse, base64, io, json, re, ast
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

REPO = Path(__file__).resolve().parents[1]
INK = colors.HexColor("#182d32")
TEAL = colors.HexColor("#107d73")
VIOLET = colors.HexColor("#7044bd")
PAPER = colors.HexColor("#f5f3eb")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=REPO / "docs/OVERNIGHT_REPORT.pdf"
    )
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    now = datetime.now(ZoneInfo("America/Toronto"))
    root = REPO / "artifacts/sprint-20261003"

    def read(folder, name="metrics.json"):
        return json.loads((root / folder / name).read_text())

    fly = read("flywalk")
    atlas = read("atlas")
    stats = read("statistics", "summary.json")
    ev = read("evidence", "summary.json")
    placements = read("phaseguard", "placements.json")
    thermal = read("spintherm") if (root / "spintherm/metrics.json").exists() else None
    active = (
        read("activebudget") if (root / "activebudget/metrics.json").exists() else None
    )
    active_noise = (
        read("activenoise") if (root / "activenoise/metrics.json").exists() else None
    )
    shield = read("spinshield") if (root / "spinshield/metrics.json").exists() else None
    flux = read("flyflux") if (root / "flyflux/metrics.json").exists() else None
    strength = (
        read("strengthnull") if (root / "strengthnull/metrics.json").exists() else None
    )
    html = (REPO / "demo/index.html").read_text()
    data = json.loads(
        re.search(
            r'<script id="experiment-data" type="application/json">(.*?)</script>',
            html,
            re.S,
        ).group(1)
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleOh",
            fontName="Helvetica-Bold",
            fontSize=32,
            leading=35,
            textColor=INK,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionOh",
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=27,
            textColor=INK,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubOh",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=TEAL,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyOh",
            fontName="Helvetica",
            fontSize=10,
            leading=14.5,
            textColor=INK,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallOh",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#536769"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableOh",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EyebrowOh",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=TEAL,
            spaceAfter=8,
        )
    )
    story = []

    def p(text, style="BodyOh"):
        story.append(Paragraph(text, styles[style]))

    def heading(track, title):
        p(track.upper(), "EyebrowOh")
        p(title, "SectionOh")

    def table(headers, rows, widths=None):
        cells = [
            [Paragraph(escape(str(v)), styles["TableOh"]) for v in row]
            for row in [headers] + rows
        ]
        t = Table(
            cells,
            colWidths=widths or [512 / len(headers)] * len(headers),
            repeatRows=1,
            hAlign="LEFT",
        )
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), PAPER),
                    ("TEXTCOLOR", (0, 0), (-1, 0), TEAL),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5ded7")),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 10))

    def figure(key, height, caption):
        blob = base64.b64decode(data["pictures"][key].split(",", 1)[1])
        w, h = ImageReader(io.BytesIO(blob)).getSize()
        width = min(512, height * w / h)
        actual_height = width * h / w
        img = Image(io.BytesIO(blob), width=width, height=actual_height)
        img.hAlign = "CENTER"
        story.append(img)
        p(caption, "SmallOh")

    def page():
        story.append(PageBreak())

    checks = sum(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name.startswith("test_")
        for path in (REPO / "tests").glob("test_*.py")
        for n in ast.walk(ast.parse(path.read_text()))
    )
    collected = sum(r["status"] == "COLLECTED" for r in ev["hardware_status"])
    p("OHRATS TECHNOLOGIES / QISKIT FALL FEST 2026", "EyebrowOh")
    p("Quantum Reality Lab", "TitleOh")
    p(
        "Feasible ideas, tested controls, and a portfolio that keeps its negative results.",
        "SubOh",
    )
    p(
        ("Final sprint report" if args.final else "Working report snapshot")
        + " - "
        + f"{now.day} {now:%B %Y, %H:%M} Toronto",
        "SmallOh",
    )
    p(
        "<b>Recommendation:</b> lead with <b>SpinShield / SpinWeave</b> for materials. Its witness challenge, independently checked magnet, thermal controls and explicit uncertainty assumptions make a focused submission. <b>EigenBudget</b> is the chemistry alternative: a failed allocator, an explanation, a paid-pilot crossover, and a noise audit that limits the gain. Keep PhaseGuard as the sustainability alternative and FlyWalk as the playful real-data showpiece."
    )
    table(
        ["Candidate", "Track", "Editorial potential / 5"],
        [
            ["SpinWeave / thermal / confidence", "Materials", "4.30"],
            ["EigenBudget", "Chemistry", "4.23"],
            ["GridGuard + PhaseGuard", "Sustainability", "4.18"],
            ["FlyWalk + noise/atlas", "Exploratory", "3.78"],
            ["KernelForge", "QML", "3.75"],
        ],
        widths=[225, 145, 142],
    )
    p(
        "Ratings weigh fit 25%, distinctiveness 25%, demo quality 20%, evidence 20%, and feasibility 10%. They are subjective submission-quality scores, not winning probabilities or an official judging rubric. Small differences should not drive the decision.",
        "SmallOh",
    )
    p(
        "<b>What is complete:</b> real pinned fly data, focused track experiments, an offline interactive demo, raw sample tables, source/evidence hashes, and "
        + str(checks)
        + " scientific checks. The implementation uses uv and Python 3.12; no Conda."
    )
    p(
        f"<b>Hardware:</b> {collected}/3 jobs collected at this snapshot. Three bounded jobs contain fourteen circuits at 1024 shots each. Returned device counts are published separately from local forecasts. The spin-ring energy is -1.8652 J; its fixed one-sided sampling upper is -1.7327 J, below the separable bound -1 under the stated measurement assumptions."
    )
    p(
        "<b>Novelty:</b> none of these established algorithms is presented as a new quantum algorithm. The contribution is the precise, reproducible experiment, a useful failure analysis, and an accessible demo. All testbeds are small enough to simulate classically; no computational advantage is claimed."
    )
    p(
        "<b>Deadline:</b> implementation stops at 05:50 Toronto; report polish completes by 06:00 on 3 October 2026. The owner requested roughly 30% fly work and 70% other tracks. Timed stages record compute runtime; they do not measure total development effort.",
        "SmallOh",
    )
    page()
    heading("Real connectivity / 3 qubits", "FlyWalk: one graph, two dynamics")
    p(
        'Eight visual-system cell-type populations come from the MaleCNS v1.0 cell-type explorer. Selection is deterministic: Mi1_R and its seven strongest downstream groups by total contacts. Directed counts are retained; models use symmetrized weights and exclude self-loops. The pinned source commit is <font name="Courier">789cc6c105798ce2fd70ba85dab394f90899616b</font>.'
    )
    p(
        "Classical diffusion uses exp(-tL); the quantum walk uses exp(-itL). Both use the same normalized graph Laplacian and initial basis state. A lesion disconnects one population while retaining the intact time scale."
    )
    figure(
        "atlas",
        300,
        "All eight starting populations, 56 non-source disconnections and 99 shuffled-weight controls. The source CSVs and SHA-256 checks are preserved.",
    )
    table(
        ["Quantity", "Observed result"],
        [
            [
                "Final classical / quantum TV at t=8",
                f"{fly['final_classical_quantum_tv']:.4f}",
            ],
            ["Final ideal-sampling TV, 4096 shots", f"{fly['final_sampling_tv']:.4f}"],
            [
                "All-source time-averaged TV / shuffled mean",
                f"{atlas['observed_mean_tv']:.4f} / {atlas['null_mean_tv']:.4f}",
            ],
        ],
        widths=[350, 162],
    )
    p(
        "These are population nodes, not individual neurons. Symmetrization drops direction and transmitter sign; outside connections are omitted. Time is dimensionless. The shuffled controls preserve edge weights and topology, not node strengths or biological organization. One selected graph does not support population inference, biological quantum computation or fly-behavior claims.",
        "SmallOh",
    )
    p(
        'Sources: <link href="https://male-cns.janelia.org/" color="#107d73">Janelia MaleCNS</link>; <link href="https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/" color="#107d73">Reiser Lab cell-type explorer</link>. Snapshot attribution: CC BY 4.0.',
        "SmallOh",
    )
    if strength:
        page()
        heading("Fly graph / control audit", "A stricter control changes the story")
        p(
            "The first comparison shuffled edge weights across a complete graph and renormalized each graph by its own maximum strength. It preserved the weight multiset, but changed population strengths and the time normalization. A follow-up uses balanced four-edge moves: add delta to ab and cd, subtract it from ac and bd. Every population keeps its total symmetrized weight, and the intact degree matrix and time scale stay fixed."
        )
        figure(
            "strengthnull",
            240,
            "Three finite chains, 99 positive complete weighted alternatives. Each chain uses 5000 burn-in moves and 500 moves between saved graphs. Independent Qiskit checks confirm sampled propagation; all node strengths are preserved to numerical precision.",
        )
        table(
            ["Graph / control family", "Preserved constraint", "Mean walk TV"],
            [
                [
                    "Selected real graph",
                    "Observed reference",
                    f"{strength['observed_mean_classical_quantum_tv']:.4f}",
                ],
                [
                    "Original weight shuffle",
                    "Complete topology, weight multiset",
                    f"{atlas['null_mean_tv']:.4f}",
                ],
                [
                    "Fixed-strength follow-up",
                    "Complete topology, each strength, intact scale",
                    f"{strength['control_mean']:.4f}",
                ],
            ],
            widths=[150, 250, 112],
        )
        p(
            "The selected graph exceeds the first control mean but falls below the fixed-strength control mean. The initial shuffled comparison therefore does not establish unusually contrastive wiring. The two controls answer different questions: preserving every strength requires changing individual edge weights, rather than preserving their multiset."
        )
        p(
            "This was exploratory follow-up after seeing the first result. Finite chain samples are dependent; spanning the fixed-strength subspace and observing similar chain means do not prove convergence or independent uniform draws. Continuous alternatives are mathematical controls, not additional anatomical measurements. Their descriptive ordering is not a biological p-value."
        )
    if flux:
        page()
        heading(
            "Fly graph / direction ablation", "FlyFlux: declared phases, modest effects"
        )
        p(
            "FlyWalk deliberately symmetrizes its directed contact counts. FlyFlux holds those magnitudes fixed and encodes the weighted direction imbalance in phases: theta_ij=(pi/2)*q*(A_ij-A_ji)/(A_ij+A_ji). The generator is [D(W)-W exp(i theta)]/max(degree(W)), with self loops omitted. This is a declared magnetic-graph-inspired model, not a measured neuronal Hamiltonian."
        )
        figure(
            "flyflux",
            340,
            "Charge q=0 recovers FlyWalk. Reversing all directed contacts conjugates the generator and transposes transition probabilities. Independent Qiskit checks confirm the complex spectral implementation.",
        )
        last = flux["comparisons"][-1]
        p(
            f"At q=1, the time/all-source mean forward/reverse total variation is {last['all_source_time_mean_reverse_tv']:.4f}. For Mi1_R at model time 8 it is {last['source0_final_reverse_tv']:.4f}. The effect is modest and depends on the chosen phase encoding. All eight starting populations and three charges are retained; no selection of the most favorable start is presented as an average."
        )
        p(
            "Gauge transformations leave basis-to-basis probabilities unchanged, and phases on a two-node edge cannot create this directional probability effect. Cycles matter. The unitary walk remains reversible; this does not imply reversible neuronal signaling, biological quantum computation, a behavioral prediction or computational advantage."
        )
        p(
            'Sources: <link href="https://arxiv.org/abs/2102.11391" color="#107d73">MagNet magnetic graph encoding</link>; <link href="https://arxiv.org/abs/1208.4049" color="#107d73">Time-reversal control of quantum transport</link>. The bounded weighted-imbalance rule here is a specified modeling choice.',
            "SmallOh",
        )
    fly_returned = [
        r
        for r in ev["physical_metrics"]
        if r["project"] == "FlyWalk" and r["origin"] == "REAL_IBM_HARDWARE"
    ]
    if fly_returned:
        page()
        heading(
            "FlyWalk / returned IBM counts",
            "Four circuits, including a zero-time control",
        )
        p(
            "These are returned device counts from ibm_quebec, not the calibration forecast. Four preselected circuits test zero model time, intact t=4 and t=8, and a disconnected population at t=8. The public snapshot includes allowlisted raw counts and ideal references; private job and service identity remain local."
        )
        table(
            ["Circuit", "Shots", "Observed source probability", "TV from ideal"],
            [
                [
                    r["case"],
                    r["actual_shots"],
                    f"{r['source_return_probability']:.4f}",
                    f"{r['total_variation_from_ideal']:.4f}",
                ]
                for r in fly_returned
            ],
            widths=[170, 65, 155, 122],
        )
        p(
            "The zero-time circuit provides a simple preparation/readout control. The other circuits add the compiled walk. Frequencies and plug-in total variation contain finite-shot error as well as device noise; this table does not isolate a unique noise mechanism or estimate biological dynamics."
        )
        t8 = next(r for r in fly_returned if r["case"] == "intact_t8")
        table(
            ["Population / t=8", "Ideal probability", "Returned frequency"],
            [
                [node, f"{expected:.4f}", f"{observed:.4f}"]
                for node, expected, observed in zip(
                    data["nodes"], t8["expected"], t8["observed"]
                )
            ],
            widths=[220, 146, 146],
        )
        p(
            "Counts assume the recorded measurement-bit ordering. Device drift and correlated errors are not covered by ideal sampling references. Agreement with the mathematical walk would support circuit execution, not quantum processing in a fly brain.",
            "SmallOh",
        )
    if (root / "forecastaudit/metrics.json").exists():
        audit = read("forecastaudit")
        page()
        heading(
            "Returned hardware / forecast control", "A useful forecast can still miss"
        )
        p(
            "A local calibration model was sampled before the returned counts were available. The original forecast used 8192 shots per circuit, while the actual IBM circuits used 1024. Comparing those histograms directly combines model differences with different sampling budgets. This diagnostic adds a shot-matched reference."
        )
        figure(
            "forecastaudit",
            235,
            "Green intervals: central 95% of 4000 multinomial predictions at 1024 shots, conditional on the fixed empirical local forecast. Purple crosses: returned hardware TV from the ideal circuit. These are conditional predictive envelopes, not hardware confidence intervals.",
        )
        table(
            [
                "Circuit",
                "IBM TV / ideal",
                "Forecast TV / ideal",
                "Shot-matched envelope",
            ],
            [
                [
                    r["case"],
                    f"{r['hardware_tv_from_ideal']:.4f}",
                    f"{r['forecast_probability_tv_from_ideal']:.4f}",
                    f"{r['conditional_predictive_95'][0]:.4f}-{r['conditional_predictive_95'][1]:.4f}",
                ]
                for r in audit["rows"]
            ],
            widths=[155, 100, 110, 147],
        )
        p(
            "The zero-time device control is closer to ideal than the forecast, while the evolved cases do not all follow the forecast envelope. A good preparation/readout control cannot certify the accuracy of the deeper walk. This does not identify a unique error mechanism or prove a calibration model is generally invalid."
        )
        p(audit["interpretation"], "SmallOh")
    page()
    heading("Noise / interference", "More shots cannot repair gate noise")
    p(
        "The FlyWalk noise lab separates finite-shot sampling, depolarizing gate noise, symmetric readout error and their combination. Exact density-matrix probabilities provide a noisy reference independent of sampled counts."
    )
    figure(
        "noise",
        235,
        "432 sampling runs: six noise cases, two times, three shot budgets and twelve repeated seeds. Error bars show uncertainty of a Monte Carlo mean, not biological or hardware uncertainty.",
    )
    p(
        "The synthetic model places depolarizing error p on CX, p/10 on sx/x, no error on rz, and symmetric readout flips r. Those choices illustrate mechanisms; they are not IBM calibrations."
    )
    p(
        "Readout noise changes observed probabilities without changing pre-readout coherence. Gate noise changes the state. More shots reduce sampling fluctuations around a biased noisy distribution but do not remove the bias."
    )
    p(
        "A separate Aer model uses the confirmed ibm_quebec backend calibration snapshot on the actual submitted circuits. It predicts small distribution errors for the fly and molecular cases, and greater error for deeper scheduling circuits. These are <b>local forecasts</b>, not returned IBM measurements."
    )
    table(
        ["Evidence class", "What it establishes"],
        [
            [
                "Exact local model",
                "The intended small circuit or Gibbs state is mathematically correct.",
            ],
            ["Synthetic noise", "Behavior under declared illustrative error channels."],
            [
                "Calibration forecast",
                "A local approximation using a device calibration snapshot.",
            ],
            [
                "Collected IBM counts",
                "An actual experiment, with shot uncertainty and device systematics.",
            ],
        ],
        widths=[155, 357],
    )
    p(
        'Source: <link href="https://qiskit.github.io/qiskit-aer/tutorials/2_device_noise_simulation.html" color="#107d73">Qiskit Aer device-noise simulation</link>. Markovian calibration models omit drift, crosstalk and other correlated or systematic errors.',
        "SmallOh",
    )
    page()
    heading(
        "Quantum chemistry / 2 qubits", "EigenBudget: a failure with an explanation"
    )
    p(
        "BondBench maps H2 in STO-3G to two qubits and checks eight bond lengths against an independent PySCF FCI calculation. Its one-parameter determinant-sector circuit reproduces the tiny exact ground state. Noise experiments measure fixed ideally optimized preparations; they are not noisy VQE training."
    )
    figure(
        "chemistry",
        185,
        "Independent molecular reference and parity filtering under synthetic noise. The measurement groups account for correlations within each basis.",
    )
    p(
        "The initial pilot allocator lost to uniform measurement at all three tested ground-state geometries. For H=A+B+cI and an exact eigenstate, (A-&lt;A&gt;)|psi&gt; = -(B-&lt;B&gt;)|psi&gt;. Taking squared norms gives Var(A)=Var(B). Under ideal independent group sampling, equal shots therefore minimize energy variance. This elementary identity is not claimed as a new theorem."
    )
    figure(
        "eigenbudget",
        185,
        "Controlled imperfect-state follow-up. Every estimate pays for 128 pilot shots; pilot counts are excluded from the production estimate. Jeffreys half-count regularization prevents extreme allocation from unseen outcomes.",
    )
    ratio = next(
        r
        for r in stats["eigenbudget_comparisons"]
        if r["offset"] == 1.2
        and r["paid_budget"] == 8192
        and r["method"] == "regularized_adaptive"
    )
    p(
        f"At offset 1.2 radians and 8192 paid shots, regularized allocation reduced RMSE by {(1 - ratio['rmse_ratio']) * 100:.1f}% in this fixed ideal simulation. The paired bootstrap RMSE ratio is {ratio['rmse_ratio']:.3f}, interval {ratio['bootstrap95'][0]:.3f}-{ratio['bootstrap95'][1]:.3f}. Near the eigenstate, no reliable gain is established. These are exploratory conditional sampling intervals, not hardware or general model guarantees.",
        "SmallOh",
    )
    p(
        'Sources: <link href="https://qiskit-community.github.io/qiskit-nature/stubs/qiskit_nature.second_q.mappers.ParityMapper.html" color="#107d73">Qiskit Nature parity mapping</link>; <link href="https://pyscf.org/user/ci.html" color="#107d73">PySCF FCI</link>; <link href="https://pubs.acs.org/doi/10.1021/acs.jctc.3c01113" color="#107d73">Established shot-assignment methods</link>.',
        "SmallOh",
    )
    if active:
        page()
        heading(
            "Quantum chemistry / controlled extension",
            "ActiveBudget: when overhead changes the answer",
        )
        p(
            "The two-group equal-variance identity does not force equal variances across a larger measurement partition. LiH provides a small controlled extension: freeze the Li 1s core, retain two electrons in two spatial orbitals, and parity-map the active Hamiltonian to two qubits. Four deterministic qubit-wise commuting groups use local XX, XZ, ZX and ZZ measurement bases."
        )
        p(
            f"The mapped ground energy including nuclear and frozen-core shifts is {active['reference_casci_energy']:.10f} hartree, agreeing with an independent PySCF CASCI(2,2) calculation to numerical precision. This is an active-space approximation with fixed RHF orbitals, not full-space FCI or a chemical-accuracy claim."
        )
        figure(
            "activebudget",
            240,
            "Ground-state group variances differ. Every adaptive trial pays 64 pilot shots per group (256 total); the pilot is excluded from production estimates. Half-count regularization and minimum production counts prevent unsupported extreme allocations.",
        )
        table(
            ["Paid shots", "Uniform RMSE", "Adaptive RMSE", "Ratio / bootstrap 95%"],
            [
                [
                    s["budget"],
                    f"{s['rmse']['uniform']:.6f}",
                    f"{s['rmse']['regularized_adaptive']:.6f}",
                    f"{s['adaptive_to_uniform_ratio']:.3f} / {s['paired_bootstrap_95'][0]:.3f}-{s['paired_bootstrap_95'][1]:.3f}",
                ]
                for s in active["summaries"]
            ],
            widths=[75, 105, 105, 227],
        )
        p(
            "The same procedure loses at 2048 paid shots and helps at 8192. That crossover is more defensible than promising universal savings. Both budgets contain 400 independent sampling repeats; paired bootstrap intervals are conditional Monte Carlo uncertainty for this fixed state and grouping. The tiny ground state is obtained classically; no LiH hardware job or noisy optimization is claimed."
        )
        p(
            'Sources: <link href="https://pyscf.org/user/mcscf.html" color="#107d73">PySCF CASCI and active spaces</link>; <link href="https://qiskit-community.github.io/qiskit-nature/stubs/qiskit_nature.second_q.transformers.ActiveSpaceTransformer.html" color="#107d73">Qiskit Nature ActiveSpaceTransformer</link>.',
            "SmallOh",
        )
    if active_noise:
        page()
        heading("Chemistry / noise audit", "Variance savings do not remove bias")
        p(
            "A real two-qubit preparation with three RY angles and one CX reproduces the same LiH active-space ground energy. The fixed circuit is compiled into rz, sx, x and cx, then each measurement basis is evaluated with a local density-matrix simulator. Independent symmetric readout errors are applied explicitly to the outcome distributions. This separates sampling variation from systematic error."
        )
        figure(
            "activenoise",
            250,
            "8192 paid shots. The left panel measures sampling error around the noisy expectation; the right panel measures total error against the independent ideal CASCI reference. These are different quantities.",
        )
        table(
            [
                "Declared case",
                "CX depolarizing p",
                "Readout flip r",
                "Exact bias / hartree",
            ],
            [
                [
                    r["case"],
                    r["gate_error"],
                    r["readout_error"],
                    f"{r['systematic_bias']:.6f}",
                ]
                for r in active_noise["references"]
            ],
            widths=[110, 130, 110, 162],
        )
        p(
            "The ideal allocation gain does not survive consistently under these declared errors. At a 1% readout-flip probability, the exact energy bias is about 0.00313 hartree; adding 0.5% CX depolarization raises it to about 0.00484. Both exceed the ideal high-budget sampling RMSE. More shots or a different allocation do not remove that bias."
        )
        p(
            "This follow-up retains all six budget/noise combinations and both estimators. It uses fixed ideally optimized states, not noisy VQE training, actual IBM calibrations, error mitigation or a proof about every noise channel. The practical project question becomes when to allocate shots and when to spend effort on measurement quality instead."
        )
    page()
    heading("Materials science / 4 qubits", "SpinWeave: an energy witness")
    p(
        "A four-spin Heisenberg ring has alternating couplings J=1+delta and 1-delta. Positive couplings imply E &gt;= -sum(J)/4 for every fully separable state: each local Bloch vector has norm at most one, so each spin-pair correlation is bounded below by -1/4. Neel product states attain the bound on this bipartite ring."
    )
    figure(
        "spinweave",
        180,
        "Alternating exchange layers match exact ground energies at all five dimerizations. Synthetic noise progressively erases the energy witness. The first restricted ansatz failed by up to 0.5 J and was rejected.",
    )
    if thermal:
        figure(
            "spintherm",
            180,
            "Exact classical Gibbs-state analysis. Heating destroys witness detection; entanglement depends on the cut. At delta=1, the two dimers are independent across the pair/pair cut at every temperature.",
        )
        p(
            "The independent-dimer entanglement crossover is exactly T=2/ln(3)=1.82048 in dimensionless kBT/J units. The implementation checks that analytic limit and verifies spectral Gibbs states against a matrix-exponential calculation. This is a finite-size crossover, not a thermodynamic phase transition.",
            "SmallOh",
        )
    p(
        "The energy witness detects some entanglement, not necessarily genuine four-partite entanglement. An energy above the bound does not prove separability. Positive negativity detects entanglement across its specified cut; zero negativity does not generally prove its absence. The model is not a prediction for a named material.",
        "SmallOh",
    )
    p(
        'Source: <link href="https://arxiv.org/abs/quant-ph/0408086" color="#107d73">Dowling, Doherty and Bartlett, Energy as an Entanglement Witness for Quantum Many-Body Systems</link>. The experimental contribution is the compact validated demonstration, not the established witness theory.',
        "SmallOh",
    )
    if shield:
        page()
        heading("Materials / confidence audit", "SpinShield: uncertainty has a price")
        p(
            "A measured energy below -1 can occur from finite-shot fluctuations even for a fully separable Neel product state. SpinShield adds a one-sided bounded-variable confidence margin, avoiding a normal approximation. For independent fixed-count measurement groups, E_true &lt;= E_hat + sqrt[log(1/alpha)/2 * sum(range_a^2/n_a)] + b, with probability at least 1-alpha, provided total absolute measurement bias is bounded by b."
        )
        figure(
            "spinshield",
            180,
            "Six reference states, three shot counts and two readout conditions; 500 trials per setting. No known separable control was detected in these trials. This observation supplements the bound; it is not a proof of zero false-alarm probability.",
        )
        ring = next(
            r
            for r in shield["first_repeat_controls"]
            if r["case"] == "Ring ground"
            and r["readout"] == 0.02
            and r["shots_per_basis"] == 1024
        )
        neel = next(
            r
            for r in shield["first_repeat_controls"]
            if r["case"] == "Neel product"
            and r["readout"] == 0
            and r["shots_per_basis"] == 1024
        )
        table(
            ["Fixed simulation trial", "Measured E", "Sampling + bias", "Upper bound"],
            [
                [
                    "Neel product / ideal readout",
                    f"{neel['energy']:.3f}",
                    f"{neel['hoeffding_margin']:.3f} + 0",
                    f"{neel['upper_with_bias']:.3f}",
                ],
                [
                    "Ring ground / 2% flips",
                    f"{ring['energy']:.3f}",
                    f"{ring['hoeffding_margin']:.3f} + {ring['readout_bias_allowance']:.3f}",
                    f"{ring['upper_with_bias']:.3f}",
                ],
            ],
            widths=[175, 75, 140, 122],
        )
        p(
            "The Neel upper bound withholds detection; the ring bound supports the witness after both allowances. Each trial costs 3072 shots. The readout allowance assumes independent symmetric flips bounded by 2%, correct basis rotations and a common prepared state. Unknown coherent errors, drift and correlated readout are not covered."
        )
        ring_plan = next(
            r
            for r in shield["plans"]
            if r["case"] == "Ring ground" and r["readout"] == 0.02
        )
        warm_plan = next(
            r for r in shield["plans"] if r["case"] == "Warm ring" and r["readout"] == 0
        )
        p(
            f"With an independently known expected measured energy, {ring_plan['total_shots_sufficient']} total shots suffice for at least 95% detection power for the ring ground state with 2% flips. The near-threshold warm ring with ideal readout requires {warm_plan['total_shots_sufficient']:,} by this conservative bound. A finite-count convolution audit checks coverage and power. This is not a data-adaptive hardware guarantee.",
            "SmallOh",
        )
        p(
            'Confidence is pointwise for one preselected fixed decision. Searching many states or adapting the stopping time needs additional control. Thermal states are classical references. SpinCourt asks viewers to issue or withhold a witness before revealing the reference. Established inequality: <link href="https://doi.org/10.1080/01621459.1963.10500830" color="#107d73">Hoeffding, 1963</link>.',
            "SmallOh",
        )
    page()
    heading("Sustainability / 4 qubits", "PhaseGuard: the histogram misses the phase")
    p(
        "GridGuard places four jobs in two slots, exactly two late. Energy, renewable supply and carbon factors are illustrative proxy units. Exact enumeration and a greedy rule both find the optimum, 0.73; this is a circuit-design experiment, not a practical carbon-saving or speedup claim."
    )
    figure(
        "phaseguard",
        205,
        "Two local RZ(pi/2) corrections change relative phases without changing the initial schedule histogram. Original-case p=1 matched optimization reaches 97.6% optimal probability after correction.",
    )
    placement_rows = []
    for heavy in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]:
        means = []
        for prep in ["pair", "phase_pair"]:
            values = [
                r["optimal_probability"]
                for r in placements["rows"]
                if r["heavy_positions"] == list(heavy) and r["preparation"] == prep
            ]
            means.append(sum(values) / len(values))
        placement_rows.append(
            [str(heavy), f"{means[0] * 100:.1f}%", f"{means[1] * 100:.1f}%"]
        )
    table(
        ["Heavy-job positions", "Original paired start", "Phase corrected"],
        placement_rows,
        widths=[185, 170, 157],
    )
    p(
        "Matched differential-evolution searches use the same angle bounds, evaluation counts and three seeds. Large gains occur in two of six placements, slight losses in two, and neither preparation succeeds in two. This is sensitivity analysis on one small problem family, not general superiority.",
        "SmallOh",
    )
    p(
        "The causal demo keeps later gates fixed and sweeps only the preparation phase: original-case optimum probability moves from 24.9% at 0 degrees to 97.6% at 90 degrees. Those fixed angles were selected for the 90-degree case. Generic compilation gives equal CX counts for the optimized pair variants; backend optimization prunes them differently (14 versus 34 two-qubit gates in the local forecast). The corrected circuit was not part of the three submitted IBM jobs.",
        "SmallOh",
    )
    p(
        'Source: <link href="https://arxiv.org/abs/1709.03489" color="#107d73">Hadfield et al., Quantum Alternating Operator Ansatz</link>. Number-conserving XY mixing is established; the phase and placement ablation is this lab\'s exploratory contribution.',
        "SmallOh",
    )
    page()
    heading(
        "Quantum machine learning / 3 qubits",
        "KernelForge: validation can select zero CX gates",
    )
    p(
        "Wine chemical features are standardized and reduced to three PCA coordinates using training data only. Five bounded circuits produce local Bloch features. A classical RBF classifier uses those quantum features. Selection considers validation accuracy and circuit cost, then freezes the architecture and hyperparameters before scoring a held-out test set."
    )
    figure(
        "kernelforge",
        220,
        "The primary split compares product, line and ring architectures with one or two layers, ideal and synthetic gate-noise features, finite-shot sampling, and matched classical controls.",
    )
    table(
        ["Model", "Mean accuracy over five splits", "Split SD"],
        [
            [
                name.replace("classical_", "").replace("_", " "),
                f"{r['mean_accuracy'] * 100:.1f}%",
                f"{r['split_standard_deviation'] * 100:.1f} points",
            ]
            for name, r in stats["qml_aggregate"].items()
        ],
        widths=[240, 180, 92],
    )
    p(
        "All five split replications selected the unentangled product preparation. Quantum features averaged 93.8% held-out accuracy; classical PCA/RBF averaged 96.4%. No quantum accuracy advantage was found. The overlapping splits are a sensitivity analysis, not five independent datasets or a population confidence interval."
    )
    p(
        "Exact expectations and synthetic noisy density matrices are computed locally. Finite-shot features use independent binomial samples of each Pauli expectation; they are not IBM kernel measurements. The paid cost is nine independent observable measurements per datum in this simulator, with three grouped settings possible in a future implementation.",
        "SmallOh",
    )
    p(
        'Sources: <link href="https://quantum.cloud.ibm.com/docs/en/tutorials/projected-quantum-kernels" color="#107d73">IBM projected quantum kernels</link>; <link href="https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_wine.html" color="#107d73">scikit-learn Wine dataset</link>. These are established methods and a familiar dataset; this is an architecture audit rather than the preferred headline submission.',
        "SmallOh",
    )
    page()
    heading(
        "Returned IBM evidence" if collected else "Hardware and evidence",
        "Three jobs, fourteen circuits"
        if collected == 3
        else "A receipt is not a result",
    )
    table(
        ["Job family", "Backend", "Current status"],
        [[r["folder"], r["backend"], r["status"]] for r in ev["hardware_status"]],
        widths=[245, 120, 147],
    )
    p(
        "The authorized event credential accessed ibm_quebec. No organizer usage limit was supplied; access does not establish unlimited allocation. The sprint cap was three jobs, up to six circuits per job, 1024 shots per circuit and 300 seconds maximum execution allowance per job. All three jobs returned counts."
    )
    evidence_rows = []
    for r in ev["physical_metrics"]:
        if r["project"] == "FlyWalk" or r["origin"] != "REAL_IBM_HARDWARE":
            continue
        if r["project"] == "SpinWeave":
            detail = f"E={r['energy']:.4f}, SE={r['standard_error']:.4f}; Hoeffding sampling upper={r['hoeffding_sampling_upper']:.4f}; systematics not covered"
        elif r["project"] == "BondBench":
            detail = f"R={r['distance']}; raw {r['raw']['energy']:.5f}, filtered {r['filtered']['energy']:.5f}"
        else:
            detail = f"{r['case']}; optimal {r['optimal_probability'] * 100:.1f}%"
        evidence_rows.append([r["origin"], r["project"], detail])
    table(
        ["Count origin", "Project", "Derived metric"],
        evidence_rows,
        widths=[155, 90, 267],
    )
    if collected:
        spin_returned = next(
            (
                r
                for r in ev["physical_metrics"]
                if r["project"] == "SpinWeave" and r["origin"] == "REAL_IBM_HARDWARE"
            ),
            None,
        )
        if spin_returned:
            p(
                f"<b>Materials result:</b> the ring returned E={spin_returned['energy']:.6f} J with sampling SE={spin_returned['standard_error']:.6f}. The fixed one-sided 95% Hoeffding sampling upper is {spin_returned['hoeffding_sampling_upper']:.6f}, below the fully separable bound -1. This supports the witness under independent fixed-shot sampling, correct measurements and a common prepared-state assumption. Unknown device measurement bias and drift have not been characterized, so this is not an unconditional physical certificate. The demo lets the audience vary a hypothetical bias allowance; this decision requires a total bias bound below 0.7327 J, which the sprint did not establish."
            )
        p(
            "<b>Chemistry caution:</b> at 0.735 angstrom, parity filtering moves the sampled energy closer to FCI; at 1.4 angstrom it moves farther away and both estimates lie below FCI within their sampling uncertainty. A noisy finite-shot estimate does not obey the variational lower bound. These two distances do not establish a universal mitigation gain or chemical accuracy.",
            "SmallOh",
        )
        p(
            "<b>Scheduling result:</b> Dicke p=2 returns 80.47% optimal outcomes and 87.60% feasible outcomes, versus 49.90% optimal for Dicke p=1 and 22.07% for the RX paired start. Depth, preparation and mixer differ, so this is a small implementation comparison, not a controlled claim that depth alone helps. The later phase-corrected preparation was not in these submitted jobs.",
            "SmallOh",
        )
    p(
        "Read the origin column before interpreting a number. LOCAL_CALIBRATION_FORECAST means locally simulated counts from a device model. REAL_IBM_HARDWARE means returned device counts. Shot standard errors do not cover unknown systematic measurement bias; a physical entanglement certificate needs those assumptions too.",
        "SmallOh",
    )
    p(
        "The credential is kept only in ignored .env. It is absent from tracked files, the public evidence snapshot and this report. Private service configuration, job IDs and circuit bundles are excluded from public artifacts. The submitted circuit records remain local for collection and audit.",
        "SmallOh",
    )
    page()
    heading("Reproduce / present / decide", "A focused submission, backed by the lab")
    p(
        "<b>Three-minute pitch:</b> choose one track; state one small question; show the simplest reference; demonstrate the result and the failed alternative; explain the limit. Use the portfolio as evidence of how the team selected its idea, rather than presenting every experiment as a separate submission."
    )
    p(
        '<b>Best materials pitch:</b> "Can a four-qubit toy magnet retain an energy witness of entanglement under noise?" Show the rejected separable-control verdict, then the returned IBM ring counts and their fixed sampling bound. Vary the hypothetical bias allowance, explain what has not been calibrated, and close with the independent-dimer thermal limit.'
    )
    p(
        '<b>Best chemistry pitch:</b> "When is adaptive measurement a waste?" Begin with the failed allocator, derive the two-group eigenstate identity, show the regularized imperfect-state comparison with paid pilots, and display both gains and non-gains.'
    )
    p(
        "<b>Playful alternatives:</b> let the audience turn the PhaseGuard knob while the starting histogram stays fixed; or disconnect a FlyWalk population and compare diffusion with interference. Keep exact/greedy controls and the single-specimen caveats visible."
    )
    table(
        ["Check", "Evidence"],
        [
            [
                "Scientific tests",
                f"{checks} tests; analytic walk, FCI, Bell basis, costs, conservation, phase equivalence and thermal limits.",
            ],
            [
                "Clean checkout",
                "Tests pass; exported source and evidence hashes match; no .env present.",
            ],
            [
                "Reproducibility",
                "uv.lock, fixed seeds, raw sample CSVs, pinned fly data, explicit settings and negative decisions.",
            ],
            [
                "Visual review",
                "Figures inspected; offline UI controls exercised for walk, budgets, scheduling, phases and materials.",
            ],
            [
                "Timing",
                "Append-only stage timestamps and runtimes; parallel compute time is not summed as development effort.",
            ],
        ],
        widths=[150, 362],
    )
    p(
        '<font name="Courier">uv sync --locked<br/>uv run python -m unittest discover -s tests -v<br/>uv run python -m flybrain run<br/>uv run python -m tracklab.spinweave<br/>uv run python -m tracklab.eigenbudget<br/>uv run python -m tracklab.demo</font>',
        "SmallOh",
    )
    p(
        "Current project commands and scope live in README.md; historical experiment assumptions live in the corresponding source modules. Frozen results are under artifacts/sprint-20261003; the portable dashboard is demo/index.html. The append-only board preserves coordination history; retired Rockland/AABC work remains removed.",
        "SmallOh",
    )
    p(
        '<link href="https://github.com/OhRats-Technologies/OhRats_QFF2026_uottawa" color="#107d73">Repository: OhRats-Technologies/OhRats_QFF2026_uottawa</link><br/><link href="https://www.uoquantum.com/" color="#107d73">Festival: uoquantum.com</link>',
        "SmallOh",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d5ded7"))
        canvas.line(50, 750, 562, 750)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(INK)
        canvas.drawString(50, 764, "OhRats. / Quantum Reality Lab")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#536769"))
        canvas.drawString(
            50,
            28,
            "Qiskit Fall Fest 2026 | Evidence snapshot "
            + now.strftime("%H:%M Toronto"),
        )
        canvas.drawRightString(562, 28, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(args.output),
        pagesize=(612, 792),
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=48,
        title="Quantum Reality Lab - Qiskit Fall Fest 2026",
        author="OhRats Technologies",
    )
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    print("Created report: " + str(args.output))


if __name__ == "__main__":
    main()
