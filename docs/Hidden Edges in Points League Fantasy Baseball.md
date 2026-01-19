# Hidden Edges in Points League Fantasy Baseball

In your specific scoring system—where **HR allowed costs -13 points** (erasing 2.5 clean innings), **holds pay 82% of save value**, and **walks equal 65% of singles**—several market inefficiencies emerge that most fantasy managers miss. The biggest exploitable edges involve ground ball pitchers, elite setup men, weather-based streaming, and catcher-pitcher pairings. Below are research-backed findings with specific thresholds and actionable strategies for your league format.

---

## Platoon splits are real, but heavily regress toward the mean

**Conventional wisdom:** Players with big platoon splits should be platooned; target "platoon killers."

**Reality:** League-wide, left-handed hitters gain **~43 points of wOBA** (8.6%) against right-handed pitching, while right-handers gain **~32 points of wOBA** (6.1%) versus lefties. However, individual player splits require massive samples to stabilize—**1,000 PA for LHH vs LHP** and a staggering **2,200 PA for RHH vs LHP**—meaning most "extreme split" players are experiencing noise, not skill.

| Matchup Advantage | wOBA Gain | Sample to Stabilize |
|-------------------|-----------|---------------------|
| LHH vs RHP | +43 pts (~8.6%) | 1,000 PA |
| RHH vs LHP | +32 pts (~6.1%) | 2,200 PA |

The sticky skill component in platoon splits is **K% and BB% differential**, not raw power. Hitters consistently strike out less and walk more against opposite-handed pitchers, which matters hugely with your **+3 walk, -1 AB** scoring. Pitch type matters too: sinkers and sliders show large platoon effects, while curveballs and changeups show **reverse splits**—so don't stack lefties against RHP curveball specialists like McCullers or Morton.

**Exploitation strategy:** Use league-average platoon advantages when streaming hitters (+8.6% for LHH vs RHP stacks). Don't chase individual player splits unless you have 500+ PA in that matchup. Prioritize walks and OBP—your scoring makes a walk worth 3 points with no AB penalty.

---

## Day/night splits are noise—don't waste lineup moves on them

**Conventional wisdom:** Some players are "day game guys" who rake in afternoon contests.

**Reality:** Year-to-year correlation for day/night performance is below 0.05, meaning if a player hit better in day games one year, it has almost zero predictive value for the next. Research testing swing rate and contact rate (which stabilize at ~50 PA) found day/night splits are *worse predictors than pitcher BABIP*—essentially random.

The one exploitable pattern: **day games after night games** often feature backup catchers and rested veterans. Stream pitchers facing fatigued lineups in these spots rather than trying to find "day game hitters."

---

## Ground ball rate is your best friend for pitcher HR suppression

**Conventional wisdom:** High-spin fastballs and pitch sequencing prevent home runs.

**Reality:** Driveline Baseball's rigorous study found **no evidence supporting Effective Velocity sequencing theory** at the MLB level—the supposed "pitches within 6 EV MPH" rule is confounded by count effects. What actually predicts HR suppression is simpler: **ground ball rate above 45%** and **barrel rate allowed below 7%**.

The numbers are stark: fly ball pitchers allow home runs **25% more often** than ground ball pitchers. In one comparison, Dallas Keuchel (19.3% FB rate) surrendered 1 HR per 73 batters, while Jered Weaver (47.9% FB rate) gave up 1 HR per 33 batters—with similar K% and HR/FB%.

| GB% Classification | Threshold | HR Risk |
|-------------------|-----------|---------|
| Extreme GB | >50% | **Lowest** |
| Ground Ball Pitcher | 45-50% | Low |
| Neutral | 40-45% | Average |
| Fly Ball Pitcher | <40% | **Avoid** |

High-spin fastballs suppress batting average (.192 vs .259 for low spin) but don't automatically reduce HRs—Scherzer and Verlander rank elite in spin yet allowed among the most long balls. The myth that ground ballers have higher HR/FB because their fly balls are "mistakes" is false—correlation between GB% and HR/FB is **-0.05** (nonexistent).

**Exploitation strategy:** With your **-13 HR allowed** penalty erasing 2.5 innings of work, prioritize **sinker-heavy pitchers with GB% above 45%** and barrel rate under 7%. Model targets: Framber Valdez, Logan Webb, Alex Cobb. Avoid four-seam dominant pitchers (>60% usage) in hitter-friendly parks regardless of velocity or spin rate.

---

## Elite catcher framers are worth 1-4 fantasy points per start

**Conventional wisdom:** Catcher framing doesn't matter for fantasy.

**Reality:** The gap between the best and worst MLB framers is **38 runs per season**—translating to roughly **2 extra strikes per game** for pitchers throwing to elite framers. In your scoring where a called strike that becomes a strikeout versus a walk means a **5-point swing** (K: +2 vs BB: -3), catcher framing creates a measurable edge.

| Catcher | Team | 2024 Framing Runs | Shadow Zone Strike % |
|---------|------|-------------------|---------------------|
| **Patrick Bailey** | Giants | +16 | 52.7% (best) |
| **Cal Raleigh** | Mariners | +13 | ~50% |
| **Austin Wells** | Yankees | +12 | ~49% |
| **Jose Trevino** | Reds | +10 | ~51% |
| Edgar Quero | White Sox | -13 | ~40% (worst) |

Framing is highly stable year-to-year (correlation 0.52-0.77), meaning elite framers stay elite. Per start, expect **1-2 extra fantasy points** streaming to an elite framer versus average, or **2-4 points** versus the worst framers.

**Exploitation strategy:** Use catcher matchups as a tiebreaker between similar streaming options. Favor pitchers throwing to Bailey, Raleigh, Wells, Kirk, or Trevino. Avoid streaming pitchers to the White Sox (Quero) or Nationals (Adams).

---

## Setup men are drastically undervalued when holds pay 82% of saves

**Conventional wisdom:** Closers are essential; holds are afterthoughts.

**Reality:** With your **+11 saves, +9 holds** scoring, elite setup men provide comparable value to closers while costing 50-100 fewer draft picks. The league produces **52% more holds than saves** annually, and 100+ pitchers earn 10+ holds versus only 39 earning 10+ saves.

Consider the math for an elite setup man producing 25 holds, 70 IP, and 85 K's:
- 25 holds × 9 = **225 points**
- 70 IP × 5 = **350 points**
- 85 K × 2 = **170 points**
- **Total: 745+ points** (before ratio factors)

A mid-tier closer with 30 saves, 55 IP, 60 K's produces roughly 775 points—a negligible advantage for a massive ADP premium.

| Target Setup Men | Team | 2024 Holds | K's | ERA |
|-----------------|------|------------|-----|-----|
| Jason Adam | Padres | 22 | 70 | 1.93 |
| Bryan Abreu | Astros | 21 | **105** | 2.28 |
| Garrett Whitlock | Red Sox | 22 | 91 | 2.25 |
| Jeremiah Estrada | Padres | 23 | **108** | 3.45 |
| Griffin Jax | Rays | 24 | 99 | Versatile |

**Closers-in-waiting to roster:** Porter Hodge (Cubs), Orion Kerkering (Phillies), Justin Martinez (D-backs—5-year extension at age 23), Lucas Erceg (Royals), Cade Smith (Guardians—47% closer probability per ESPN).

**Exploitation strategy:** Don't overpay for closers. Target high-gmLI (>1.4) relievers on winning teams who generate 20-30 holds plus elite strikeout rates. Monitor the Cubs (Pressly aging), Reds (Pagan vulnerable), and Cardinals (Helsley trade candidate) for mid-season closer changes.

---

## Weather creates the largest single-game swings in expected HRs

**Conventional wisdom:** Weather effects are minor curiosities.

**Reality:** Temperature and wind create massive, predictable swings in home run probability. Research shows approximately **4 feet of additional carry per 10°F**, resulting in **63% more home runs** in extremely hot weather versus cold. Wind effects are even more dramatic: **5 mph wind blowing out adds 18-20 feet** to fly balls, with extreme conditions shifting landing spots up to 100 feet.

| HRFI Score | Avg HR/Game | Avg Runs/Game |
|------------|-------------|---------------|
| 1-2 (Cold/unfavorable) | **1.40** | 7.51 |
| 9-10 (Hot/favorable) | **2.61** | 10.04 |

That's an **86% increase in HR rate** between the most and least favorable conditions.

Wind-sensitive parks where streaming decisions matter most:
- **Wrigley Field**: 23% HR/FB with wind out vs 13% with wind in—a 50% swing
- **Oracle Park**: Average 18 mph wind (highest in MLB); ~1 in 3 games have wind-influenced HR outcomes
- **Kauffman Stadium**: 67 wind-prevented HRs in recent season (most in MLB)

**Exploitation strategy:** Check the **Home Run Forecast Index** (homerunforecast.com) before setting lineups—it's free and updated hourly. Start pitchers when HRFI is 1-3 (cold, wind in). Bench pitchers at Wrigley or Coors when HRFI exceeds 8. With your **-13 HR allowed** penalty, weather-based streaming is high-leverage.

---

## Reliever fatigue follows predictable velocity drops after three consecutive days

**Conventional wisdom:** Monitor reliever workload loosely.

**Reality:** PITCHf/x data shows a clear pattern: relievers lose **~0.5 mph on back-to-back days**, but three consecutive days of use drops velocity by **nearly 2 mph**—a massive performance hit.

| Days Worked | Fastball Velocity |
|-------------|-------------------|
| Back-to-back | 91.0 mph |
| 1 day rest | 91.6 mph |
| 3 straight days | **89.2 mph** |
| 5+ days rest | 91.1 mph |

ESPN's "Tired Reliever" formula flags: **25+ pitches previous day**, OR **35+ pitches over last 3 days**, OR **appearances in both prior 2 days**.

**Eastward travel** also hurts performance measurably: a Northwestern study using 20 years of MLB data found home teams after traveling east **lose their entire 4% home field advantage**. Pitchers allow **~0.1-0.2 more runs per game** and more HRs after eastward travel.

**Exploitation strategy:** Avoid starting relievers working their third consecutive day—expect meaningful velocity and command decline. Target pitchers facing teams that just returned from West Coast road trips (eastward travel fatigue). Check Monday/Thursday off-days to identify when bullpens are fully rested.

---

## Umpire zones vary by 22% in strikeout rates—check assignments pre-game

**Conventional wisdom:** Umpires are roughly interchangeable.

**Reality:** Extreme umpires show **22% variation in strikeout rates** from the mean. Pitcher-friendly umps like Doug Eddings and D.J. Reyburn generate 22% more strikeouts per game, while hitter-friendly umps like Marvin Hudson and Chris Guccione produce 12% fewer.

Zone accuracy on borderline pitches is only ~81%, with **9% of all called pitches incorrect**. The 2025 rule change shrinking the evaluation "buffer zone" from 2 inches to 0.75 inches has effectively shrunk the called strike zone, producing fewer edge strikes.

**Fantasy impact:** With your scoring (K: +2, BB: -3), a pitcher-friendly ump adding 1-2 extra called strikes per game could mean **1-4 extra fantasy points per start**—significant for streaming decisions.

**Exploitation strategy:** Check umpire assignments **1-3 hours before gametime** at umpscorecards.com or evanalytics.com. Use as a tiebreaker between similar streaming options. In DFS, stack hitters against hitter-friendly umps.

---

## High-walk hitters are undervalued; pure speed is overvalued in points leagues

**Conventional wisdom:** Points leagues and roto leagues require similar roster construction.

**Reality:** Your scoring creates several systematic biases most managers miss:

**Walks are premium:** With no AB penalty on walks (+3 points) versus the **-1 AB penalty on all plate appearances**, high-walk hitters gain hidden value. Kyle Schwarber's 80+ walks equal 240+ points annually—equivalent to 50+ singles—yet he's often discounted for low batting average. Jonathan India's 80 walks made him the **52nd-best points league hitter** despite middling roto value.

**Speed is overrated:** Your SB/CS scoring (+1.9/-2.8) requires **60%+ success rate to break even**. With league-wide CS rate at 21.3% and improving, marginal base stealers destroy value. Worse, speed peaks at age **22 for sprint speed** and **25-26 for steals**, declining rapidly thereafter—elite speedsters lose ~7 steals by age 30.

**Workhorse starters dominate:** IP accumulation matters enormously. Pablo López finished **top-20 in points** despite a 4.08 ERA because he logged 200+ innings. Michael King and Sonny Gray cracked the top-10 via 200+ strikeouts.

**Middle relievers without saves are useless:** No reliever with fewer than 10 saves finished in the top-80 pitchers in points leagues. The ratio benefits don't translate without counting stats.

| Market Bias | Correction |
|------------|------------|
| Closers essential | Setup men with holds nearly equivalent value |
| Speed premium | Break-even requires 60%+ success; avoid pure speed |
| Low-AVG hitters penalized | High walks offset; Schwarber-types gain value |
| Aging curves at 27-29 | Modern data shows hitters only decline from arrival |
| SP ratios over volume | IP matters more; draft workhorses early |

---

## Actionable thresholds for roster management and streaming

| Category | Threshold | Action |
|----------|-----------|--------|
| GB% for pitchers | >45% | **Prioritize** (avoid <40%) |
| Barrel% allowed | <7% | Strong HR suppression indicator |
| gmLI for relievers | >1.4 | High-leverage hold opportunities |
| Reliever consecutive days | 3+ days | **Bench**—expect 2 mph velocity drop |
| Weather HRFI | 1-3 | Start pitchers; 8+ = bench pitchers |
| Temperature | <60°F | Pitcher-friendly; >80°F = hitter-friendly |
| Catcher framing | Top 5 | +1-4 pts per start streaming advantage |
| Umpire assignment | Check 1-3 hours pre-game | Tiebreaker for streaming |
| Platoon advantage | LHH vs RHP | ~8.6% wOBA gain (use for stacks) |
| SB success rate | <60% | Negative expected value |

The cumulative edge from systematically exploiting these inefficiencies—rostering elite-ratio setup men, streaming by weather and catcher, avoiding fly ball pitchers—compounds over a 162-game season into a significant competitive advantage in your points format.