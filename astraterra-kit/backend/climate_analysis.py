import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pymannkendall as mk
import matplotlib.pyplot as plt
import numpy as np

def trends(df):
    feature_columns = {
        "summer_tmax_c",
        "summer_rain_mm",
        "summer_soil_moisture_root",
        "is_heat_days"
    }


def year_types(yearly):
    """Cluster yearly summer conditions into three readable weather types.

    ``yearly`` is indexed by year. The features are standardized before
    clustering so rainfall, temperature, and soil moisture contribute equally.
    """
    feature_columns = [
        "summer_rain_mm",
        "summer_tmax_c",
        "summer_soil_moisture_root",
    ]

    missing = [column for column in feature_columns if column not in yearly.columns]
    if missing:
        raise ValueError(f"year_types requires columns: {', '.join(missing)}")

    years = pd.Series(yearly.index, index=yearly.index)
    samples = yearly[feature_columns].copy()
    valid = samples.notna().all(axis=1)
    samples = samples.loc[valid]
    years = years.loc[valid]
    if len(samples) < 3:
        raise ValueError("year_types requires at least three complete years")

    scaled = StandardScaler().fit_transform(samples)
    model = KMeans(n_clusters=3, random_state=0, n_init=10)
    cluster_ids = model.fit_predict(scaled)

    # In standardized feature space, hot/dry is warm with low rain and
    # moisture; wet/cool is the opposite. The remaining cluster is normal.
    centroids = model.cluster_centers_
    hot_dry = int((centroids[:, 1] - centroids[:, 0] - centroids[:, 2]).argmax())
    remaining = [cluster for cluster in range(3) if cluster != hot_dry]
    wet_cool = max(
        remaining,
        key=lambda cluster: centroids[cluster, 0] + centroids[cluster, 2] - centroids[cluster, 1],
    )
    labels = {
        hot_dry: "hot_dry",
        wet_cool: "wet_cool",
        next(cluster for cluster in range(3) if cluster not in (hot_dry, wet_cool)): "normal",
    }

    return {
        int(year): labels[cluster]
        for year, cluster in zip(years.astype(int), cluster_ids)
    }