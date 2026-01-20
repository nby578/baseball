# META SYNTHESIS: What Actually Matters

**Purpose:** Reconcile all research findings, identify contradictions, and rank by VALIDATED IMPACT vs CONVENTIONAL WISDOM that may be wrong.

---

## TIER 1: VALIDATED HIGH-IMPACT (Build into system)

These findings have strong evidence, high impact, and should be core to the system.

### Pitcher Evaluation

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **K-BB% is best ERA predictor** | R²=0.224, outperforms xERA/xFIP/SIERA | HIGH | ✅ VERY HIGH |
| **Stuff+ stabilizes in ~80 pitches** | FanGraphs research, beats projections after 4-5 starts | HIGH | ✅ VERY HIGH |
| **GB% > 45% = HR suppression** | Driveline study, 25% fewer HRs than FB pitchers | HIGH (given -13 HR) | ✅ VERY HIGH |
| **Barrel rate < 7% = safe** | Statcast correlation with HR allowed | HIGH | ✅ HIGH |

### Opponent Evaluation

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **Team K% is most exploitable** | Stable, directly translates to +2 pts per K | HIGH | ✅ VERY HIGH |
| **Team ISO matters for HR risk** | Direct correlation with HR allowed | HIGH (given -13 HR) | ✅ HIGH |
| **Platoon advantage = ~8% wOBA** | *The Book* by Tango/Lichtman, 1000+ PA to stabilize | MODERATE | ✅ HIGH |

### Scoring System Exploits (BLJ X Specific)

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **Walks = 65% of singles value** | Math: +3 BB vs +5.6 H with -1 AB | HIGH | ✅ CERTAIN |
| **Holds = 82% of saves** | Math: +9 HLD vs +11 SV | HIGH | ✅ CERTAIN |
| **Setup men undervalued** | 52% more holds than saves, similar total points | HIGH | ✅ HIGH |
| **SB break-even = 60%** | Math: +1.9 SB vs -2.8 CS | MODERATE | ✅ CERTAIN |

### Optimization Framework

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **Problem is trivially small for exact solve** | C(20,5)=15,504 combos, <10ms | HIGH | ✅ CERTAIN |
| **Consumable + Renewable resources** | OR research, validated in slot_scheduler | HIGH | ✅ HIGH |
| **ICM variance adjustment** | Poker theory, widely validated | MODERATE | ✅ HIGH |
| **Snipe risk = survival process** | Auction theory, intuitive | MODERATE | ✅ MODERATE |

### Trade Optimization

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **Keeper leagues = kidney exchange** | Nobel Prize work (Alvin Roth) | HIGH | ✅ VERY HIGH |
| **TTC algorithm for Pareto trades** | Shapley/Scarf 1974, proven | HIGH | ✅ VERY HIGH |
| **Endowment effect = 2-3x overvaluation** | Kahneman/Tversky, replicated | MODERATE | ✅ VERY HIGH |
| **First offer = 50-85% of outcome** | Anchoring research | MODERATE | ✅ HIGH |

---

## TIER 2: VALIDATED MODERATE-IMPACT (Use as tiebreakers)

These are real effects but smaller magnitude or situational.

### Environmental Factors

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **Temperature: 1.8°F = 2% more HR** | Meteorology research | MODERATE | ✅ HIGH |
| **HRFI 1-2 vs 9-10 = 86% HR difference** | homerunforecast.com data | MODERATE | ✅ HIGH |
| **Wrigley wind = 50% HR/FB swing** | Park-specific data | LOW (one park) | ✅ HIGH |
| **Catcher framing = 1-4 pts/start** | Statcast, stable YoY | LOW-MODERATE | ✅ HIGH |
| **Umpire zones = +/- 2-3.5 pts** | umpscorecards.com | LOW | ✅ HIGH |

**BUT:** Umpire assignments post 1-3 hours before game - timing issue!

### Behavioral/Opponent Modeling

| Finding | Evidence | Impact | Confidence |
|---------|----------|--------|------------|
| **Most managers are L1-L2 sophistication** | Level-K research | MODERATE | ✅ MODERATE |
| **Glicko-2 for opponent skill** | Rating system research | LOW | ✅ HIGH |
| **Time zone advantage (PT +3hr vs ET)** | Platform mechanics | LOW | ✅ CERTAIN |

---

## TIER 3: QUESTIONABLE / CONTRADICTED (Re-evaluate)

These findings appear in research but may be WRONG or overstated.

### ✅ COORS FIELD - MYTH DEBUNKED

**Conventional wisdom:** "Never stream at Coors" (HR factor ~130)

**VALIDATED REALITY (Jan 2026):** Coors HR factor is **106** - only 6% above average!

**Why conventional wisdom is WRONG:**
- Humidor installed in 2002 reduced HR factor from 1.566 to 1.06 (50% reduction!)
- Coors has MLB's deepest outfield (415ft to center)
- The humidor keeps balls at 70°F/50% humidity vs Denver's 30% humidity
- Heavier, softer balls don't carry as far

**CONTRARIAN OPPORTUNITY:**
- Coors is SAFER than 5 other parks including Yankee Stadium
- Lower snipe risk because others avoid it
- Dodger Stadium (127) is 4x more dangerous for HR

**Verdict:** ✅ VALIDATED - Coors is acceptable for streaming. Avoid Dodger Stadium instead!

**Full Analysis:** See `Park Factor Analysis - Coors Myth Debunked.md`

### ✅ PARK FACTORS - VALIDATED DATA (2023-2025 Statcast)

**Data Source:** [Baseball Savant Park Factors](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors) - Update monthly during season

| Park | HR Factor | Streaming Verdict |
|------|-----------|-------------------|
| **Dodger Stadium** | **127** | **AVOID - WORST** |
| Great American | 123 | AVOID |
| Yankee Stadium | 119 | AVOID |
| Citizens Bank | 114 | Risky |
| **Coors Field** | **106** | **OK - Acceptable** |
| Oriole Park | 105 | Moderate |
| Oracle Park | 82 | Excellent |
| PNC Park | 76 | SAFEST |

**Early Season Strategy (April-May when current-year data insufficient):**
1. Use 3-year rolling Statcast factors (most reliable)
2. Trust structural features (dimensions, altitude, marine layer)
3. Switch to current-year data by June

**Verdict:** ✅ VALIDATED - Use Statcast 3-year rolling, update monthly during season.

### ⚠️ SECRETARY PROBLEM APPLICABILITY

**Original claim:** Use secretary problem thresholds for streaming.

**User correction:** "Probable pitchers are known 1-1.5 weeks ahead" - we CAN plan the week.

**Verdict:** ❌ Secretary problem is WRONG model. Real uncertainty is:
- Will someone SNIPE the target before your day?
- Will you have a SLOT available?

**Correct model:** Resource-constrained scheduling (what we built in slot_scheduler.py)

### ⚠️ HOT/COLD STREAKS

| Claim | Evidence | Verdict |
|-------|----------|---------|
| "Hot hand" in baseball | DraftKings study: NO evidence of actual effect | ❌ MYTH |
| Players believe in hot hand | Same study: Yes, creates mispricing | ✅ EXPLOIT |

**Verdict:** Don't chase hot players, but FADE them (others overpay).

### ⚠️ DAY/NIGHT SPLITS

**Claim:** Some players are "day game guys"

**Evidence:** Year-to-year correlation < 0.05

**Verdict:** ❌ NOISE - don't use for streaming decisions.

### ⚠️ PITCHER-BATTER HISTORY (BvP)

**Claim:** Historical matchup data predicts future performance.

**Evidence:** Below 50 PA = essentially zero predictive value. Even at 50+ PA, only 1/3 weight.

**Verdict:** ❌ IGNORE for streaming (sample sizes too small).

---

## TIER 4: COMPLEXITY NOT WORTH IT

These are technically real but marginal gains don't justify complexity.

| Factor | Marginal Gain | Complexity | Verdict |
|--------|---------------|------------|---------|
| Humidity alone | <1% | LOW | ❌ Skip |
| Day/night splits | <1% | LOW | ❌ Skip |
| Recent hot/cold streaks | ~1% | LOW | ❌ Skip (noise) |
| Full Bayesian projection updates | +5% accuracy | HIGH | ⚠️ Maybe |
| Thompson Sampling vs UCB | +3-4x lower regret | MODERATE | ⚠️ Maybe |
| Colonel Blotto category allocation | Unknown | HIGH | ⚠️ For category leagues only |

---

## THE ACTUAL PRIORITY STACK

Based on validated impact, here's what to implement:

### MUST HAVE (Core System)

1. **Slot Scheduler** ✅ DONE
   - Exact optimization for streaming selection
   - Snipe risk modeling
   - Contingency planning

2. **Matchup Analyzer** ✅ DONE
   - ICM variance adjustment (leading/trailing)
   - Opponent activity prediction
   - Win probability

3. **Risk Analysis** ✅ DONE
   - Floor/ceiling projections
   - Disaster probability (Poisson)
   - Risk tiers

4. **Matchup Evaluator** (TO BUILD)
   - Pitcher: K-BB%, Stuff+, GB%
   - Opponent: Team K%, Team ISO
   - Park: Current-year HR factor (not historical!)

5. **Trade Analyzer** (TO BUILD)
   - Surplus detection
   - TTC algorithm for Pareto trades
   - Behavioral framing tactics

### SHOULD HAVE (Tiebreakers)

6. **Weather Integration**
   - HRFI for extreme conditions only (≤3 or ≥8)
   - Skip humidity, day/night

7. **Catcher Framing**
   - Top 5 / Bottom 5 as tiebreaker

8. **Umpire Data**
   - Only if assignments known before lineup lock
   - Otherwise skip

### NICE TO HAVE (Future)

9. Thompson Sampling (may beat UCB)
10. Bayesian projection updates mid-season
11. FAAB bid optimizer

---

## CONTRADICTIONS RESOLVED

| Topic | Research Says | Reality | Resolution |
|-------|---------------|---------|------------|
| **Coors** | "Never stream" | May be overstated | Validate with current data; contrarian opportunity |
| **Secretary Problem** | Use for streaming thresholds | Pitchers known in advance | Use slot scheduling model instead |
| **Park Factors** | Historical averages | Change over time | Use current-year only |
| **Hot Streaks** | Players are hot/cold | No evidence | Fade hot players (contrarian) |
| **BvP Data** | Check historical matchups | Too small samples | Ignore for streaming |
| **Complexity** | More factors = better | 70% variance from simple model | Keep it simple |

---

## THE SIMPLE MODEL THAT WORKS

**Research confirmed:** A basic model captures ~70% of predictable variance.

```
E[Points] = (K × 2) + (IP × 5) - (BB × 3) - (HR × 13)

Where projections adjusted by:
1. Pitcher baseline (K-BB%, Stuff+, GB%)     → 60%
2. Opponent (Team K%, Team ISO)              → 20%
3. Park factor (current year HR factor)       → 15%
4. Weather/Umpire (extremes only)            → 5%
```

**Don't overcomplicate.** The edge comes from:
1. Systematic application (not gut feel)
2. Risk management (avoiding disasters)
3. Slot optimization (timing of adds)
4. Opponent modeling (snipe risk, behavior prediction)
5. Trade detection (surplus/deficit matching)

---

## CONTRARIAN OPPORTUNITIES

The user's insight about Coors reveals a broader principle:

**Where conventional wisdom is WRONG, contrarian value exists:**

| Conventional Wisdom | Potential Contrarian Edge |
|---------------------|---------------------------|
| "Never stream at Coors" | Lower snipe risk, may not be as bad |
| "Chase hot hitters" | Fade them (overpriced) |
| "Closers essential" | Setup men nearly as valuable at fraction of cost |
| "Avoid low-AVG hitters" | High-walk hitters undervalued |
| "Speed wins" | <60% SB success = negative value |

**Key insight:** Your edge isn't just knowing what's RIGHT - it's knowing what others get WRONG.

---

## FINAL VALIDATION CHECKLIST

Before trusting any factor, verify:

1. **Sample size adequate?** (K-BB%: 150 PA, Stuff+: 80 pitches, GB%: 100 BIP)
2. **Year-to-year stable?** (Framing: 0.52-0.77 correlation, Day/Night: <0.05)
3. **Magnitude worth tracking?** (>2% impact or skip)
4. **Data available in time?** (Umpires: often too late)
5. **Current data, not historical?** (Park factors change)

---

*This synthesis represents the distillation of 7 research documents. Focus on TIER 1 validated findings. Use TIER 2 as tiebreakers. Be skeptical of TIER 3 conventional wisdom. Skip TIER 4 complexity.*
