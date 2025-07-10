from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import os
import glob
import pandas as pd
from pydriller import Repository
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA

TIME_LIMIT_MONTHS = 30
URLPATH = "active_projects.csv"
REPO_DATA_EXPORT_PATH = "data_active"
COMMIT_EXPORT_PATH = "commit_data.csv"
ENG_EXPORT_PATH = "engagement_data.csv"

os.makedirs(REPO_DATA_EXPORT_PATH, exist_ok=True)

def sanitize_name(url: str) -> str:
    parts = url.rstrip("/").split("/")[-2:]
    return "-".join(parts).replace(".git", "")

def collect_commits_with_dmm(repo_url: str, since: datetime, ) -> pd.DataFrame:
    records = []
    repo = Repository(path_to_repo=repo_url, since=since)
    for commit in repo.traverse_commits():
        author = commit.author.email or commit.author.name or "<unknown>"
        records.append({
            'url'                 : repo_url,
            'developer'           : author,
            'commit_hash'         : commit.hash,
            'commit_date'         : commit.committer_date,
            'churn'               : commit.lines,
            'dmm_unit_size'       : commit.dmm_unit_size,       # comment out these three columns for pure engagement data
            'dmm_unit_complexity' : commit.dmm_unit_complexity, # comment out these three columns for pure engagement data
            'dmm_unit_interfacing': commit.dmm_unit_interfacing # comment out these three columns for pure engagement data
        })
    df = pd.DataFrame(records)
    if not df.empty:
        df['commit_date'] = (
            pd.to_datetime(df['commit_date'], utc=True)
              .dt.tz_localize(None)
        )
    return df

sample_set = pd.read_csv(URLPATH, usecols=['url'])
repo_urls = sample_set['url'].dropna().unique().tolist()
cutoff_date = datetime.now(timezone.utc) - relativedelta(months=TIME_LIMIT_MONTHS)

for url in repo_urls:
    name = sanitize_name(url)
    out_path = os.path.join(REPO_DATA_EXPORT_PATH, f"{name}.csv")
    # if already mined, skip
    if os.path.exists(out_path):
        continue

    df = collect_commits_with_dmm(url, cutoff_date)
    n = len(df)
    if n:
        df.to_csv(out_path, index=False)

files = glob.glob(os.path.join(REPO_DATA_EXPORT_PATH, "*.csv"))

if not files:
    print("No per-repo data found—nothing to combine.")
else:
    combined = pd.concat((pd.read_csv(f, parse_dates=['commit_date']) for f in files),
                         ignore_index=True)
    combined.to_csv(COMMIT_EXPORT_PATH, index=False)
    print(f"\nSaved {len(combined)} total commits from {len(files)} repos.")

df = pd.read_csv(COMMIT_EXPORT_PATH, parse_dates=['commit_date'])
df = df.sort_values(['url','developer','commit_date'])

df['time_since_last_h'] = (
    df.groupby(['url','developer'])['commit_date']
      .diff().dt.total_seconds() / 3600
).fillna(0)

df['month'] = df['commit_date'].dt.to_period('M').dt.to_timestamp()

agg = (
    df.groupby(['url','month'])
      .agg(
          churn_sum       = ('churn',       'sum'),
          commit_count    = ('commit_date', 'count'),
          dev_count       = ('developer',   'nunique'),
          sum_interval_h  = ('time_since_last_h', 'sum')
      )
      .reset_index()
)

agg['churn_per_dev']  = agg['churn_sum'] / agg['dev_count']
agg['commit_rate']    = agg['commit_count'] / (agg['sum_interval_h'] + 1e-6)

features = ['churn_sum','commit_count','dev_count','churn_per_dev','commit_rate']
rscaler = RobustScaler()
X_robust = rscaler.fit_transform(agg[features])
agg[features] = X_robust

mm = MinMaxScaler()
agg = agg.groupby('url', group_keys=False).apply(lambda g: g.assign(**{
    feat: mm.fit_transform(g[[feat]]).flatten()
    for feat in features
}))

pca = PCA(n_components=1)
agg['eng_raw'] = pca.fit_transform(agg[features])

print("PCA feature weights (component 1):")
for feat, weight in zip(features, pca.components_[0]):
    print(f"  {feat:15s}: {weight: .4f}")

agg['engagement_score'] = agg.groupby('url')['eng_raw'] \
                             .transform(lambda x: (x - x.min())/(x.max()-x.min()))

agg.to_csv(ENG_EXPORT_PATH, index=False)
