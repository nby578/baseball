# Quantitative Methods for Sequential Resource Allocation Under Uncertainty

**Your fantasy baseball add allocation problem is formally a constrained stochastic sequential decision problem**—and multiple well-developed mathematical frameworks directly address it. This report provides the exact formulas, algorithms, and implementation paths for each approach, prioritizing methods that work with small samples and limited data.

The core problem—allocating 5 adds across 7 days to maximize expected points under uncertainty—maps precisely to **bandits with knapsacks** (BwK), with elements of **optimal stopping**, **MDPs with constraints**, and **portfolio optimization**. The most implementable solution combines a budgeted contextual bandit algorithm with threshold-based stopping rules and risk-adaptive utility functions for leading/trailing scenarios.

---

## Optimal stopping: threshold formulas for K selections from N candidates

The secretary problem with multiple selections provides the foundation for "when to pull the trigger" on a pickup.

### K-selection secretary problem threshold

For selecting up to K candidates from N sequential arrivals, Kleinberg (2005) established:

**Competitive ratio:**
$$\text{Ratio} = 1 - \frac{5}{\sqrt{k}}$$

For **k=5 adds**, this yields approximately **0.78** of the optimal sum (78% of what an omniscient selector achieves).

**Practical thresholds for k=5, N=30 options:**
```
Observation phase: Skip first ⌊N/e⌋ ≈ 11 options (just record values)
After observation: Accept if value exceeds all previously seen AND selection count allows
```

The recursive algorithm uses a random transition point with nested selection:

```python
def k_secretary(n, k, values_stream):
    """Kleinberg's multiple-choice secretary algorithm"""
    if k == 1:
        threshold_idx = int(n / 2.718)  # n/e
        best_so_far = max(values_stream[:threshold_idx]) if threshold_idx > 0 else -float('inf')
        for i in range(threshold_idx, n):
            if values_stream[i] > best_so_far:
                return [i]
        return [n-1]
    
    # k > 1: Split recursively
    m = np.random.binomial(n, 0.5)
    ell = k // 2
    phase1_selected = k_secretary(m, ell, values_stream[:m])
    
    phase1_values = sorted([values_stream[i] for i in phase1_selected], reverse=True)
    threshold = phase1_values[ell-1] if len(phase1_values) >= ell else -float('inf')
    
    selected = phase1_selected.copy()
    for i in range(m, n):
        if values_stream[i] > threshold and len(selected) < k:
            selected.append(i)
    return selected
```

**Complexity:** O(n log n); **Space:** O(n)

### Prophet inequalities for k-selection

When value distributions are known (e.g., you have projection confidence intervals), prophet inequalities bound performance:

**Single-threshold policy:**
$$T = \frac{1}{2} \cdot \mathbb{E}[\max_i X_i]$$

Accept the first option exceeding T. This guarantees **½ of the prophet's value** for single selection.

**For k selections (Alaei 2014):**
$$\text{Competitive Ratio} = 1 - \frac{1}{\sqrt{k+3}}$$

For k=5: ratio ≈ **0.65** with a single static threshold.

**Computing the k-selection threshold:**
```python
def prophet_k_threshold(distributions, k):
    """Find threshold φ such that E[min(k, count ≥ φ)] = k/2"""
    def expected_count(phi):
        return sum(1 - d.cdf(phi) for d in distributions)
    
    # Binary search for φ
    low, high = min(d.ppf(0.01) for d in distributions), max(d.ppf(0.99) for d in distributions)
    while high - low > 0.001:
        mid = (low + high) / 2
        if expected_count(mid) > k/2:
            low = mid
        else:
            high = mid
    return mid
```

### Pandora's box: when inspection has cost

When using an add to "see" a player's value (streaming a speculative pickup), the Weitzman index determines optimal exploration order.

**Reservation value σᵢ** for option i with inspection cost cᵢ:
$$c_i = \mathbb{E}[\max(v_i - \sigma_i, 0)] = \int_{\sigma_i}^{\infty}(1 - F_i(v))dv$$

**Optimal policy:** Open boxes in decreasing order of σᵢ. Stop when the best σ among unopened boxes is below the best value already seen. If you observe v > σ, claim immediately.

```python
def compute_reservation_value(cost, distribution_cdf, distribution_support):
    """Binary search for Weitzman index"""
    low, high = distribution_support
    while high - low > 1e-6:
        mid = (low + high) / 2
        expected_bonus = quad(lambda v: 1 - distribution_cdf(v), mid, high)[0]
        if expected_bonus > cost:
            low = mid
        else:
            high = mid
    return (low + high) / 2
```

**Key papers:** Kleinberg (2005) "A Multiple-Choice Secretary Algorithm"; Krengel & Sucheston (1978) for prophet inequalities; Weitzman (1979) "Optimal Search for the Best Alternative"

---

## MDP formulation with the Bellman equations

The full MDP framework provides optimal sequential decisions when state transitions are modeled.

### State space formulation

**State tuple:**
$$s = (t, n, \text{score}, \text{opp\_score}, A_t)$$

Where:
- **t ∈ {1,...,7}**: Current day
- **n ∈ {0,...,5}**: Remaining adds
- **score, opp_score**: Current point totals
- **A_t**: Available players (or feature representation)

The 5-add constraint is embedded directly in state variable n—no separate constrained MDP machinery needed.

### Finite-horizon Bellman optimality equation

$$V^*_t(s) = \max_{a \in A(s)} \left[ R(s,a) + \sum_{s'} P(s'|s,a) V^*_{t+1}(s') \right]$$

**Boundary condition (day 7):**
$$V^*_7(s) = \max_a [R(s,a) + R_{\text{terminal}}(s')]$$

**For the specific fantasy problem:**
$$V^*_t(n, \text{score}, \text{opp}, A) = \max_{k \in \{0,...,\min(n,|A|)\}} \left\{ \mathbb{E}[r_k] + \int V^*_{t+1}(n-k, \text{score}+r_k, \text{opp}', A') \, dP \right\}$$

### Value iteration pseudocode

```python
def finite_horizon_value_iteration(T=7, max_adds=5, states, transitions, rewards):
    V = {t: {} for t in range(T+2)}
    policy = {t: {} for t in range(1, T+1)}
    
    # Initialize terminal values
    for s in states:
        V[T+1][s] = 0
    
    # Backward induction
    for t in range(T, 0, -1):
        for s in states:
            n = s.remaining_adds
            best_value, best_action = -float('inf'), 0
            
            for a in range(min(n, max_actions_per_day) + 1):
                q_value = rewards(s, a)
                for s_prime, prob in transitions(s, a):
                    q_value += prob * V[t+1][s_prime]
                
                if q_value > best_value:
                    best_value, best_action = q_value, a
            
            V[t][s] = best_value
            policy[t][s] = best_action
    
    return V, policy
```

**Complexity:** O(T × |S|² × |A|) time, O(T × |S|) space. For 7 days with reasonable state discretization (score bins, opponent bins, player aggregates), this is tractable.

### Risk-sensitive extension for leading vs. trailing

When you're ahead, play conservatively; when behind, increase variance. Exponential utility MDPs capture this:

**Risk-sensitive Bellman equation:**
$$V(s) = \max_a \left\{ R(s,a) + \frac{1}{\theta} \log \mathbb{E}[\exp(\theta V(s'))] \right\}$$

- **θ > 0**: Risk-averse (protect lead)
- **θ < 0**: Risk-seeking (need variance to catch up)
- **θ → 0**: Risk-neutral (standard MDP)

```python
def adaptive_risk_parameter(score_margin, days_remaining):
    if score_margin > 30 and days_remaining <= 2:
        return 2.0   # Very risk-averse: protect large lead
    elif score_margin > 10:
        return 0.5   # Mildly risk-averse
    elif score_margin < -20:
        return -2.0  # Risk-seeking: need variance
    else:
        return 0.0   # Risk-neutral
```

**Key papers:** Puterman (1994) "Markov Decision Processes"; Bertsekas (2012) "Dynamic Programming and Optimal Control"; Howard & Matheson (1972) for exponential utility MDPs

**Libraries:** `stable-baselines3`, `gymnasium`, `cvxpy` for LP formulations

---

## Bandits with knapsacks: the direct model

Your problem maps exactly to **Contextual Bandits with Knapsacks (BwK)**—this is the most directly applicable framework.

### Problem formulation (Badanidiyuru et al. 2018)

- **K arms** (available pickups), **T rounds** (7 days), **B budget** (5 adds)
- Each pull yields reward r_t(a) and consumes cost c_t(a) = 1
- Stop when budget depleted

**Optimal benchmark (LP relaxation):**
$$\max_{\pi} \mathbb{E}\left[\sum_t r_t(\pi)\right] \quad \text{s.t.} \quad \mathbb{E}\left[\sum_t c_t(\pi)\right] \leq B$$

### UCB formula for budget-constrained contextual bandits

**The exact formula:**
$$\text{UCB}_t(a) = \frac{\hat{\mu}_t(a) + \text{conf}_r(t,a)}{\max\{\hat{c}_t(a) - \text{conf}_c(t,a), \epsilon\}}$$

Where confidence terms are:
$$\text{conf}_r(t,a) = \alpha \sqrt{\frac{\ln t}{N_t(a)}}$$

**Budget-adjusted exploration:**
$$f(\text{conf}, B_{\text{remain}}, T_{\text{remain}}) = \alpha \sqrt{\frac{\ln t}{N_t(a)}} \cdot \left(1 + \beta \cdot \frac{B_{\text{remain}}/B_{\text{total}}}{T_{\text{remain}}/T_{\text{total}}}\right)$$

When budget/time ratio is high, explore more; when low, exploit aggressively.

**For linear contexts (LinUCB-BwK):**
$$\text{UCB}_t(a) = x_t(a)^T \hat{\theta}_r + \alpha_r \|x_t(a)\|_{A_t^{-1}}$$

Where A_t = I + Σ x_τ x_τ^T is the design matrix.

### Implementation

```python
class BudgetedLinUCB:
    def __init__(self, n_arms, d, budget, time_horizon, alpha=1.0):
        self.A = [np.eye(d) for _ in range(n_arms)]  # d×d matrices
        self.b = [np.zeros(d) for _ in range(n_arms)]  # d×1 vectors
        self.budget_remaining = budget
        self.time_remaining = time_horizon
        self.alpha = alpha
        
    def select_arm(self, contexts, available_arms, deadlines=None):
        if self.budget_remaining <= 0:
            return None
        
        # Adjust exploration based on budget/time ratio
        budget_ratio = self.budget_remaining / self.budget
        time_ratio = self.time_remaining / self.time_horizon
        adjusted_alpha = self.alpha * (budget_ratio / max(time_ratio, 0.1))
        
        ucb_values = []
        for a in available_arms:
            A_inv = np.linalg.inv(self.A[a])
            theta = A_inv @ self.b[a]
            x = contexts[a]
            
            mean = theta @ x
            confidence = adjusted_alpha * np.sqrt(x @ A_inv @ x)
            ucb = mean + confidence
            
            # Urgency bonus for expiring options
            if deadlines and deadlines[a]:
                urgency = 1.0 / max(deadlines[a] - self.time_remaining, 1)
                ucb += 0.5 * urgency
            
            ucb_values.append((a, ucb))
        
        return max(ucb_values, key=lambda x: x[1])[0]
    
    def update(self, arm, context, reward):
        self.A[arm] += np.outer(context, context)
        self.b[arm] += reward * context
        self.budget_remaining -= 1
        self.time_remaining -= 1
```

### Regret bounds

**BwK regret (Badanidiyuru et al.):**
$$\text{Regret} \leq O\left(\text{OPT} \cdot \sqrt{\frac{K \ln K \ln T}{B}}\right)$$

**Contextual BwK (linear):**
$$\text{Regret} \leq \tilde{O}\left(\left(\frac{\text{OPT}}{B} + 1\right) \cdot m \cdot \sqrt{T}\right)$$

For your problem (K≈20, T=7, B=5, m≈15): Regret ≈ O(15·√7) ≈ **40 points** suboptimality bound.

### Thompson Sampling variant

```python
class BudgetedThompsonSampling:
    def __init__(self, n_arms, budget):
        self.alpha_r = np.ones(n_arms)  # Beta prior: successes
        self.beta_r = np.ones(n_arms)   # Beta prior: failures
        self.budget_remaining = budget
        
    def select_arm(self, available_arms):
        # Sample from posterior
        theta = np.array([np.random.beta(self.alpha_r[a], self.beta_r[a]) 
                         for a in available_arms])
        return available_arms[np.argmax(theta)]
    
    def update(self, arm, reward_success):
        if reward_success:
            self.alpha_r[arm] += 1
        else:
            self.beta_r[arm] += 1
        self.budget_remaining -= 1
```

**Key papers:** Badanidiyuru, Kleinberg, Slivkins (2018) "Bandits with Knapsacks"; Agrawal & Goyal (2013) "Thompson Sampling for Contextual Bandits"

**Libraries:** `vowpalwabbit`, `contextualbandits` (Python package), custom NumPy implementation

---

## Multi-asset Kelly criterion for correlated bets

When making multiple simultaneous pickups with correlated outcomes, the Kelly criterion provides optimal sizing.

### Matrix formulation

**Optimal allocation:**
$$f^* = \Sigma^{-1} \mu$$

Where:
- **f*** = Fraction vector (how much "weight" to each pickup)
- **Σ** = Covariance matrix of player performances
- **μ** = Expected excess returns (projected points above replacement)

**Fractional Kelly (always use in practice):**
$$f_{\text{fractional}} = k \cdot f^* \quad \text{where } k \in [0.25, 0.5]$$

Half-Kelly returns 75% of optimal profit with only 25% of the variance—essential when estimates are uncertain.

### Ledoit-Wolf shrinkage for small samples

With only ~25 weeks of data, sample covariance is unreliable. Shrinkage toward identity:

$$\hat{\Sigma}_{\text{shrunk}} = \delta \cdot F + (1-\delta) \cdot S$$

Where S is sample covariance, F = (tr(S)/p)·I is scaled identity, and δ ∈ [0,1] is optimal shrinkage intensity.

```python
from sklearn.covariance import LedoitWolf

lw = LedoitWolf()
lw.fit(player_performance_matrix)  # Shape: (n_games, n_players)
shrunk_cov = lw.covariance_
shrinkage_used = lw.shrinkage_  # Typically 0.3-0.7 for small samples
```

### Implementation

```python
def multi_asset_kelly(expected_returns, cov_matrix, fraction=0.5):
    """Fractional Kelly allocation for correlated assets"""
    precision = np.linalg.inv(cov_matrix)
    full_kelly = precision @ expected_returns
    
    # Constrain to positive weights, sum to 1
    weights = np.maximum(fraction * full_kelly, 0)
    if weights.sum() > 0:
        weights = weights / weights.sum()
    
    return weights
```

**Key papers:** Thorp (2011) "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"; Ledoit & Wolf (2004) "A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices"

**Libraries:** `sklearn.covariance.LedoitWolf`, `pypfopt.risk_models.CovarianceShrinkage`

---

## Bayesian updating of projections mid-season

As games are played, update pre-season projections with observed performance using conjugate priors.

### Normal-Normal update (for fantasy points)

**Prior:** Pre-season projection μ₀ with uncertainty σ₀  
**Likelihood:** Observed mean x̄ over n games with known variance σ²

**Posterior mean:**
$$\mu_{\text{post}} = \frac{\frac{\mu_0}{\sigma_0^2} + \frac{n\bar{x}}{\sigma^2}}{\frac{1}{\sigma_0^2} + \frac{n}{\sigma^2}}$$

**Posterior variance:**
$$\sigma_{\text{post}}^2 = \frac{1}{\frac{1}{\sigma_0^2} + \frac{n}{\sigma^2}}$$

```python
def bayesian_update_projection(prior_mean, prior_std, observed_mean, observed_std, n_games):
    prior_precision = 1 / prior_std**2
    obs_precision = n_games / observed_std**2
    
    post_precision = prior_precision + obs_precision
    post_mean = (prior_precision * prior_mean + obs_precision * observed_mean) / post_precision
    post_std = np.sqrt(1 / post_precision)
    
    return post_mean, post_std
```

**Example:** Pre-season projection: 25 HR (σ₀=5). After 50 games, player on pace for 18 HR. With league σ=8:
- Posterior mean ≈ 22 HR (weighted average favoring larger sample)
- Posterior std ≈ 3.5 (uncertainty reduced)

### Beta-Binomial for rate stats

For batting average, on-base percentage:
- **Prior:** Beta(α, β) where α/(α+β) = projected rate
- **After k hits in n AB:** Beta(α+k, β+n-k)

```python
def update_batting_avg(prior_alpha, prior_beta, hits, at_bats):
    """Return posterior Beta distribution for batting average"""
    return scipy.stats.beta(prior_alpha + hits, prior_beta + at_bats - hits)
```

**Key papers:** Jensen et al. (2009) "Hierarchical Bayesian Modeling of Hitting Performance"

---

## Projection aggregation: optimal weighting of sources

Combine ESPN, Yahoo, FanGraphs projections optimally.

### Inverse variance weighting

$$\hat{x} = \frac{\sum_i w_i x_i}{\sum_i w_i} \quad \text{where } w_i = \frac{1}{\sigma_i^2}$$

Weight each source by inverse of its historical mean squared error:

```python
def combine_projections(projections, historical_errors):
    """projections: dict of source -> value; historical_errors: dict of source -> list of past errors"""
    mse = {source: np.mean(np.array(errors)**2) for source, errors in historical_errors.items()}
    weights = {source: 1/mse[source] for source in projections}
    total_weight = sum(weights.values())
    
    combined = sum(projections[s] * weights[s] for s in projections) / total_weight
    combined_var = 1 / total_weight
    
    return combined, np.sqrt(combined_var)
```

**Key papers:** Satopää et al. (2014) "Combining Multiple Probability Predictions"; Bates & Granger (1969) "The Combination of Forecasts"

---

## DFS integer programming for lineup optimization

While your problem is sequential, the single-day optimization is a standard IP.

### Formulation

$$\max \sum_i p_i x_i \quad \text{(maximize projected points)}$$

Subject to:
- $\sum_i c_i x_i \leq B$ (salary cap)
- $\sum_{i \in P} x_i = n_P$ (positional requirements)
- $\sum_{i \in T} x_i \leq 4$ (max per team)
- $x_i \in \{0, 1\}$

```python
from pulp import LpProblem, LpVariable, LpMaximize, lpSum

prob = LpProblem("DFS", LpMaximize)
x = {p: LpVariable(f"x_{p}", cat='Binary') for p in players}

prob += lpSum(projections[p] * x[p] for p in players)
prob += lpSum(salary[p] * x[p] for p in players) <= 50000

for pos, required in position_requirements.items():
    prob += lpSum(x[p] for p in players if positions[p] == pos) == required

prob.solve()
optimal_lineup = [p for p in players if x[p].value() == 1]
```

### Stacking correlations (quantified)

| Stack Type | Correlation |
|------------|-------------|
| QB-WR1 (same team) | **0.53-0.55** |
| QB-TE1 | 0.47-0.49 |
| QB-opposing QB | **0.58** (game environment) |
| QB-opposing WR | 0.37 (bring-back) |

**Lineup variance with correlation:**
$$\text{Var}(\text{Lineup}) = \sum_i w_i^2 \sigma_i^2 + \sum_{i \neq j} w_i w_j \rho_{ij} \sigma_i \sigma_j$$

Stacking increases variance, improving GPP ceiling.

**Key papers:** Hunter, Vielma, Zaman (2016) "Picking Winners in Daily Fantasy Sports Using Integer Programming"; Haugh & Singal (2021) "How to Play Fantasy Sports Strategically"

**Libraries:** `PuLP`, `cvxpy`, `OR-Tools`

---

## Monte Carlo tree search for sequential decisions

MCTS explores the decision tree of sequential add choices.

### UCT formula

$$\text{UCT}(s,a) = Q(s,a) + C_p \sqrt{\frac{\ln N(s)}{N(s,a)}}$$

Where:
- Q(s,a) = Average reward from action a in state s
- N(s) = Visit count for state s
- C_p = Exploration constant (typically √2)

```python
def mcts(root_state, iterations=1000, Cp=1.41):
    root = Node(root_state)
    
    for _ in range(iterations):
        node, state = root, root_state.copy()
        
        # Selection
        while node.fully_expanded() and not state.terminal:
            node = max(node.children, key=lambda c: c.wins/c.visits + Cp*np.sqrt(np.log(node.visits)/c.visits))
            state.apply(node.action)
        
        # Expansion
        if not state.terminal:
            action = node.untried_actions.pop()
            state.apply(action)
            node = node.add_child(action, state)
        
        # Simulation (random playout)
        while not state.terminal:
            state.apply(random.choice(state.legal_actions()))
        
        # Backpropagation
        reward = state.get_reward()
        while node:
            node.visits += 1
            node.wins += reward
            node = node.parent
    
    return max(root.children, key=lambda c: c.visits).action
```

**Complexity:** O(iterations × depth × branching_factor)

---

## Risk parity formula for diversification

Allocate pickups so no single player dominates risk.

**Marginal risk contribution:**
$$\text{MRC}_i = \frac{(\Sigma w)_i}{\sigma_p}$$

**Risk parity condition (equal risk contribution):**
$$w_i \cdot \text{MRC}_i = w_j \cdot \text{MRC}_j \quad \forall i,j$$

**Naïve approximation (inverse volatility):**
$$w_i \propto \frac{1}{\sigma_i}$$

```python
def naive_risk_parity(volatilities):
    inv_vol = 1 / np.array(volatilities)
    return inv_vol / inv_vol.sum()
```

---

## Newsvendor formula for contingency reserves

How many adds to reserve for unexpected IL activations?

$$Q^* = F^{-1}\left(\frac{C_u}{C_u + C_o}\right)$$

Where:
- C_u = Cost of underage (missing a valuable activation)
- C_o = Cost of overage (wasting an add on speculation)
- F⁻¹ = Inverse CDF of "need for emergency adds"

**For fantasy:** If missing a key IL activation costs ~15 points and wasting an add costs ~5 points of opportunity:
$$\text{Critical fractile} = \frac{15}{15+5} = 0.75$$

Reserve capacity at the 75th percentile of expected emergency need—typically **1-2 adds**.

---

## Recommended implementation approach

**Primary algorithm:** Budgeted LinUCB with deadline urgency bonuses
- Handles context (player stats, matchups)
- Respects budget constraint naturally
- Adapts exploration to budget/time ratio

**Enhancements:**
1. **Bayesian projection updates** as games are played
2. **Ledoit-Wolf shrinkage** for covariance estimation
3. **Risk-adaptive utility** based on score margin
4. **Newsvendor reserve** of 1-2 adds for contingencies

**Context vector features:**
```python
context = [
    player_war, recent_7day_avg, career_vs_opponent,
    matchup_pitcher_era, park_factor, is_home,
    days_until_deadline / 7, games_remaining_this_week,
    injury_probability, two_start_indicator
]
```

**Decision threshold (simplified):**
$$\text{Add player if: } \mathbb{E}[\text{Points}] > \tau + \frac{\text{adds\_remaining}}{\text{days\_remaining}} \cdot \sigma_{\text{opportunity}}$$

Where τ is your baseline threshold and σ_opportunity is the standard deviation of expected future pickup quality.

---

## Computational complexity summary

| Method | Time | Space | Tractable? |
|--------|------|-------|------------|
| K-secretary | O(n log n) | O(n) | ✓ |
| Prophet threshold | O(n × distribution calls) | O(n) | ✓ |
| Finite-horizon MDP | O(T × \|S\|² × \|A\|) | O(T × \|S\|) | ✓ with state aggregation |
| LinUCB | O(d³) per update | O(Kd²) | ✓ |
| MCTS | O(iterations × depth) | O(tree size) | ✓ |
| Full Bellman | Exponential in raw state | — | ✗ without approximation |

For your 7-day, 5-add problem with ~20 daily options: **all methods are tractable** with appropriate discretization.

---

## Key Python libraries

| Purpose | Library |
|---------|---------|
| Optimization | `cvxpy`, `PuLP`, `scipy.optimize` |
| Bandits | `vowpalwabbit`, `contextualbandits` |
| Covariance shrinkage | `sklearn.covariance.LedoitWolf` |
| Portfolio optimization | `pypfopt` |
| RL/MDPs | `stable-baselines3`, `gymnasium` |
| Simulation | `numpy.random`, `scipy.stats` |

---

## Seminal papers by area

**Optimal Stopping:** Kleinberg (2005) "A Multiple-Choice Secretary Algorithm" • Krengel & Sucheston (1978) prophet inequalities • Weitzman (1979) "Optimal Search for the Best Alternative"

**MDPs:** Puterman (1994) "Markov Decision Processes" • Altman (1999) "Constrained Markov Decision Processes"

**Bandits:** Badanidiyuru et al. (2018) "Bandits with Knapsacks" • Agrawal & Goyal (2013) "Thompson Sampling for Contextual Bandits"

**Portfolio:** Ledoit & Wolf (2004) shrinkage estimators • Black & Litterman (1992) combining views

**DFS:** Hunter, Vielma, Zaman (2016) "Picking Winners" • Haugh & Singal (2021) "How to Play Fantasy Sports Strategically"