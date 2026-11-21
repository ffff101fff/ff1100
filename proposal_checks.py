"""Proposal section 2.4: sensitivity, event contrasts, persistence and exact ranks."""
from itertools import combinations
from math import erfc, sqrt

import numpy as np
import pandas as pd

import analysis


def olympic_contrast(wide, olympics, lag):
    # Relative to the geometric mean of the four other sports; year fixed effects.
    others = wide.drop(columns="fencing")
    y = np.log(wide.fencing) - np.log(others).mean(axis=1)
    event = np.zeros(len(y))
    for game in olympics.itertuples():
        event[(y.index >= game.start) & (y.index <= game.end)] = 1
    year = pd.get_dummies(y.index.year, drop_first=True, dtype=float)
    x = np.column_stack([np.ones(len(y)), event, year])
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    scores = x * (y - x @ beta).to_numpy()[:, None]
    meat = scores.T @ scores
    for h in range(1, lag + 1):
        cross = scores[h:].T @ scores[:-h]
        meat += (1 - h / (lag + 1)) * (cross + cross.T)
    bread = np.linalg.inv(x.T @ x)
    se = sqrt((bread @ meat @ bread)[1, 1])
    return dict(days=len(y), event_days=int(event.sum()), lag=lag,
                ratio=np.exp(beta[1]), low=np.exp(beta[1]-1.96*se),
                high=np.exp(beta[1]+1.96*se), p=erfc(abs(beta[1]/se)/sqrt(2)))


def exact_u(group, other):
    values = np.r_[group, other]
    n = len(group)
    ranks = pd.Series(values).rank().to_numpy()
    center = n * (len(values)+1)/2
    observed = ranks[:n].sum()
    distances = [abs(ranks[list(ix)].sum()-center) for ix in combinations(range(len(values)), n)]
    return dict(n=n, m=len(other), fencing_median=np.median(group), other_median=np.median(other),
                U=observed-n*(n+1)/2, permutations=len(distances),
                p=np.mean(np.asarray(distances)>=abs(observed-center)))


def main():
    data, athletes, games = analysis.load()
    for k in (1, 3, 10):
        _, summary = analysis.topk_share(data, k)
        print("Top days", k, summary["median"].unstack().round(2).to_string())
    olympics = games[games.type == "olympics"]
    for region in ("ko", "en"):
        wide = data[(data.source=="wikipedia") & (data.region==region)].pivot(
            index="date", columns="sport", values="value_norm").sort_index().loc["2016":"2025"]
        for lag in (7, 30):
            print(region, "HAC", olympic_contrast(wide, olympics, lag))
        full = analysis.series(data, "wikipedia", region, "fencing")
        for game in olympics.itertuples():
            # Equal 31-day windows, avoiding the 30-day buffer on either side.
            day = pd.Timedelta(days=1)
            before = full.loc[game.start-90*day:game.start-60*day]
            after = full.loc[game.end+60*day:game.end+90*day]
            if len(before)==len(after)==31:
                print(region, game.name, "retention", round(after.mean()/before.mean(),3))
    metrics = analysis.athlete_metrics(athletes, games)
    ko = metrics[metrics.region=="ko"]
    print("Exact U", exact_u(ko.loc[ko.sport=="fencing","games_share"],
                             ko.loc[ko.sport!="fencing","games_share"]))
    for region in ("korea", "world"):
        gt=data[(data.source=="google_trends") & (data.region==region) & (data.sport=="fencing")]
        marked = gt.date.dt.to_period("M").isin(set(olympics.start.dt.to_period("M")) | set(olympics.end.dt.to_period("M")))
        print(region,"Trends Olympic months / other months (median)",
              gt.loc[marked,"value"].median(),gt.loc[~marked,"value"].median())


if __name__ == "__main__":
    main()
