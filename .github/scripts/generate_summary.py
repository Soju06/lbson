#!/usr/bin/env python3
"""
GitHub Actions CI Summary Generator

This script generates a detailed test matrix summary for the CI workflow.
It fetches job results from GitHub API and creates a markdown table.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple

import requests


class CISummaryGenerator:
    def __init__(self) -> None:
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.repository = os.environ.get("GITHUB_REPOSITORY")
        self.run_id = os.environ.get("GITHUB_RUN_ID")
        self.step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

        # Test matrix configuration
        self.python_versions = ["3.9", "3.10", "3.11", "3.12", "3.13"]
        self.platforms = [
            ("ubuntu-24.04", "x64", "Ubuntu 24.04 (x64)"),
            ("ubuntu-24.04-arm", "arm64", "Ubuntu 24.04 ARM (arm64)"),
            ("windows-2025", "x64", "Windows 2025 (x64)"),
            ("windows-11-arm", "arm64", "Windows 11 ARM (arm64)"),
            ("macos-13", "x64", "macOS 13 (Intel x64)"),
            ("macos-13", "arm64", "macOS 13 (ARM64)"),
            ("macos-14", "x64", "macOS 14 (Intel x64)"),
            ("macos-14", "arm64", "macOS 14 (ARM64)"),
            ("macos-15", "x64", "macOS 15 (Intel x64)"),
            ("macos-15", "arm64", "macOS 15 (ARM64)"),
        ]

        # Unsupported combinations based on workflow matrix excludes
        self.unsupported_combinations = {
            # Windows ARM64 doesn't support Python 3.9 and 3.10
            ("windows-11-arm", "arm64", "3.9"),
            ("windows-11-arm", "arm64", "3.10"),
            # macOS 14 and 15 x64 don't support Python 3.9 and 3.10
            ("macos-14", "x64", "3.9"),
            ("macos-14", "x64", "3.10"),
            ("macos-15", "x64", "3.9"),
            ("macos-15", "x64", "3.10"),
        }

    def fetch_job_results(self) -> List[Dict]:
        """Fetch job results from GitHub API."""
        if not all([self.github_token, self.repository, self.run_id]):
            print("Warning: Missing GitHub environment variables, using mock data")
            return []

        url = f"https://api.github.com/repos/{self.repository}/actions/runs/{self.run_id}/jobs"
        headers = {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github.v3+json"}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json().get("jobs", [])
        except Exception as e:
            print(f"Error fetching job results: {e}")
            return []

    def parse_job_name(self, job_name: str) -> Optional[Tuple[str, str, str]]:
        """Parse job name to extract platform, arch, and Python version."""
        if not job_name.startswith("Test on "):
            return None

        # Example: "Test on ubuntu-24.04-x64 with Python 3.11"
        # Example: "Test on macos-15-arm64 with Python 3.12"
        parts = job_name.replace("Test on ", "").split(" with Python ")
        if len(parts) != 2:
            return None

        platform_arch = parts[0]
        python_version = parts[1]

        # Split platform and arch
        if platform_arch.endswith("-x64"):
            platform = platform_arch[:-4]
            arch = "x64"
        elif platform_arch.endswith("-arm64"):
            platform = platform_arch[:-6]
            arch = "arm64"
        elif platform_arch.endswith("-arm"):
            platform = platform_arch[:-4]
            arch = "arm64"
        else:
            # For platforms without explicit arch suffix
            platform = platform_arch
            arch = "x64"  # Default assumption

        return platform, arch, python_version

    def get_job_status(self, jobs: List[Dict], platform: str, arch: str, python_version: str) -> str:
        """Get the status of a specific job combination."""
        # Check if this combination is unsupported
        if (platform, arch, python_version) in self.unsupported_combinations:
            return "not_supported"

        for job in jobs:
            parsed = self.parse_job_name(job["name"])
            if not parsed:
                continue

            job_platform, job_arch, job_python = parsed
            if job_platform == platform and job_arch == arch and job_python == python_version:
                conclusion = job.get("conclusion", "in_progress")
                return conclusion or "in_progress"

        return "not_found"

    def status_to_emoji(self, status: str) -> str:
        """Convert job status to emoji."""
        status_map = {
            "success": "✅",
            "failure": "❌",
            "cancelled": "⏸️",
            "skipped": "⏭️",
            "in_progress": "⏳",
            "not_supported": "⚫",
            "not_found": "❓",
        }
        return status_map.get(status, "❓")

    def generate_matrix_table(self, jobs: List[Dict]) -> str:
        """Generate the test matrix table."""
        lines = []

        # Table header
        header = "| Python Version |"
        separator = "|----------------|"

        for _, _, display_name in self.platforms:
            header += f" {display_name} |"
            separator += "-----------------|"

        lines.append(header)
        lines.append(separator)

        # Table rows
        for python_version in self.python_versions:
            row = f"| Python {python_version} |"

            for platform, arch, _ in self.platforms:
                status = self.get_job_status(jobs, platform, arch, python_version)
                emoji = self.status_to_emoji(status)
                row += f" {emoji} |"

            lines.append(row)

        return "\n".join(lines)

    def get_overall_status(self, jobs: List[Dict]) -> Tuple[str, str]:
        """Determine overall status and message."""
        if not jobs:
            return "unknown", "⏳ **Unable to fetch job results. Check the 'Jobs' tab for details.**"

        statuses = set()
        for job in jobs:
            if job["name"].startswith("Test on "):
                conclusion = job.get("conclusion", "in_progress")
                statuses.add(conclusion or "in_progress")

        if "in_progress" in statuses or None in statuses:
            return "in_progress", "⏳ **Tests are still running.**"
        elif "failure" in statuses:
            return "failure", "❌ **Some tests failed across the matrix.**"
        elif "cancelled" in statuses:
            return "cancelled", "⏸️ **Tests were cancelled.**"
        elif all(s == "success" for s in statuses):
            return "success", "✅ **All tests completed successfully across all platforms!**"
        else:
            return "mixed", "❓ **Mixed results. Check individual jobs for details.**"

    def generate_legend(self) -> str:
        """Generate the legend section."""
        lines = []
        lines.append("### 📖 Legend:")
        lines.append("- ✅ **Success**: Test passed")
        lines.append("- ❌ **Failed**: Test failed")
        lines.append("- ⚫ **Not Supported**: Platform doesn't support this Python version")
        lines.append("- ⏸️ **Cancelled**: Test was cancelled")
        lines.append("- ⏭️ **Skipped**: Test was skipped")
        lines.append("- ⏳ **In Progress**: Test is still running")
        lines.append("- ❓ **Unknown**: Unable to determine status")
        lines.append("")
        lines.append(
            "💡 **Tip**: Click on individual job names in the 'Jobs' tab above to see detailed results for each platform and Python version combination."
        )

        return "\n".join(lines)

    def generate_summary(self) -> str:
        """Generate the complete summary."""
        jobs = self.fetch_job_results()

        lines = []
        lines.append("## 📊 Test Results Summary")
        lines.append("")

        # Matrix table
        lines.append(self.generate_matrix_table(jobs))
        lines.append("")

        # Overall status
        status, message = self.get_overall_status(jobs)
        lines.append("### 🏁 Overall Status:")
        lines.append(f"- **Test Results**: {status}")
        lines.append("")
        lines.append(message)

        if status == "failure":
            lines.append("")
            lines.append("🔍 **To identify which specific combinations failed:**")
            lines.append("   1. Click on the 'Jobs' tab above")
            lines.append("   2. Look for jobs with ❌ (failed) status")
            lines.append("   3. Click on failed jobs to see detailed error logs")

        lines.append("")
        lines.append(self.generate_legend())

        return "\n".join(lines)

    def write_summary(self) -> bool:
        """Write summary to GitHub Step Summary file."""
        summary = self.generate_summary()

        if self.step_summary_path:
            try:
                with open(self.step_summary_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                print("✅ Summary written to GitHub Step Summary")
                return True
            except Exception as e:
                print(f"❌ Error writing to step summary: {e}")
                print("Summary content:")
                print(summary)
                return False
        else:
            print("📝 Summary content (GITHUB_STEP_SUMMARY not set):")
            print(summary)
            return True


def main():
    """Main entry point."""
    generator = CISummaryGenerator()
    success = generator.write_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
