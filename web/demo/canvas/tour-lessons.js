export const tour = [
  {
    name: "ONTARIO", tab: "map", zone: "map",
    pages: [
      "Hi, I'm Betty! Welcome to our workshop. This map shows recorded Ontario fires and forest cover.",
      "We'll build an engine that estimates a year's average hectares per reported fire. Then we'll try to improve it together!",
    ],
  },
  {
    name: "SIGNAL RACK", tab: "rack", zone: "rack",
    pages: [
      "Pick what your engine sees: heat, rain or forest signals. The glowing buttons are your connected inputs.",
      "Start with a few signals. More inputs take more computation, and they don't always make a better engine.",
    ],
  },
  {
    name: "ANGLE", tab: "kernel", ids: ["angle-down", "angle-up"],
    pageZones: [null, null, "kernel", "kernel", "kernel", "kernel"],
    pages: [
      "These buttons change the angle range. We scale each signal, then encode it as rotations in a quantum circuit.",
      "The resulting states overlap to form this similarity grid. Changing the angle range changes those similarities. Wider isn't always better!",
      "Each row and column is a year. A cell compares that pair of years; the diagonal compares each year with itself.",
      "Brighter cells mean more similar encoded conditions; darker cells mean less similar. After the tour, point at a cell to compare its years.",
      "The regression learns from these similarities and known fire sizes to estimate another year's average size. Similarity isn't a fire-risk score.",
      "Changing signals or angles changes which years look alike. If every pair looks identical or unrelated, the regression has little structure to learn.",
    ],
  },
  {
    name: "C", tab: "kernel", ids: ["strength-down", "strength-up"],
    pages: [
      "C controls how strongly our classical regression solver penalizes errors outside its tolerance band. Higher C pushes harder to fit training years.",
      "Lower C favors a simpler fit. Try both: fitting familiar years closely doesn't guarantee better estimates for other years.",
    ],
  },
  {
    name: "EPSILON", tab: "kernel", ids: ["epsilon-down", "epsilon-up"],
    pages: [
      "Epsilon gives small errors some breathing room. Errors inside this tolerance band receive no fitting penalty from the regression solver.",
      "A wider band tolerates more deviations; a narrower band asks for a closer fit. These units are scaled log targets, not hectares.",
    ],
  },
  {
    name: "SUBSET FOUNDRY", tab: "rack", ids: ["foundry"],
    pages: [
      "The foundry searches for four-signal combinations. QAOA stands for Quantum Approximate Optimization Algorithm. Let's peek at how it works!",
      "QAOA alternates cost and mixing operations, reshaping which subsets get sampled. Our foundry uses a fixed circuit to propose candidates.",
    ],
  },
  {
    name: "SQD SHORTLIST", tab: "rack", foundry: true,
    pages: [
      "SQD means Sample-based Quantum Diagonalization. It solves a smaller Hamiltonian matrix built from sampled states. Here, those states represent signal subsets.",
      "Our matrix is diagonal, so the starred row is the cheapest sampled subset. Patch it into your engine, then test its prediction!",
    ],
  },
  {
    name: "TUNE YOUR ENGINE", tab: "rack", zone: "execution",
    pages: [
      "Each complete build tests itself after a short pause. Change a signal or setting and watch your score update automatically.",
      "Cut error by five percent, or computation by twenty-five percent with at most five percent extra error. Next appears when you succeed!",
    ],
  },
];
export const tourText = (s) => tour[s.guideStep || 0].pages[s.guidePage || 0];
