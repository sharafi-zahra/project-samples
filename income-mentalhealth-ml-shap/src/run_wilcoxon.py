# -*- coding: utf-8 -*-
"""
Generate pairwise Wilcoxon signed-rank test tables (LaTeX) from bootstrap
checkpoint CSVs.

Produces:
  results/{label}/wilcoxon_auc.tex   — Table for main text (full sample)
  results/{label}/wilcoxon_sex.tex   — Table for sex-stratified (Table 3 companion)
"""
import os
import numpy as np
import pandas as pd
from itertools import combinations
from scipy.stats import wilcoxon

MODELS = ["Regression", "DecisionTree", "RandomForest", "XGBoost"]
MODEL_LABELS = {
    "Regression":   "Logistic Regression",
    "DecisionTree": "Decision Tree",
    "RandomForest": "Random Forest",
    "XGBoost":      "XGBoost",
}
N_COMPARISONS = 12   # C(4,2)=6 pairs × 2 tasks
ALPHA_CORRECTED = 0.05 / N_COMPARISONS   # 0.0042

def load_aucs(csv_path):
    df = pd.read_csv(csv_path)
    return {m: df[df['model'] == m].sort_values('iter')['auc'].values
            for m in MODELS}

def sig_label(p):
    if p < ALPHA_CORRECTED:
        return "$^{***}$"
    elif p < 0.05:
        return "$^{**}$"
    elif p < 0.10:
        return "$^{*}$"
    else:
        return "\\textsuperscript{ns}"

def run_pairwise(aucs):
    """Return list of (labelA, labelB, meanA, meanB, W, p, sig) sorted by meanA desc."""
    pairs = []
    for mA, mB in combinations(MODELS, 2):
        a = aucs[mA]; b = aucs[mB]
        # Put higher-mean model first
        if np.mean(a) < np.mean(b):
            a, b, mA, mB = b, a, mB, mA
        stat, p = wilcoxon(a, b, alternative='two-sided')
        pairs.append((MODEL_LABELS[mA], MODEL_LABELS[mB],
                      np.mean(a), np.mean(b), stat, p, sig_label(p)))
    return sorted(pairs, key=lambda x: -x[2])

def latex_wilcoxon_main(income_aucs, mental_aucs, label):
    rows = []
    for task, aucs in [("\\textit{Mental Health}", mental_aucs),
                        ("\\textit{Income}",        income_aucs)]:
        pairs = run_pairwise(aucs)
        n = len(pairs)
        for i, (lA, lB, mA, mB, W, p, sig) in enumerate(pairs):
            tl = f"\\multirow{{{n}}}{{*}}{{{task}}}" if i == 0 else ""
            p_str = f"$<$0.0001" if p < 0.0001 else f"{p:.4f}"
            rows.append(
                f"  {tl} & {lA} vs.\\ {lB} & {mA:.3f} & {mB:.3f} "
                f"& {W:.1f} & {p_str} & {sig} \\\\"
            )
        rows.append("\\midrule")
    rows.pop()
    body = "\n".join(rows)
    return (
        "\\begin{table}[ht]\n"
        "\\centering\n"
        f"\\label{{tab:wilcoxon_auc}}\n"
        "\\renewcommand{\\arraystretch}{1.25}\n"
        "\\caption{Pairwise Wilcoxon Signed-Rank Test Results for Classifier "
        "Comparison by Task (AUC).}\n"
        "\\begin{tabular}{llccccl}\n"
        "\\toprule\n"
        "\\textbf{Target} & \\textbf{Comparison} & "
        "\\textbf{AUC\\textsubscript{A}} & \\textbf{AUC\\textsubscript{B}} & "
        "\\textbf{W} & \\textbf{\\textit{p}-value} & \\textbf{Sig.} \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\vspace{0.5em}\n"
        "\\parbox{0.9\\linewidth}{\\scriptsize\\textbf{Notes:} "
        "\\emph{Mean AUC values are reported per classifier. "
        f"Bonferroni-corrected significance threshold: "
        f"$\\alpha = {ALPHA_CORRECTED:.4f}$ ({N_COMPARISONS} comparisons). "
        "Significance levels: $^{***}p < \\alpha_{Bonf}$, "
        "$^{**}p < 0.05$, $^{*}p < 0.1$, "
        "\\textsuperscript{ns}$p \\geq 0.1$. "
        "All tests are two-sided. "
        "Classifier listed first (A) has higher mean AUC where significant.}}\n"
        "\\end{table}"
    )

def latex_wilcoxon_sex(f_inc, m_inc, f_mnt, m_mnt):
    rows = []
    for task, (aucs_f, aucs_m) in [
            ("\\textit{Mental Health}", (f_mnt, m_mnt)),
            ("\\textit{Income}",        (f_inc, m_inc))]:
        for sg, aucs in [("Female", aucs_f), ("Male", aucs_m)]:
            pairs = run_pairwise(aucs)
            n = len(pairs)
            for i, (lA, lB, mA, mB, W, p, sig) in enumerate(pairs):
                tl = (f"\\multirow{{{2*n}}}{{*}}{{{task}}}"
                      if sg == "Female" and i == 0 else "")
                sl = f"\\multirow{{{n}}}{{*}}{{{sg}}}" if i == 0 else ""
                p_str = "$<$0.0001" if p < 0.0001 else f"{p:.4f}"
                rows.append(
                    f"  {tl} & {sl} & {lA} vs.\\ {lB} & {mA:.3f} & {mB:.3f} "
                    f"& {W:.1f} & {p_str} & {sig} \\\\"
                )
        rows.append("\\midrule")
    rows.pop()
    body = "\n".join(rows)
    return (
        "\\begin{table}[ht]\n"
        "\\centering\n"
        f"\\label{{tab:wilcoxon_sex}}\n"
        "\\renewcommand{\\arraystretch}{1.25}\n"
        "\\caption{Pairwise Wilcoxon Signed-Rank Test Results by Sex Subgroup (AUC).}\n"
        "\\begin{tabular}{lllccccl}\n"
        "\\toprule\n"
        "\\textbf{Target} & \\textbf{Subgroup} & \\textbf{Comparison} & "
        "\\textbf{AUC\\textsubscript{A}} & \\textbf{AUC\\textsubscript{B}} & "
        "\\textbf{W} & \\textbf{\\textit{p}-value} & \\textbf{Sig.} \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )

def run_for_label(label):
    ckdir = os.path.join('results', label, 'checkpoints')
    outdir = os.path.join('results', label)

    inc  = load_aucs(os.path.join(ckdir, 'ck_income.csv'))
    mnt  = load_aucs(os.path.join(ckdir, 'ck_mental.csv'))
    f_inc = load_aucs(os.path.join(ckdir, 'ck_f_inc.csv'))
    m_inc = load_aucs(os.path.join(ckdir, 'ck_m_inc.csv'))
    f_mnt = load_aucs(os.path.join(ckdir, 'ck_f_mnt.csv'))
    m_mnt = load_aucs(os.path.join(ckdir, 'ck_m_mnt.csv'))

    t_main = latex_wilcoxon_main(inc, mnt, label)
    with open(os.path.join(outdir, 'wilcoxon_auc.tex'), 'w') as f:
        f.write(t_main)
    print(f"  wilcoxon_auc.tex saved.")

    t_sex = latex_wilcoxon_sex(f_inc, m_inc, f_mnt, m_mnt)
    with open(os.path.join(outdir, 'wilcoxon_sex.tex'), 'w') as f:
        f.write(t_sex)
    print(f"  wilcoxon_sex.tex saved.")

    # Console summary
    print(f"\n  --- {label} Wilcoxon summary (full sample) ---")
    for task, aucs in [("Income", inc), ("Mental", mnt)]:
        print(f"  {task}:")
        for lA, lB, mA, mB, W, p, sig in run_pairwise(aucs):
            print(f"    {lA:22s} vs {lB:22s}  p={p:.4f}  {sig}")

os.chdir(r'C:\Users\sharafi')

print("=== Median v2 ===")
run_for_label('median_v2')
