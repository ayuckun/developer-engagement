# Project Summary
## **Benchmarking Software Maintainability in Enterprise-Driven Open Source Projects in Terms of Developer Engagement**

This document summarizes the work completed in the following files:

## 1. `data_mining.ipynb`
- Data collection and preprocessing from various sources.
- Cleaning, normalization, and transformation of raw datasets.

## 2. `dmm_evaluation.ipynb`
- Implementation and evaluation of Data Mining Models (DMM).

## 3. `engagement_score.ipynb`
- Definition and calculation of engagement metrics.
- Development of a composite engagement score based on user activity data.
- Visualization and interpretation of engagement patterns.

## 4. `results.ipynb`
- Exploratory data analysis to identify trends and outliers.
- Aggregation and presentation of final results.
- Comparative analysis of model performance and engagement scores.
- Conclusions and recommendations based on findings.

## 5. `graphs.ipynb`
- Creation of visual representation of the outcomes.

## Single File Engagement Score
The file singlefile_eng.py can be run with global parameters changed. Its job is to create a subdirectory and put per-repo data inside as csv. After every project data is gathered, it combines them and runs the engagement algorithm on the whole data. The output directory can also be changed from global variables. The outcome is a per-repo per-month engagement score (normalized per-project) in a single csv file.

---
This compilation provides an overview of the workflow, from data preparation to model evaluation and result interpretation. The process can be replicated using a similarly shaped url list. The sampling step can be done on a larger scale.