"""Step 2: scenarios. Metrics (TTC, required deceleration), mining braking events from the logs, and the physics
frontier that separates 'no planner could have avoided this' from 'this planner failed'."""
import numpy as np

from . import config as C


def ttc(gap, closing):
    """Time to collision [s] = gap / closing speed (inf when the gap is not closing)."""
    gap, closing = np.asarray(gap, dtype=float), np.asarray(closing, dtype=float)
    closing_in = closing > 0
    return np.where(closing_in, gap / np.where(closing_in, closing, 1.0), np.inf)


def required_decel(gap, closing):
    """Deceleration [m/s^2] needed to remove the closing speed exactly at contact: closing^2 / (2 gap)."""
    gap, closing = np.asarray(gap, dtype=float), np.asarray(closing, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):          # gap 0 while closing in: infinite deceleration
        return np.where(closing > 0, closing ** 2 / (2 * gap), 0.0)


def unavoidable(gaps, dvs, t_react=0.0, b_max=C.B_MAX):
    """Boolean grid (len(dvs), len(gaps)): True where NO planner can avoid contact, even braking at b_max after the
    reaction delay: gap < dv * t_react + dv^2 / (2 b_max)  (lead keeps its speed)."""
    G, DV = np.meshgrid(np.asarray(gaps, dtype=float), np.asarray(dvs, dtype=float))
    # during the delay the gap shrinks by dv * t_react; braking at b_max then needs dv^2 / (2 b_max) more
    needed = DV * t_react + DV ** 2 / (2 * b_max)
    return (DV > 0) & (G < needed)


def mine_braking(logs, threshold=C.BRAKE_THRESHOLD, min_steps=5):
    """Find trajectories where the lead brakes: smoothed deceleration below `threshold` for at least `min_steps`
    consecutive steps (0.5 s). Returns a list of event dicts (one per trajectory, first event only)."""
    events = []
    kernel = np.ones(min_steps, dtype=int)
    for i in range(len(logs)):
        k = int(logs.n[i])
        a = logs.a_lead[i, :k]                                   # smoothed, NOT acc_lead_raw
        below = a < threshold                                    # NaN counts as not braking
        if k < min_steps or below.sum() < min_steps:
            continue
        full = np.flatnonzero(np.convolve(below.astype(int), kernel, mode="valid") == min_steps)
        if not full.size:
            continue
        onset = int(full[0])                                     # first full window = start of the first long run
        stops = np.flatnonzero(~below[onset:])
        end = onset + (int(stops[0]) if stops.size else k - onset)
        events.append({"traj": i, "onset_step": onset, "peak_decel": float(a[onset:end].min()),
                       "gap_m": float(logs.gap[i, onset]),
                       "closing_m_s": float(logs.v_ego[i, onset] - logs.v_lead_s[i, onset]),
                       "ego_speed": float(logs.v_ego[i, onset])})
    return events


def human_brake_limit(logs, q=0.1):
    """Hardest braking [m/s^2, positive number] that the logged human followers ever applied (the q-th percentile of
    their acceleration, from the speed differences). Learned planners cannot have seen anything harder."""
    a = np.diff(logs.v_ego, axis=1) / C.DT
    return float(-np.nanpercentile(a, q))


def grid_from_logs(logs, v_ego, n_gap=60, n_dv=45):
    """Scenario grid. Gap limits come from what the logs contain (p2 .. p98 of the logged gaps). Closing speed runs
    from 0 to v_ego: dv = v_ego means the cutter is standing still, the most extreme case (never faster than that,
    otherwise the cutter would drive backwards)."""
    g_lo, g_hi = np.nanpercentile(logs.gap, [2, 98])
    return np.linspace(g_lo, g_hi, n_gap), np.linspace(0.0, v_ego, n_dv)
