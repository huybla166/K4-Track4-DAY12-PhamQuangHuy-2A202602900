/* Bonus (step 8, not graded): sweep the 3D simulator of viz/ headless, with MY trained models, over every training seed.
   Same scenes and the same scoring as the "Bài lab" chapter of viz/app.js (labParams / labExec / labOutcome), but run as a
   grid instead of one slider position at a time, so the observations of GUIDE.md step 8 come with counts.

     python3 scripts/export_viz.py          # writes viz/lab_models.js and viz/lab_data.js from work/models + evidence
     node bonus/viz_sweep.js                # writes bonus/viz_sweep.json and prints the tables

   The 3D world has its own physics (bicycle model, 20 Hz, other traffic): compare the SHAPE with evidence/, not the numbers. */
"use strict";
const fs = require("fs");
const path = require("path");

const VIZ = path.join(__dirname, "..", "viz");
const S = require(path.join(VIZ, "sim.js"));             // loads viz/lab_models.js by itself
const LD = require(path.join(VIZ, "lab_data.js"));
if (!S.hasLab()) throw new Error("viz/lab_models.js missing: run python3 scripts/export_viz.py first");

const PLANNERS = [["labidm", "IDM"], ["labcv", "const-vel"], ["labego", "EgoMLP"], ["labperc", "PercMLP"], ["labfix", "PercMLP+"]];
const LEARNED = { labego: true, labperc: true, labfix: true };
const T_END = 14;

function params(sc) {                                    // = labParams() in viz/app.js
  const p = { pedT0: 1e9, busGo: 1e9, cutT0: 99, tgMode: sc.rear === "replay" ? "const" : "idm", react: sc.rear === "reactive" ? 0.6 : 0, tgT: 1.4 };
  let v0 = 11.2;
  if (sc.scene === "brake") { p.brkDecel = sc.decel; p.brkDur = 2.4; }
  else if (sc.scene === "cutin") { v0 = sc.v0; p.brkT0 = 99; p.egoV0 = v0; p.labCut = { gap: sc.gap, dv: Math.min(sc.dv, v0 - 0.5) }; }
  else { const L = LD.logs[sc.log]; v0 = L.ego[0]; p.brkT0 = 99; p.egoV0 = v0; p.leadProf = L.lead; p.egoProf = L.ego; p.leadGap0 = L.gap0; }
  p.rearGap = 2 + v0 * 1.4;
  return p;
}

function outcome(R) {                                    // = labOutcome() in viz/app.js (front / rear collision)
  const replayed = R.opts.params.tgMode === "const";
  let front = false, rear = false, tRear = Infinity;
  const other = (h) => (h.a === "ego" ? h.b : h.a);
  R.m.hits.forEach((h) => { if (other(h) === "TG") { rear = true; if (replayed) tRear = Math.min(tRear, h.t); } });
  R.m.hits.forEach((h) => { if (other(h) !== "TG" && h.t < tRear) front = true; });   // after a fake rear hit nothing counts
  return { front, rear };
}

function runScene(sc) {                                  // {planner short name: {front: k, rear: k, n: seeds}}
  const p = params(sc), out = {};
  for (const [pl, name] of PLANNERS) {
    const seeds = LEARNED[pl] ? LD.seeds.map((_, i) => i) : [0];
    const res = seeds.map((i) => {
      const R = S.run({ params: p, ego: "planner", planner: pl, policy: { labSeed: LD.seeds[i] }, others: "reactive", tEnd: T_END });
      R.m = S.egoMetrics(R, null);
      return outcome(R);
    });
    out[name] = { front: res.filter((r) => r.front).length, rear: res.filter((r) => r.rear).length, n: res.length };
  }
  return out;
}

const fmt = (c) => (c.n > 1 ? `${c.front}/${c.n}` : c.front ? "yes" : "no");
function table(title, rows, label, key = "front") {
  const names = PLANNERS.map((p) => p[1]);
  console.log(`\n${title}\n| ${label} | ${names.join(" | ")} |\n|---|${names.map(() => "---").join("|")}|`);
  for (const [x, r] of rows) console.log(`| ${x} | ${names.map((n) => (key === "front" ? fmt(r[n]) : `${r[n][key]}/${r[n].n}`)).join(" | ")} |`);
}

const t0 = Date.now();
const result = { student: LD.student.student_id, seeds: LD.seeds, scenes: {} };

// 1. the lead brakes hard (reactive rear car): from which deceleration does each planner hit the lead?
const brake = [];
for (const decel of [3, 4, 5, 6, 7, 8, 9]) brake.push([decel, runScene({ scene: "brake", decel, rear: "reactive" })]);
result.scenes.brake_decel_sweep = Object.fromEntries(brake);
table("Lead brakes for 2.4 s (rear car reacts): front collisions, k / seeds", brake, "lead decel [m/s²]");

// 2. the lab's cut-in at the default ego speed of the page (14 m/s): sweep the closing speed at three gaps
const cutin = [];
for (const gap of [6, 10, 20]) for (const dv of [2, 4, 6, 8, 10, 12, 13.5]) cutin.push([`gap ${gap} m, dv ${dv}`, runScene({ scene: "cutin", v0: 14, gap, dv, rear: "reactive" })]);
result.scenes.cutin_sweep_v14 = Object.fromEntries(cutin);
table("Cut-in, ego at 14 m/s (rear car reacts): front collisions, k / seeds", cutin, "cut-in");

// 3. replayed vs reactive rear car on the same scenes: rear collisions
const rearRows = [];
for (const sc of [{ scene: "brake", decel: 6 }, { scene: "cutin", v0: 14, gap: 10, dv: 8 }]) {
  for (const rear of ["replay", "reactive"]) {
    const label = `${sc.scene === "brake" ? "brake 6 m/s²" : "cut-in 10 m / 8 m/s"}, rear ${rear}`;
    rearRows.push([label, runScene({ ...sc, rear })]);
  }
}
result.scenes.rear_replay_vs_reactive = Object.fromEntries(rearRows);
table("Rear car replayed (cannot react) vs reactive: REAR collisions, k / seeds", rearRows, "scene", "rear");
table("Same scenes: FRONT collisions (before any fake rear hit), k / seeds", rearRows, "scene");

// 4. every exported real log (12 with the hardest held-out lead braking + 12 calm): how many logs end in a front collision?
const names = PLANNERS.map((p) => p[1]);
const perLog = LD.logs.map((L, i) => ({ id: L.id, brake: L.brake, peak_decel: L.peak_decel, res: runScene({ scene: "log", log: i, rear: "reactive" }) }));
const logsSummary = {};
for (const n of names) {
  const k = perLog[0].res[n].n;                          // each (log, seed) run counts once
  logsSummary[n] = { seed_runs: k, logs: LD.logs.length, braking_logs: LD.logs.filter((l) => l.brake).length,
                     front_hits_total_over_seeds: perLog.reduce((a, r) => a + r.res[n].front, 0),
                     front_hits_on_braking_logs_over_seeds: perLog.filter((r) => r.brake).reduce((a, r) => a + r.res[n].front, 0),
                     logs_hit_by_any_seed: perLog.filter((r) => r.res[n].front > 0).length };
}
result.scenes.real_logs = { per_log: perLog, summary: logsSummary };
console.log(`\nAll ${LD.logs.length} exported real logs (${logsSummary.IDM.braking_logs} with a braking lead), rear car reacts`);
console.log("| planner | runs (logs × seeds) | front collisions | of which on braking logs | logs hit by ≥1 seed |\n|---|---|---|---|---|");
for (const n of names) {
  const s = logsSummary[n];
  console.log(`| ${n} | ${s.logs * s.seed_runs} | ${s.front_hits_total_over_seeds} | ${s.front_hits_on_braking_logs_over_seeds} | ${s.logs_hit_by_any_seed} |`);
}

result.seconds = Math.round((Date.now() - t0) / 1000);
fs.writeFileSync(path.join(__dirname, "viz_sweep.json"), JSON.stringify(result, null, 1));
console.log(`\n-> bonus/viz_sweep.json (${result.seconds} s)`);
