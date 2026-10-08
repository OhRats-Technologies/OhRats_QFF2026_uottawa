import { planHints } from "./coach-plan.js";
onmessage = ({ data: { data, state } }) => {
  try {
    const plan = planHints(data, state, (checked) => postMessage({ checked }));
    postMessage({ plan });
  } catch (error) { postMessage({ error: error.message }); }
};
