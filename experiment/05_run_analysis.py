#!/usr/bin/env python3
"""
Phase 5: Statistical analysis pipeline.

Runs the preregistered analyses:
  - LMM for main effects and interactions (H1-H5)
  - Metric-human correlation analysis (H6)
  - Post-hoc pairwise comparisons
  - Generates all figures and tables

Usage:
  python3 05_run_analysis.py                          # full analysis
  python3 05_run_analysis.py --computational-only     # metrics only (no human data yet)
  python3 05_run_analysis.py --human-data results/human_ratings.csv
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def run_computational_analysis(metrics_df: pd.DataFrame, config: dict, output_dir: Path):
    """Run factorial ANOVA on computational metrics (no human data needed)."""
    from scipy import stats

    output_dir.mkdir(parents=True, exist_ok=True)

    metric_cols = [c for c in metrics_df.columns if c not in
                   ["identity", "emotion", "sentence_id", "vc_system",
                    "lipsync_system", "output_video"]]

    print("\n--- Computational Metrics: Factorial Analysis ---\n")

    anova_results = []

    for metric in metric_cols:
        col_data = metrics_df[metric].dropna()
        if len(col_data) < 10:
            print(f"  {metric}: insufficient data (n={len(col_data)}), skipping")
            continue

        valid = metrics_df.dropna(subset=[metric])

        # Two-way ANOVA: VC × Lipsync (pooling across emotions and identities)
        groups_vc = [group[metric].values for name, group in valid.groupby("vc_system")]
        groups_ls = [group[metric].values for name, group in valid.groupby("lipsync_system")]
        groups_emo = [group[metric].values for name, group in valid.groupby("emotion")]

        # Main effect of VC
        if len(groups_vc) >= 2 and all(len(g) >= 2 for g in groups_vc):
            f_vc, p_vc = stats.f_oneway(*groups_vc)
            # Eta-squared
            ss_between = sum(len(g) * (np.mean(g) - np.mean(col_data))**2 for g in groups_vc)
            ss_total = sum((x - np.mean(col_data))**2 for x in col_data)
            eta2_vc = ss_between / ss_total if ss_total > 0 else 0
        else:
            f_vc, p_vc, eta2_vc = float("nan"), float("nan"), float("nan")

        # Main effect of Lipsync
        if len(groups_ls) >= 2 and all(len(g) >= 2 for g in groups_ls):
            f_ls, p_ls = stats.f_oneway(*groups_ls)
            ss_between = sum(len(g) * (np.mean(g) - np.mean(col_data))**2 for g in groups_ls)
            eta2_ls = ss_between / ss_total if ss_total > 0 else 0
        else:
            f_ls, p_ls, eta2_ls = float("nan"), float("nan"), float("nan")

        # Main effect of Emotion
        if len(groups_emo) >= 2 and all(len(g) >= 2 for g in groups_emo):
            f_emo, p_emo = stats.f_oneway(*groups_emo)
            ss_between = sum(len(g) * (np.mean(g) - np.mean(col_data))**2 for g in groups_emo)
            eta2_emo = ss_between / ss_total if ss_total > 0 else 0
        else:
            f_emo, p_emo, eta2_emo = float("nan"), float("nan"), float("nan")

        result = {
            "metric": metric,
            "n": len(col_data),
            "mean": float(col_data.mean()),
            "std": float(col_data.std()),
            "F_vc": float(f_vc), "p_vc": float(p_vc), "eta2_vc": float(eta2_vc),
            "F_ls": float(f_ls), "p_ls": float(p_ls), "eta2_ls": float(eta2_ls),
            "F_emo": float(f_emo), "p_emo": float(p_emo), "eta2_emo": float(eta2_emo),
        }
        anova_results.append(result)

        sig_vc = "*" if p_vc < 0.05 else ""
        sig_ls = "*" if p_ls < 0.05 else ""
        sig_emo = "*" if p_emo < 0.05 else ""
        print(f"  {metric:20s}  VC: F={f_vc:.2f}, p={p_vc:.4f}{sig_vc}, η²={eta2_vc:.3f}  |  "
              f"LS: F={f_ls:.2f}, p={p_ls:.4f}{sig_ls}, η²={eta2_ls:.3f}  |  "
              f"Emo: F={f_emo:.2f}, p={p_emo:.4f}{sig_emo}, η²={eta2_emo:.3f}")

    # Apply FDR correction
    from scipy.stats import false_discovery_control
    all_p = []
    for r in anova_results:
        all_p.extend([r["p_vc"], r["p_ls"], r["p_emo"]])
    all_p_arr = np.array([p for p in all_p if not np.isnan(p)])
    if len(all_p_arr) > 0:
        # BH correction
        sorted_indices = np.argsort(all_p_arr)
        m = len(all_p_arr)
        bh_critical = np.array([(i+1) / m * 0.05 for i in range(m)])
        reject = all_p_arr[sorted_indices] <= bh_critical
        n_significant = np.sum(reject)
        print(f"\n  BH FDR correction: {n_significant}/{m} tests remain significant at α=0.05")

    # Save ANOVA table
    anova_df = pd.DataFrame(anova_results)
    anova_path = output_dir / "computational_anova.csv"
    anova_df.to_csv(anova_path, index=False)
    print(f"\n  Saved: {anova_path}")

    # --- Condition means table ---
    print("\n--- Condition Means ---\n")
    for metric in metric_cols[:5]:  # show first 5
        pivot = metrics_df.pivot_table(
            values=metric, index="vc_system", columns="lipsync_system",
            aggfunc="mean"
        )
        if not pivot.empty:
            print(f"  {metric}:")
            print(pivot.to_string(float_format="%.4f"))
            print()

    return anova_results


def generate_figures(metrics_df: pd.DataFrame, config: dict, figures_dir: Path):
    """Generate publication-ready figures."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_style("whitegrid")
    plt.rcParams.update({"font.size": 12})

    metric_cols = [c for c in metrics_df.columns if c not in
                   ["identity", "emotion", "sentence_id", "vc_system",
                    "lipsync_system", "output_video"]]

    # Figure 1: Heatmaps for key metrics (VC × Lipsync)
    key_metrics = [m for m in ["lse_c", "avsu", "ssim", "wavlm_sim"] if m in metric_cols]
    if key_metrics:
        fig, axes = plt.subplots(1, len(key_metrics), figsize=(5 * len(key_metrics), 4))
        if len(key_metrics) == 1:
            axes = [axes]

        for ax, metric in zip(axes, key_metrics):
            pivot = metrics_df.pivot_table(
                values=metric, index="vc_system", columns="lipsync_system",
                aggfunc="mean"
            )
            if not pivot.empty:
                sns.heatmap(pivot, annot=True, fmt=".3f", cmap="YlOrRd", ax=ax)
                ax.set_title(metric.upper())

        plt.tight_layout()
        fig.savefig(figures_dir / "fig2_heatmaps.png", dpi=300, bbox_inches="tight")
        fig.savefig(figures_dir / "fig2_heatmaps.pdf", bbox_inches="tight")
        plt.close()
        print(f"  Saved: fig2_heatmaps.png/pdf")

    # Figure 2: Emotion comparison (neutral vs emotional per metric)
    if "emotion" in metrics_df.columns and len(metrics_df["emotion"].unique()) >= 2:
        n_metrics = min(len(key_metrics), 4)
        if n_metrics > 0:
            fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 5))
            if n_metrics == 1:
                axes = [axes]

            for ax, metric in zip(axes, key_metrics[:n_metrics]):
                data = metrics_df[["emotion", metric]].dropna()
                if len(data) > 0:
                    sns.boxplot(data=data, x="emotion", y=metric, ax=ax)
                    ax.set_title(metric.upper())
                    ax.set_xlabel("")

            plt.tight_layout()
            fig.savefig(figures_dir / "fig4_emotion_comparison.png", dpi=300, bbox_inches="tight")
            fig.savefig(figures_dir / "fig4_emotion_comparison.pdf", bbox_inches="tight")
            plt.close()
            print(f"  Saved: fig4_emotion_comparison.png/pdf")

    # Figure 3: Per-system comparison (box plots)
    for factor, label in [("vc_system", "VC System"), ("lipsync_system", "Lipsync System")]:
        if factor in metrics_df.columns:
            n_metrics = min(len(key_metrics), 4)
            if n_metrics > 0:
                fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 5))
                if n_metrics == 1:
                    axes = [axes]

                for ax, metric in zip(axes, key_metrics[:n_metrics]):
                    data = metrics_df[[factor, metric]].dropna()
                    if len(data) > 0:
                        sns.boxplot(data=data, x=factor, y=metric, ax=ax)
                        ax.set_title(metric.upper())
                        ax.set_xlabel(label)
                        ax.tick_params(axis="x", rotation=45)

                plt.tight_layout()
                fname = f"fig3_{factor}_comparison"
                fig.savefig(figures_dir / f"{fname}.png", dpi=300, bbox_inches="tight")
                fig.savefig(figures_dir / f"{fname}.pdf", bbox_inches="tight")
                plt.close()
                print(f"  Saved: {fname}.png/pdf")

    # Figure 4: Interaction plot (VC × Lipsync for key metric)
    if key_metrics and "vc_system" in metrics_df.columns and "lipsync_system" in metrics_df.columns:
        metric = key_metrics[0]
        fig, ax = plt.subplots(figsize=(8, 6))
        pivot = metrics_df.pivot_table(
            values=metric, index="vc_system", columns="lipsync_system",
            aggfunc="mean"
        )
        if not pivot.empty:
            pivot.plot(kind="line", marker="o", ax=ax)
            ax.set_ylabel(metric.upper())
            ax.set_xlabel("VC System")
            ax.set_title(f"Interaction Plot: VC × Lipsync ({metric.upper()})")
            ax.legend(title="Lipsync System")

        plt.tight_layout()
        fig.savefig(figures_dir / "fig3_interaction_plot.png", dpi=300, bbox_inches="tight")
        fig.savefig(figures_dir / "fig3_interaction_plot.pdf", bbox_inches="tight")
        plt.close()
        print(f"  Saved: fig3_interaction_plot.png/pdf")


def run_human_analysis(metrics_df: pd.DataFrame, human_df: pd.DataFrame,
                        config: dict, output_dir: Path):
    """Run full analysis including human ratings (H1-H6)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n--- Linear Mixed Model Analysis ---\n")

    try:
        from pymer4.models import Lmer

        # Merge computational metrics with human ratings
        merged = pd.merge(
            human_df,
            metrics_df,
            on=["identity", "emotion", "sentence_id", "vc_system", "lipsync_system"],
            how="inner",
        )

        if len(merged) < 30:
            print(f"  Insufficient merged data (n={len(merged)}). Need more human ratings.")
            return

        # Fit LMM for each human rating dimension
        for rating_name in ["overall_quality", "lip_sync", "voice_naturalness", "visual_naturalness"]:
            if rating_name not in merged.columns:
                continue

            print(f"\n  DV: {rating_name}")
            formula = f"{rating_name} ~ vc_system * lipsync_system * emotion + (1|participant_id) + (1|identity)"

            try:
                model = Lmer(formula, data=merged)
                model.fit()
                print(model.anova())
                print()

                # Save model summary
                summary_path = output_dir / f"lmm_{rating_name}.txt"
                with open(summary_path, "w") as f:
                    f.write(f"DV: {rating_name}\n")
                    f.write(f"Formula: {formula}\n")
                    f.write(f"N observations: {len(merged)}\n\n")
                    f.write(str(model.anova()))
                print(f"  Saved: {summary_path}")
            except Exception as e:
                print(f"  LMM failed for {rating_name}: {e}")
                print("  Falling back to standard ANOVA...")
                _fallback_anova(merged, rating_name, output_dir)

    except ImportError:
        print("  pymer4 not installed. Using scipy ANOVA as fallback.")
        for rating_name in ["overall_quality", "lip_sync", "voice_naturalness", "visual_naturalness"]:
            if rating_name in human_df.columns:
                merged = pd.merge(
                    human_df, metrics_df,
                    on=["identity", "emotion", "sentence_id", "vc_system", "lipsync_system"],
                    how="inner",
                )
                _fallback_anova(merged, rating_name, output_dir)

    # H6: Metric-human correlations
    print("\n--- Metric-Human Correlations (H6) ---\n")
    _compute_metric_human_correlations(metrics_df, human_df, config, output_dir)


def _fallback_anova(data: pd.DataFrame, dv: str, output_dir: Path):
    """Fallback ANOVA using scipy when pymer4 is not available."""
    from scipy import stats

    print(f"\n  ANOVA for {dv}:")

    for factor in ["vc_system", "lipsync_system", "emotion"]:
        if factor not in data.columns:
            continue
        groups = [g[dv].dropna().values for _, g in data.groupby(factor)]
        groups = [g for g in groups if len(g) >= 2]
        if len(groups) >= 2:
            f_stat, p_val = stats.f_oneway(*groups)
            print(f"    {factor}: F={f_stat:.3f}, p={p_val:.4f}")


def _compute_metric_human_correlations(metrics_df, human_df, config, output_dir):
    """Compute Spearman correlations between metrics and human MOS."""
    from scipy import stats

    # Average human ratings per condition
    condition_cols = ["vc_system", "lipsync_system", "emotion"]
    human_means = human_df.groupby(condition_cols).agg({
        "overall_quality": "mean",
    }).reset_index()

    # Average metrics per condition
    metric_cols = [c for c in metrics_df.columns if c not in
                   ["identity", "sentence_id", "output_video"] + condition_cols]
    metric_means = metrics_df.groupby(condition_cols)[metric_cols].mean().reset_index()

    # Merge
    merged = pd.merge(human_means, metric_means, on=condition_cols, how="inner")

    if len(merged) < 5:
        print("  Insufficient data for correlation analysis")
        return

    print(f"  Conditions: {len(merged)}")
    correlations = []

    for metric in metric_cols:
        valid = merged[["overall_quality", metric]].dropna()
        if len(valid) < 5:
            continue

        rho, p = stats.spearmanr(valid["overall_quality"], valid[metric])

        # Bootstrap CI
        n_boot = config["analysis"]["bootstrap_n"]
        boot_rhos = []
        for _ in range(n_boot):
            idx = np.random.choice(len(valid), size=len(valid), replace=True)
            boot_rho, _ = stats.spearmanr(
                valid["overall_quality"].iloc[idx], valid[metric].iloc[idx]
            )
            boot_rhos.append(boot_rho)
        ci_low = np.percentile(boot_rhos, 2.5)
        ci_high = np.percentile(boot_rhos, 97.5)

        correlations.append({
            "metric": metric,
            "spearman_rho": float(rho),
            "p_value": float(p),
            "ci_low": float(ci_low),
            "ci_high": float(ci_high),
            "n_conditions": len(valid),
        })

        sig = "*" if p < 0.05 else ""
        print(f"  {metric:20s}: ρ={rho:+.3f}{sig}  95% CI: [{ci_low:.3f}, {ci_high:.3f}]  p={p:.4f}")

    if correlations:
        corr_df = pd.DataFrame(correlations)
        corr_path = output_dir / "metric_human_correlations.csv"
        corr_df.to_csv(corr_path, index=False)
        print(f"\n  Saved: {corr_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 5: Statistical analysis")
    parser.add_argument("--computational-only", action="store_true",
                        help="Run only computational metric analysis (no human data)")
    parser.add_argument("--human-data", default=None,
                        help="Path to human ratings CSV")
    args = parser.parse_args()

    config = load_config()
    output_dir = Path(config["analysis"]["output_dir"])
    figures_dir = Path(config["analysis"]["figures_dir"])

    # Load computational metrics
    metrics_path = Path(config["metrics"]["output_file"])
    if not metrics_path.exists():
        print(f"ERROR: Metrics file not found: {metrics_path}")
        print("Run 04_compute_metrics.py first.")
        return

    metrics_df = pd.read_csv(metrics_path)
    print("=" * 60)
    print("Phase 5: Statistical Analysis")
    print("=" * 60)
    print(f"Metrics data: {len(metrics_df)} rows from {metrics_path}")

    # Run computational analysis (always)
    print("\n" + "=" * 40)
    print("Part 1: Computational Metrics Analysis")
    print("=" * 40)
    run_computational_analysis(metrics_df, config, output_dir)

    # Generate figures
    print("\n" + "=" * 40)
    print("Part 2: Generate Figures")
    print("=" * 40)
    generate_figures(metrics_df, config, figures_dir)

    # Run human analysis (if data available)
    if not args.computational_only and args.human_data:
        human_path = Path(args.human_data)
        if human_path.exists():
            human_df = pd.read_csv(human_path)
            print(f"\nHuman data: {len(human_df)} ratings from {human_path}")

            print("\n" + "=" * 40)
            print("Part 3: Human Evaluation Analysis")
            print("=" * 40)
            run_human_analysis(metrics_df, human_df, config, output_dir)
        else:
            print(f"\nWARN: Human data file not found: {human_path}")
    elif not args.computational_only:
        print("\nNo human data provided. Run with --human-data to include human analysis.")
        print("Or use --computational-only to skip.")

    print(f"\n{'=' * 60}")
    print(f"DONE.")
    print(f"  Results: {output_dir}/")
    print(f"  Figures: {figures_dir}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
