# ONTO-Bench Annual Report Automation Pipeline

## Purpose

Automated generation of the "State of Epistemic Calibration" annual report. Sustained visibility + authoritative reference + citation magnet.

---

## Report Structure

```
State of Epistemic Calibration 2026
├── Executive Summary
├── 1. Introduction
├── 2. Methodology
│   ├── 2.1 Dataset Updates
│   ├── 2.2 Metric Definitions
│   └── 2.3 Evaluation Protocol
├── 3. Results
│   ├── 3.1 Overall Rankings
│   ├── 3.2 Unknown Detection
│   ├── 3.3 Calibration Analysis
│   ├── 3.4 Year-over-Year Trends
│   └── 3.5 Per-Domain Breakdown
├── 4. Analysis
│   ├── 4.1 Why Models Fail
│   ├── 4.2 What Works
│   └── 4.3 Open Challenges
├── 5. Recommendations
├── 6. Consortium Updates
├── Appendix A: Full Results Tables
├── Appendix B: Methodology Details
└── Appendix C: Model Specifications
```

---

## Automation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                 ANNUAL REPORT PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │  Data       │ ──▶ │  Analysis   │ ──▶ │  Report     │   │
│  │  Collection │     │  Engine     │     │  Generator  │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │ Leaderboard │     │ Statistical │     │   LaTeX     │   │
│  │   Results   │     │  Analysis   │     │    PDF      │   │
│  │  Model APIs │     │   Trends    │     │   HTML      │   │
│  │  Submissions│     │  Comparisons│     │   Data      │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Pipeline Components

### 1. Data Collection Module

```python
#!/usr/bin/env python3
"""
Annual Report Data Collector
Aggregates all leaderboard submissions for the reporting period
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import requests

class DataCollector:
    def __init__(self, year: int):
        self.year = year
        self.start_date = datetime(year, 1, 1)
        self.end_date = datetime(year, 12, 31)
        self.data_dir = Path(f"annual_reports/{year}/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_leaderboard(self) -> List[Dict]:
        """Fetch all submissions from leaderboard API"""
        submissions = []
        
        # From database/API
        response = requests.get(
            "https://onto-bench.org/api/submissions",
            params={
                "after": self.start_date.isoformat(),
                "before": self.end_date.isoformat(),
            }
        )
        
        if response.ok:
            submissions = response.json()
        
        # Save raw data
        with open(self.data_dir / "submissions.json", 'w') as f:
            json.dump(submissions, f, indent=2)
        
        return submissions
    
    def collect_model_metadata(self, submissions: List[Dict]) -> Dict:
        """Collect metadata about evaluated models"""
        models = {}
        
        for sub in submissions:
            model_id = sub["model"]
            if model_id not in models:
                models[model_id] = {
                    "name": sub["model"],
                    "organization": sub.get("organization"),
                    "first_submission": sub["submitted_at"],
                    "best_u_f1": sub["u_f1"],
                    "submissions_count": 1,
                }
            else:
                models[model_id]["submissions_count"] += 1
                if sub["u_f1"] > models[model_id]["best_u_f1"]:
                    models[model_id]["best_u_f1"] = sub["u_f1"]
        
        with open(self.data_dir / "models.json", 'w') as f:
            json.dump(models, f, indent=2)
        
        return models
    
    def collect_historical(self) -> Dict:
        """Load historical data for trend analysis"""
        historical = {}
        
        for prev_year in range(2026, self.year):
            path = Path(f"annual_reports/{prev_year}/data/summary.json")
            if path.exists():
                with open(path) as f:
                    historical[prev_year] = json.load(f)
        
        return historical
    
    def run(self) -> Dict:
        """Execute full data collection"""
        print(f"Collecting data for {self.year}...")
        
        submissions = self.collect_leaderboard()
        models = self.collect_model_metadata(submissions)
        historical = self.collect_historical()
        
        summary = {
            "year": self.year,
            "total_submissions": len(submissions),
            "unique_models": len(models),
            "collection_date": datetime.now().isoformat(),
        }
        
        with open(self.data_dir / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year
    collector = DataCollector(year)
    summary = collector.run()
    print(json.dumps(summary, indent=2))
```

### 2. Analysis Engine

```python
#!/usr/bin/env python3
"""
Annual Report Analysis Engine
Statistical analysis, trends, and insights
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from scipy import stats
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    metric: str
    mean: float
    std: float
    median: float
    best: float
    worst: float
    trend: str  # "improving" | "stable" | "declining"
    trend_pvalue: float


class AnalysisEngine:
    def __init__(self, year: int):
        self.year = year
        self.data_dir = Path(f"annual_reports/{year}/data")
        self.output_dir = Path(f"annual_reports/{year}/analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        with open(self.data_dir / "submissions.json") as f:
            self.submissions = json.load(f)
    
    def compute_statistics(self) -> Dict[str, AnalysisResult]:
        """Compute descriptive statistics for all metrics"""
        metrics = ["u_f1", "u_recall", "u_precision", "ece", "accuracy"]
        results = {}
        
        for metric in metrics:
            values = [s[metric] for s in self.submissions if metric in s]
            
            if not values:
                continue
            
            results[metric] = AnalysisResult(
                metric=metric,
                mean=float(np.mean(values)),
                std=float(np.std(values)),
                median=float(np.median(values)),
                best=float(max(values) if metric != "ece" else min(values)),
                worst=float(min(values) if metric != "ece" else max(values)),
                trend="stable",
                trend_pvalue=1.0,
            )
        
        return results
    
    def compute_rankings(self) -> List[Dict]:
        """Generate final rankings"""
        # Get best submission per model
        best_by_model = {}
        
        for sub in self.submissions:
            model = sub["model"]
            if model not in best_by_model or sub["u_f1"] > best_by_model[model]["u_f1"]:
                best_by_model[model] = sub
        
        # Sort by U-F1
        rankings = sorted(
            best_by_model.values(),
            key=lambda x: x["u_f1"],
            reverse=True
        )
        
        # Add ranks
        for i, entry in enumerate(rankings):
            entry["rank"] = i + 1
        
        return rankings
    
    def compute_trends(self, historical: Dict) -> Dict:
        """Analyze year-over-year trends"""
        if not historical:
            return {"status": "insufficient_data"}
        
        years = sorted(historical.keys())
        
        trends = {}
        
        for metric in ["mean_u_f1", "mean_ece"]:
            values = [historical[y].get(metric, 0) for y in years]
            
            if len(values) >= 2:
                # Linear regression for trend
                slope, intercept, r, p, se = stats.linregress(
                    range(len(values)), values
                )
                
                if p < 0.05:
                    trend = "improving" if slope > 0 else "declining"
                else:
                    trend = "stable"
                
                trends[metric] = {
                    "slope": slope,
                    "p_value": p,
                    "trend": trend,
                    "values": dict(zip(years, values)),
                }
        
        return trends
    
    def compute_category_breakdown(self) -> Dict:
        """Performance breakdown by question category"""
        # This would require per-question predictions
        # Placeholder for full implementation
        return {
            "KNOWN": {"mean_accuracy": 0.0},
            "UNKNOWN": {"mean_u_recall": 0.0},
            "CONTRADICTION": {"mean_c_f1": 0.0},
        }
    
    def generate_insights(self, stats: Dict, rankings: List) -> List[str]:
        """Generate natural language insights"""
        insights = []
        
        # Best performer
        if rankings:
            best = rankings[0]
            insights.append(
                f"**Top performer**: {best['model']} ({best['organization']}) "
                f"achieved U-F1 of {best['u_f1']:.2f}"
            )
        
        # Unknown detection gap
        if "u_recall" in stats:
            mean_recall = stats["u_recall"].mean
            if mean_recall < 0.5:
                insights.append(
                    f"**Epistemic gap persists**: Average unknown recall "
                    f"remains low at {mean_recall:.1%}"
                )
        
        # Calibration status
        if "ece" in stats:
            mean_ece = stats["ece"].mean
            if mean_ece > 0.2:
                insights.append(
                    f"**Calibration challenge**: Average ECE of {mean_ece:.2f} "
                    f"indicates significant miscalibration"
                )
        
        return insights
    
    def run(self) -> Dict:
        """Execute full analysis"""
        print(f"Analyzing data for {self.year}...")
        
        stats = self.compute_statistics()
        rankings = self.compute_rankings()
        insights = self.generate_insights(stats, rankings)
        
        # Load historical for trends
        historical = {}
        for prev_year in range(2026, self.year):
            path = Path(f"annual_reports/{prev_year}/analysis/summary.json")
            if path.exists():
                with open(path) as f:
                    historical[prev_year] = json.load(f)
        
        trends = self.compute_trends(historical)
        
        # Save results
        results = {
            "year": self.year,
            "statistics": {k: vars(v) for k, v in stats.items()},
            "rankings": rankings[:20],  # Top 20
            "trends": trends,
            "insights": insights,
        }
        
        with open(self.output_dir / "summary.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save full rankings
        with open(self.output_dir / "full_rankings.json", 'w') as f:
            json.dump(rankings, f, indent=2)
        
        return results


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    engine = AnalysisEngine(year)
    results = engine.run()
    print(json.dumps(results["insights"], indent=2))
```

### 3. Report Generator

```python
#!/usr/bin/env python3
"""
Annual Report Generator
Produces LaTeX, PDF, and HTML outputs
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    def __init__(self, year: int):
        self.year = year
        self.analysis_dir = Path(f"annual_reports/{year}/analysis")
        self.output_dir = Path(f"annual_reports/{year}/output")
        self.template_dir = Path("annual_reports/templates")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load analysis
        with open(self.analysis_dir / "summary.json") as f:
            self.analysis = json.load(f)
        
        # Setup Jinja
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
    
    def generate_latex(self) -> str:
        """Generate LaTeX report"""
        template = self.env.get_template("annual_report.tex.j2")
        
        content = template.render(
            year=self.year,
            generation_date=datetime.now().strftime("%B %d, %Y"),
            statistics=self.analysis["statistics"],
            rankings=self.analysis["rankings"],
            trends=self.analysis.get("trends", {}),
            insights=self.analysis["insights"],
        )
        
        output_path = self.output_dir / f"onto_bench_report_{self.year}.tex"
        with open(output_path, 'w') as f:
            f.write(content)
        
        return str(output_path)
    
    def generate_pdf(self, tex_path: str) -> str:
        """Compile LaTeX to PDF"""
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path],
                cwd=self.output_dir,
                check=True,
                capture_output=True,
            )
            # Run twice for references
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path],
                cwd=self.output_dir,
                check=True,
                capture_output=True,
            )
            return tex_path.replace(".tex", ".pdf")
        except subprocess.CalledProcessError as e:
            print(f"PDF generation failed: {e}")
            return None
    
    def generate_html(self) -> str:
        """Generate HTML report for web"""
        template = self.env.get_template("annual_report.html.j2")
        
        content = template.render(
            year=self.year,
            generation_date=datetime.now().strftime("%B %d, %Y"),
            statistics=self.analysis["statistics"],
            rankings=self.analysis["rankings"],
            trends=self.analysis.get("trends", {}),
            insights=self.analysis["insights"],
        )
        
        output_path = self.output_dir / f"report_{self.year}.html"
        with open(output_path, 'w') as f:
            f.write(content)
        
        return str(output_path)
    
    def generate_json(self) -> str:
        """Generate machine-readable JSON"""
        output = {
            "report_version": "1.0",
            "year": self.year,
            "generated_at": datetime.now().isoformat(),
            "data": self.analysis,
        }
        
        output_path = self.output_dir / f"report_{self.year}.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return str(output_path)
    
    def run(self) -> Dict[str, str]:
        """Generate all report formats"""
        print(f"Generating reports for {self.year}...")
        
        outputs = {}
        
        # LaTeX
        tex_path = self.generate_latex()
        outputs["latex"] = tex_path
        print(f"  ✓ LaTeX: {tex_path}")
        
        # PDF
        pdf_path = self.generate_pdf(tex_path)
        if pdf_path:
            outputs["pdf"] = pdf_path
            print(f"  ✓ PDF: {pdf_path}")
        
        # HTML
        html_path = self.generate_html()
        outputs["html"] = html_path
        print(f"  ✓ HTML: {html_path}")
        
        # JSON
        json_path = self.generate_json()
        outputs["json"] = json_path
        print(f"  ✓ JSON: {json_path}")
        
        return outputs


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    generator = ReportGenerator(year)
    outputs = generator.run()
    print(f"\nGenerated: {list(outputs.keys())}")
```

### 4. LaTeX Template

```latex
% annual_reports/templates/annual_report.tex.j2
\documentclass[11pt]{article}

\usepackage[utf8]{inputenc}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage[margin=1in]{geometry}

\title{State of Epistemic Calibration {{ year }}}
\author{ONTO-Bench Consortium}
\date{Generated: {{ generation_date }}}

\begin{document}

\maketitle

\begin{abstract}
This report presents the {{ year }} evaluation of epistemic calibration 
across {{ rankings|length }} AI models submitted to ONTO-Bench. 
{% for insight in insights[:2] %}
{{ insight | replace("**", "") }}
{% endfor %}
\end{abstract}

\section{Executive Summary}

\begin{itemize}
{% for insight in insights %}
\item {{ insight | replace("**", "\\textbf{") | replace("**", "}") }}
{% endfor %}
\end{itemize}

\section{Rankings}

\begin{table}[h]
\centering
\begin{tabular}{@{}rlcccc@{}}
\toprule
Rank & Model & Organization & U-F1 & U-Recall & ECE \\
\midrule
{% for entry in rankings[:10] %}
{{ entry.rank }} & {{ entry.model }} & {{ entry.organization }} & {{ "%.2f"|format(entry.u_f1) }} & {{ "%.2f"|format(entry.u_recall) }} & {{ "%.2f"|format(entry.ece) }} \\
{% endfor %}
\bottomrule
\end{tabular}
\caption{Top 10 models by U-F1 score.}
\end{table}

\section{Statistical Summary}

{% if statistics.u_f1 %}
\textbf{Unknown Detection (U-F1)}:
Mean: {{ "%.3f"|format(statistics.u_f1.mean) }},
Std: {{ "%.3f"|format(statistics.u_f1.std) }},
Best: {{ "%.3f"|format(statistics.u_f1.best) }}
{% endif %}

{% if statistics.ece %}
\textbf{Calibration (ECE)}:
Mean: {{ "%.3f"|format(statistics.ece.mean) }},
Std: {{ "%.3f"|format(statistics.ece.std) }},
Best: {{ "%.3f"|format(statistics.ece.best) }}
{% endif %}

\section{Methodology}

Evaluation conducted on ONTO-Bench v1.8 (SHA256: \texttt{cb6978...}).
All submissions evaluated on identical test set of 55 samples.
Metrics computed using official evaluation scripts.

\section{Citation}

\begin{verbatim}
@techreport{ontobench{{ year }},
  title={State of Epistemic Calibration {{ year }}},
  author={ONTO-Bench Consortium},
  year={{ year }},
  url={https://onto-bench.org/reports/{{ year }}}
}
\end{verbatim}

\end{document}
```

---

## Automation Schedule

### Cron Configuration

```bash
# /etc/cron.d/onto-bench-reports

# Daily: Update leaderboard snapshot
0 2 * * * onto /opt/onto-bench/scripts/snapshot_leaderboard.sh

# Monthly: Generate monthly digest
0 3 1 * * onto /opt/onto-bench/scripts/monthly_digest.sh

# Annual: Full report generation (January 15)
0 4 15 1 * onto /opt/onto-bench/scripts/annual_report.sh
```

### Annual Report Script

```bash
#!/bin/bash
# annual_report.sh

YEAR=$(($(date +%Y) - 1))  # Previous year
REPORT_DIR="/opt/onto-bench/annual_reports"

echo "Generating annual report for $YEAR"

# 1. Collect data
python3 $REPORT_DIR/scripts/collect_data.py $YEAR

# 2. Run analysis
python3 $REPORT_DIR/scripts/analyze.py $YEAR

# 3. Generate reports
python3 $REPORT_DIR/scripts/generate_report.py $YEAR

# 4. Publish
cp $REPORT_DIR/$YEAR/output/* /var/www/onto-bench/reports/$YEAR/

# 5. Notify
python3 $REPORT_DIR/scripts/notify_consortium.py $YEAR

echo "Annual report complete"
```

---

## Distribution Channels

### Automatic Distribution

1. **Website**: onto-bench.org/reports/2026
2. **Email**: Consortium members + mailing list
3. **arXiv**: Technical report submission
4. **Twitter**: Thread with key findings
5. **Press release**: For major milestones

### Embargo Policy

- Consortium members: 48 hours early access
- Public release: January 20 annually
- No leaks of rankings before release

---

## Quality Assurance

### Pre-Release Checklist

- [ ] Data validation complete
- [ ] Statistical analysis reviewed
- [ ] Rankings verified
- [ ] PDF renders correctly
- [ ] HTML responsive
- [ ] Citations accurate
- [ ] Consortium approval (if required)

### Post-Release Monitoring

- Track downloads
- Monitor citations
- Collect feedback
- Note corrections needed

---

*Annual Report Pipeline v1.0*
