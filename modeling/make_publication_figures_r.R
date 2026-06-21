#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(scales)
  library(grid)
  library(ggrepel)
  library(ragg)
})

`%||%` <- function(x, y) if (is.null(x)) y else x

script_path <- tryCatch(normalizePath(sys.frame(1)$ofile, winslash = "/", mustWork = FALSE), error = function(e) NA_character_)
root <- if (!is.na(script_path)) normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = FALSE) else normalizePath(getwd(), winslash = "/", mustWork = TRUE)
if (!dir.exists(file.path(root, "results"))) {
  root <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)
}

out_dir <- file.path(root, "results", "figures_r_publication")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

theme_pub <- function(base_size = 8) {
  theme_classic(base_size = base_size, base_family = "Arial") +
    theme(
      text = element_text(colour = "#111827"),
      plot.title = element_text(face = "bold", size = base_size + 0.8, hjust = 0),
      plot.subtitle = element_text(size = base_size - 0.5, colour = "#4b5563"),
      axis.title = element_text(size = base_size),
      axis.text = element_text(size = base_size - 1, colour = "#111827"),
      axis.line = element_line(linewidth = 0.35, colour = "#111827"),
      axis.ticks = element_line(linewidth = 0.30, colour = "#111827"),
      legend.position = "right",
      legend.title = element_blank(),
      legend.text = element_text(size = base_size - 1.2),
      panel.grid.major = element_line(linewidth = 0.25, colour = "#e5e7eb"),
      panel.grid.minor = element_blank(),
      plot.margin = margin(6, 8, 6, 6)
    )
}

pal <- c(
  "MIMIC-IV" = "#2f6f9f",
  "MIMIC-III" = "#b64b4b",
  "SICdb" = "#6f7f3f",
  "eICU" = "#8b6bb1",
  "Full-feature XGBoost" = "#9ca3af",
  "Cross-database XGBoost" = "#2f6f9f"
)

feature_labels <- c(
  "current_kdigo" = "Current KDIGO stage",
  "creatinine_recent" = "Most recent creatinine",
  "urine_output_total" = "Urine output, 24 h",
  "temp_mean" = "Mean temperature",
  "current_or_prior_max_kdigo" = "Current/prior max KDIGO",
  "sbp_mean" = "Mean systolic BP",
  "creatinine_max" = "Maximum creatinine",
  "lactate_max" = "Maximum lactate",
  "spo2_min" = "Minimum SpO2",
  "chloride_min" = "Minimum chloride",
  "urine_output_count" = "Urine-output measurements",
  "gender_F" = "Female sex",
  "platelet_min" = "Minimum platelet count",
  "heart_rate_mean" = "Mean heart rate",
  "sodium_min" = "Minimum sodium"
)

save_pub <- function(plot, filename, width_mm = 180, height_mm = 120, dpi = 600) {
  w <- width_mm / 25.4
  h <- height_mm / 25.4
  png_file <- file.path(out_dir, paste0(filename, ".png"))
  tiff_file <- file.path(out_dir, paste0(filename, ".tiff"))
  pdf_file <- file.path(out_dir, paste0(filename, ".pdf"))
  svg_file <- file.path(out_dir, paste0(filename, ".svg"))
  grDevices::svg(svg_file, width = w, height = h, family = "Arial", bg = "white")
  print(plot)
  dev.off()
  ragg::agg_png(png_file, width = w, height = h, units = "in", res = dpi, background = "white")
  print(plot)
  dev.off()
  ragg::agg_tiff(tiff_file, width = w, height = h, units = "in", res = dpi, background = "white", compression = "lzw")
  print(plot)
  dev.off()
  grDevices::cairo_pdf(pdf_file, width = w, height = h, family = "Arial", onefile = FALSE)
  print(plot)
  dev.off()
}

read_csv_base <- function(path) {
  read.csv(file.path(root, path), check.names = FALSE, stringsAsFactors = FALSE)
}

fmt_n <- function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE)

add_panel_label <- function(label) {
  annotate("text", x = -Inf, y = Inf, label = label, hjust = -0.35, vjust = 1.35,
           fontface = "bold", size = 4.0, colour = "#111827")
}

make_flow <- function() {
  flow <- read_csv_base("results/cohort_flow/cohort_flow_source_table.csv")
  land <- read_csv_base("results/cohort_flow/cohort_landmark_event_table.csv")
  flow <- flow %>%
    mutate(
      cohort = factor(cohort, levels = c("MIMIC-IV", "MIMIC-III", "SICdb")),
      step_order = as.integer(step_order),
      y = max(step_order) - step_order + 1,
      label = paste0(step, "\nRows: ", fmt_n(rows), "\nICU stays: ", fmt_n(icu_stays)),
      role_short = case_when(
        cohort == "MIMIC-IV" ~ "Development/internal validation",
        cohort == "MIMIC-III" ~ "Primary temporal/external validation",
        TRUE ~ "Exploratory sensitivity validation"
      )
    )
  land_note <- land %>%
    group_by(cohort) %>%
    summarise(
      y = -0.25,
      label = paste0(
        "Landmarks: ",
        paste0(landmark_hour, "h n=", fmt_n(rows), " (", event_rate, ")", collapse = "\n"),
        "\nEvents: ", fmt_n(sum(events))
      ),
      .groups = "drop"
    ) %>%
    mutate(cohort = factor(cohort, levels = levels(flow$cohort)))

  arrows <- flow %>%
    group_by(cohort) %>%
    arrange(step_order) %>%
    mutate(yend = lead(y)) %>%
    filter(!is.na(yend)) %>%
    ungroup()

  ggplot(flow, aes(x = cohort, y = y)) +
    geom_segment(data = arrows, aes(xend = cohort, y = y - 0.42, yend = yend + 0.42),
                 arrow = arrow(length = unit(2.8, "mm")), linewidth = 0.45, colour = "#6b7280") +
    geom_label(aes(label = label, colour = cohort), fill = "white", linewidth = 0.38,
               label.r = unit(0.08, "lines"), size = 2.05, fontface = "bold",
               lineheight = 0.92, label.padding = unit(0.23, "lines")) +
    geom_label(data = land_note, aes(label = label, colour = cohort), fill = "#f9fafb",
               linewidth = 0.35, size = 2.05, lineheight = 0.95,
               label.padding = unit(0.25, "lines")) +
    geom_text(data = distinct(flow, cohort, role_short), aes(x = cohort, y = 6.75, label = as.character(cohort)),
              fontface = "bold", size = 3.0, colour = "#111827") +
    geom_text(data = distinct(flow, cohort, role_short), aes(x = cohort, y = 6.48, label = role_short),
              size = 2.1, colour = "#6b7280") +
    scale_colour_manual(values = pal, guide = "none") +
    coord_cartesian(ylim = c(-0.8, 6.9), clip = "off") +
    labs(
      title = "A  Cohort construction and validation roles",
      subtitle = "SICdb and eICU were used as exploratory transportability analyses, not co-primary validation cohorts"
    ) +
    theme_void(base_family = "Arial") +
    theme(
      plot.title = element_text(face = "bold", size = 9.5, colour = "#111827"),
      plot.subtitle = element_text(size = 7, colour = "#4b5563"),
      plot.margin = margin(10, 12, 10, 12)
    )
}

make_forest <- function() {
  perf <- read_csv_base("results/performance_summary/performance_summary_with_ci.csv")
  df <- perf %>%
    filter(landmark == "overall") %>%
    filter(
      (cohort == "MIMIC-IV internal test" & model == "xgboost_crossdb") |
        (cohort == "MIMIC-III external with CRRT" & model == "xgboost_crossdb") |
        (cohort == "SICdb sensitivity external" & model == "xgboost_crossdb")
    ) %>%
    mutate(
      cohort_short = factor(
        case_when(
          grepl("MIMIC-IV", cohort) ~ "MIMIC-IV",
          grepl("MIMIC-III", cohort) ~ "MIMIC-III",
          TRUE ~ "SICdb"
        ),
        levels = c("SICdb", "MIMIC-III", "MIMIC-IV")
      ),
      label = sprintf("AUROC %.3f (%.3f-%.3f)\nAUPRC %.3f; Brier %.3f",
                      auroc, auroc_ci_low, auroc_ci_high, auprc, brier)
    )
  ggplot(df, aes(x = auroc, y = cohort_short, colour = cohort_short)) +
    geom_vline(xintercept = 0.5, colour = "#d1d5db", linetype = "dashed", linewidth = 0.35) +
    geom_errorbar(aes(xmin = auroc_ci_low, xmax = auroc_ci_high), orientation = "y", width = 0.14, linewidth = 0.65) +
    geom_point(size = 2.4) +
    geom_text(aes(label = label), x = 0.86, hjust = 0, size = 2.05, colour = "#111827", lineheight = 0.95) +
    scale_colour_manual(values = pal, guide = "none") +
    scale_x_continuous(limits = c(0.45, 1.02), breaks = seq(0.5, 0.9, 0.1)) +
    labs(title = "B  Discrimination of the locked cross-database model",
         x = "AUROC (95% CI)", y = NULL) +
    theme_pub(7.2) +
    theme(panel.grid.major.y = element_blank())
}

make_calibration <- function() {
  m4 <- read_csv_base("results/mimic_iv_crossdb_features/calibration_bins_xgboost.csv") %>% mutate(cohort = "MIMIC-IV")
  m3 <- read_csv_base("results/mimiciii_external_validation_xgboost_crossdb_with_crrt/calibration_bins_mimiciii_crossdb_with_crrt.csv") %>% mutate(cohort = "MIMIC-III")
  sic <- read_csv_base("results/sicdb_external_validation_xgboost_crossdb/calibration_bins_sicdb.csv") %>% mutate(cohort = "SICdb")
  df <- bind_rows(m4, m3, sic) %>% mutate(cohort = factor(cohort, levels = c("MIMIC-IV", "MIMIC-III", "SICdb")))
  ggplot(df, aes(predicted_mean, observed_rate, colour = cohort)) +
    geom_abline(intercept = 0, slope = 1, linetype = "dashed", colour = "#6b7280", linewidth = 0.5) +
    geom_line(linewidth = 0.65) +
    geom_point(size = 1.8) +
    scale_colour_manual(values = pal) +
    scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25), labels = label_number(accuracy = 0.01, trim = TRUE)) +
    scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25), labels = label_number(accuracy = 0.01, trim = TRUE)) +
    coord_equal() +
    labs(title = "C  Calibration across validation settings",
         subtitle = "Dashed line indicates perfect calibration",
         x = "Mean predicted risk", y = "Observed event rate") +
    theme_pub(7.2)
}

make_dca <- function() {
  m4 <- read_csv_base("results/mimic_iv_crossdb_features/decision_curve_xgboost.csv") %>% mutate(cohort = "MIMIC-IV")
  m3 <- read_csv_base("results/mimiciii_external_validation_xgboost_crossdb_with_crrt/decision_curve_mimiciii_crossdb_with_crrt.csv") %>% mutate(cohort = "MIMIC-III")
  df <- bind_rows(m4, m3) %>% filter(threshold <= 0.80)
  all_line <- m3 %>% filter(threshold <= 0.80) %>% transmute(threshold, strategy = "Treat all", net_benefit = pmax(net_benefit_all, -0.05))
  none_line <- m3 %>% filter(threshold <= 0.80) %>% transmute(threshold, strategy = "Treat none", net_benefit = net_benefit_none)
  model_line <- df %>% transmute(threshold, strategy = cohort, net_benefit = net_benefit_model)
  ggplot() +
    geom_line(data = model_line, aes(threshold, net_benefit, colour = strategy), linewidth = 0.70) +
    geom_line(data = all_line, aes(threshold, net_benefit), colour = "#6b7280", linetype = "longdash", linewidth = 0.65) +
    geom_line(data = none_line, aes(threshold, net_benefit), colour = "#111827", linetype = "dotted", linewidth = 0.65) +
    annotate("text", x = 0.69, y = 0.34, label = "Treat all", size = 2.25, colour = "#6b7280") +
    annotate("text", x = 0.62, y = 0.024, label = "Treat none", size = 2.15, colour = "#111827") +
    annotate("text", x = 0.745, y = 0.070, label = "MIMIC-IV", size = 2.15, colour = pal[["MIMIC-IV"]], hjust = 0) +
    annotate("text", x = 0.715, y = -0.004, label = "MIMIC-III", size = 2.15, colour = pal[["MIMIC-III"]], hjust = 0) +
    scale_colour_manual(values = pal[c("MIMIC-IV", "MIMIC-III")], name = NULL) +
    scale_x_continuous(breaks = seq(0.1, 0.8, 0.1)) +
    scale_y_continuous(breaks = seq(0, 0.4, 0.1)) +
    coord_cartesian(xlim = c(0.01, 0.80), ylim = c(-0.075, 0.475), clip = "off") +
    labs(title = "D  Decision-curve analysis",
         subtitle = "Net benefit shown for thresholds from 0.01 to 0.80; treat-all values below -0.05 are truncated",
         x = "Risk threshold", y = "Net benefit") +
    theme_pub(7.2) +
    theme(legend.position = "none",
          plot.margin = margin(6, 10, 7, 7))
}

make_importance <- function() {
  imp <- read_csv_base("results/xgboost_crossdb_explanations/xgboost_contribution_importance.csv") %>%
    arrange(desc(mean_abs_contribution)) %>%
    slice_head(n = 12) %>%
    mutate(
      feature_label = ifelse(clean_feature %in% names(feature_labels), feature_labels[clean_feature], clean_feature),
      feature_label = factor(feature_label, levels = rev(feature_label)),
      share = absolute_contribution_share
    )
  ggplot(imp, aes(share, feature_label)) +
    geom_segment(aes(x = 0, xend = share, yend = feature_label), linewidth = 0.48, colour = "#9ca3af") +
    geom_point(aes(size = mean_abs_contribution), colour = "#2f6f9f", alpha = 0.92) +
    geom_label(aes(x = share + 0.012, label = percent(share, accuracy = 0.1)),
               hjust = 0, size = 1.95, colour = "#374151",
               linewidth = 0, label.padding = unit(0.06, "lines"),
               fill = alpha("white", 0.86)) +
    scale_x_continuous(labels = percent_format(accuracy = 1),
                       limits = c(0, 0.43),
                       breaks = seq(0, 0.4, 0.1),
                       expand = expansion(mult = c(0, 0.02))) +
    scale_size_continuous(range = c(1.35, 3.25), guide = "none") +
    labs(title = "E  Global model-contribution importance",
         subtitle = "Mean absolute additive contribution in the MIMIC-IV internal test set",
         x = "Share of total absolute contribution", y = NULL) +
    theme_pub(7.2) +
    theme(panel.grid.major.y = element_blank(),
          axis.text.y = element_text(size = 6.4))
}

make_dependence <- function() {
  dep <- read_csv_base("results/xgboost_crossdb_explanations/xgboost_binned_dependence.csv") %>%
    filter(feature %in% c("creatinine_recent", "urine_output_total", "sbp_mean", "lactate_max")) %>%
    mutate(feature = factor(feature, levels = c("creatinine_recent", "urine_output_total", "sbp_mean", "lactate_max")))
  ggplot(dep, aes(raw_median, mean_contribution)) +
    geom_hline(yintercept = 0, colour = "#d1d5db", linewidth = 0.35) +
    geom_line(colour = "#2f6f9f", linewidth = 0.58) +
    geom_point(colour = "#2f6f9f", size = 1.35) +
    facet_wrap(~ feature, scales = "free_x", ncol = 2,
               labeller = labeller(feature = as_labeller(c(
                 "creatinine_recent" = "Most recent creatinine",
                 "urine_output_total" = "Urine output, 24 h",
                 "sbp_mean" = "Mean systolic BP",
                 "lactate_max" = "Maximum lactate"
               )))) +
    labs(title = "F  Binned feature-contribution relationships",
         subtitle = "Positive values increase predicted log-odds; associations are not causal effects",
         x = "Feature value, decile median", y = "Mean contribution to log-odds") +
    theme_pub(6.8) +
    theme(strip.background = element_blank(),
          strip.text = element_text(face = "bold", size = 7.2),
          legend.position = "none")
}

plots <- list(
  fig1_cohort_flow = list(plot = make_flow(), width = 183, height = 125),
  fig2_performance_forest = list(plot = make_forest(), width = 170, height = 78),
  fig3_calibration = list(plot = make_calibration(), width = 135, height = 105),
  fig4_decision_curve = list(plot = make_dca(), width = 145, height = 98),
  fig5_xgboost_importance = list(plot = make_importance(), width = 135, height = 105),
  fig6_xgboost_dependence = list(plot = make_dependence(), width = 160, height = 118)
)

for (nm in names(plots)) {
  save_pub(plots[[nm]]$plot, nm, plots[[nm]]$width, plots[[nm]]$height)
}

manifest <- data.frame(
  figure = names(plots),
  svg = paste0(names(plots), ".svg"),
  png = paste0(names(plots), ".png"),
  tiff = paste0(names(plots), ".tiff"),
  pdf = paste0(names(plots), ".pdf"),
  stringsAsFactors = FALSE
)
write.csv(manifest, file.path(out_dir, "figure_manifest.csv"), row.names = FALSE)
cat("Saved R publication figures to:", out_dir, "\n")
