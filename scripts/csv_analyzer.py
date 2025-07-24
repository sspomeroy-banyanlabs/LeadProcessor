#!/usr/bin/env python3
"""
CSV Data Analyzer
Analyze your CSV files before processing to understand the data quality and structure
"""

import pandas as pd
import os
from pathlib import Path
import re
from collections import Counter
import sys

class CSVAnalyzer:
    def __init__(self):
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.phone_pattern = r'[\d\(\)\-\.\s\+]+'

    def analyze_csv(self, file_path: str) -> dict:
        """Analyze a single CSV file"""
        print(f"\n🔍 Analyzing: {Path(file_path).name}")
        print("=" * 50)
        
        try:
            # Try different encodings if UTF-8 fails
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"✅ Successfully read with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return {"error": "Failed to read CSV with any encoding"}
                
        except Exception as e:
            return {"error": f"Failed to read CSV: {str(e)}"}
        
        analysis = {
            "file_name": Path(file_path).name,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "data_quality": {},
            "sample_data": {},
            "recommendations": []
        }
        
        # Analyze key columns
        key_mappings = self.identify_key_columns(df.columns)
        analysis["column_mappings"] = key_mappings
        
        # Data quality analysis
        for column_type, column_name in key_mappings.items():
            if column_name:
                analysis["data_quality"][column_type] = self.analyze_column_quality(df, column_name, column_type)
                analysis["sample_data"][column_type] = self.get_sample_data(df, column_name)
        
        # Generate recommendations
        analysis["recommendations"] = self.generate_recommendations(analysis)
        
        return analysis

    def identify_key_columns(self, columns: list) -> dict:
        """Identify which columns map to our key data types"""
        mappings = {
            "name": None,
            "first_name": None,
            "last_name": None,
            "email": None,
            "phone": None,
            "company": None,
            "title": None,
            "revenue": None
        }
        
        for col in columns:
            col_lower = col.lower()
            
            # Name mappings
            if "contact full name" in col_lower or "full name" in col_lower:
                mappings["name"] = col
            elif "first name" in col_lower and not mappings["first_name"]:
                mappings["first_name"] = col
            elif "last name" in col_lower and not mappings["last_name"]:
                mappings["last_name"] = col
            
            # Email mappings
            elif ("email" in col_lower and ("1" in col or col_lower == "email")):
                mappings["email"] = col
            
            # Phone mappings
            elif "contact phone" in col_lower and "1" in col:
                mappings["phone"] = col
            elif col_lower == "phone number":
                mappings["phone"] = col
            
            # Company mappings
            elif "company name" in col_lower and "cleaned" in col_lower:
                mappings["company"] = col
            elif "associated company" in col_lower and "primary" in col_lower:
                mappings["company"] = col
            elif col_lower == "company":
                mappings["company"] = col
            
            # Title mappings
            elif col_lower == "title" or col_lower == "job title":
                mappings["title"] = col
            
            # Revenue mappings
            elif "annual revenue" in col_lower:
                mappings["revenue"] = col
        
        return mappings

    def analyze_column_quality(self, df: pd.DataFrame, column_name: str, column_type: str) -> dict:
        """Analyze data quality for a specific column"""
        if column_name not in df.columns:
            return {"error": "Column not found"}
        
        series = df[column_name]
        total_rows = len(series)
        
        quality = {
            "total_values": total_rows,
            "non_null_values": series.notna().sum(),
            "null_values": series.isna().sum(),
            "null_percentage": round((series.isna().sum() / total_rows) * 100, 2),
            "unique_values": series.nunique(),
            "duplicate_percentage": round(((total_rows - series.nunique()) / total_rows) * 100, 2) if total_rows > 0 else 0
        }
        
        # Type-specific quality checks
        if column_type == "email":
            if series.notna().sum() > 0:
                valid_emails = series[series.notna()].apply(lambda x: bool(re.match(self.email_pattern, str(x)))).sum()
                quality["valid_format"] = valid_emails
                quality["valid_format_percentage"] = round((valid_emails / series.notna().sum()) * 100, 2)
            else:
                quality["valid_format"] = 0
                quality["valid_format_percentage"] = 0
        
        elif column_type == "phone":
            if series.notna().sum() > 0:
                # Count entries that look like phone numbers (at least 7 digits)
                phone_like = series[series.notna()].apply(lambda x: len(re.findall(r'\d', str(x))) >= 7).sum()
                quality["phone_like_format"] = phone_like
                quality["phone_like_percentage"] = round((phone_like / series.notna().sum()) * 100, 2)
            else:
                quality["phone_like_format"] = 0
                quality["phone_like_percentage"] = 0
        
        elif column_type in ["name", "company", "title"]:
            if series.notna().sum() > 0:
                # Count non-empty strings
                non_empty = series[series.notna()].apply(lambda x: len(str(x).strip()) > 0).sum()
                quality["non_empty"] = non_empty
                quality["non_empty_percentage"] = round((non_empty / series.notna().sum()) * 100, 2)
            else:
                quality["non_empty"] = 0
                quality["non_empty_percentage"] = 0
        
        return quality

    def get_sample_data(self, df: pd.DataFrame, column_name: str, sample_size: int = 5) -> list:
        """Get sample data from a column"""
        if column_name not in df.columns:
            return []
        
        # Get non-null samples
        non_null_data = df[column_name][df[column_name].notna()]
        if len(non_null_data) == 0:
            return []
        
        # Return up to sample_size unique values
        return non_null_data.drop_duplicates().head(sample_size).tolist()

    def generate_recommendations(self, analysis: dict) -> list:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        data_quality = analysis.get("data_quality", {})
        
        # Check for missing key data
        mappings = analysis["column_mappings"]
        if not mappings.get("name") and not (mappings.get("first_name") and mappings.get("last_name")):
            recommendations.append("⚠️  No name columns found - you'll need to manually map name fields")
        
        if not mappings.get("email"):
            recommendations.append("⚠️  No email column found - leads without emails are less valuable")
        
        if not mappings.get("company"):
            recommendations.append("⚠️  No company column found - consider adding company data")
        
        if not mappings.get("phone"):
            recommendations.append("⚠️  No phone column found - reduces lead contact options")
        
        # Check data quality
        for field, quality in data_quality.items():
            if quality.get("null_percentage", 0) > 75:
                recommendations.append(f"🔴 {field.title()} field is {quality['null_percentage']}% empty - major data quality issue")
            elif quality.get("null_percentage", 0) > 50:
                recommendations.append(f"🟡 {field.title()} field is {quality['null_percentage']}% empty - consider data enrichment")
        
        # Email quality
        email_quality = data_quality.get("email", {})
        if email_quality and email_quality.get("valid_format_percentage", 0) < 70:
            recommendations.append(f"📧 Only {email_quality.get('valid_format_percentage', 0)}% of emails are in valid format")
        
        # Phone quality
        phone_quality = data_quality.get("phone", {})
        if phone_quality and phone_quality.get("phone_like_percentage", 0) < 70:
            recommendations.append(f"📱 Only {phone_quality.get('phone_like_percentage', 0)}% of phone numbers look valid")
        
        # Duplicate check
        if analysis["total_rows"] > 100:
            name_quality = data_quality.get("name", {})
            if name_quality and name_quality.get("duplicate_percentage", 0) > 20:
                recommendations.append(f"👥 High duplicate rate ({name_quality['duplicate_percentage']}%) - deduplication recommended")
        
        # File size recommendations
        if analysis["total_rows"] > 10000:
            recommendations.append("📊 Large dataset - consider processing in batches")
        
        return recommendations

    def print_analysis(self, analysis: dict):
        """Print formatted analysis results"""
        if "error" in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        print(f"📊 Basic Stats:")
        print(f"   Rows: {analysis['total_rows']:,}")
        print(f"   Columns: {analysis['total_columns']}")
        
        print(f"\n🎯 Column Mappings:")
        for field_type, column_name in analysis["column_mappings"].items():
            if column_name:
                print(f"   ✅ {field_type.title()}: {column_name}")
            else:
                print(f"   ❌ {field_type.title()}: Not found")
        
        print(f"\n📈 Data Quality:")
        for field_type, quality in analysis["data_quality"].items():
            if quality.get("error"):
                print(f"   ❌ {field_type.title()}: {quality['error']}")
                continue
            
            print(f"   📋 {field_type.title()}:")
            print(f"      Non-null: {quality['non_null_values']:,} ({100-quality['null_percentage']:.1f}%)")
            print(f"      Unique: {quality['unique_values']:,}")
            
            if field_type == "email" and "valid_format_percentage" in quality:
                print(f"      Valid format: {quality['valid_format_percentage']:.1f}%")
            elif field_type == "phone" and "phone_like_percentage" in quality:
                print(f"      Phone-like: {quality['phone_like_percentage']:.1f}%")
            elif "non_empty_percentage" in quality:
                print(f"      Non-empty: {quality['non_empty_percentage']:.1f}%")
        
        print(f"\n📝 Sample Data:")
        for field_type, samples in analysis["sample_data"].items():
            if samples:
                sample_display = samples[:3]  # Show first 3 samples
                print(f"   {field_type.title()}: {sample_display}")
        
        if analysis["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"   {rec}")
        
        # Calculate completeness score
        score = self.calculate_completeness_score(analysis)
        print(f"\n⭐ Completeness Score: {score}/10")

    def calculate_completeness_score(self, analysis: dict) -> int:
        """Calculate a completeness score from 0-10"""
        score = 0
        mappings = analysis["column_mappings"]
        data_quality = analysis["data_quality"]
        
        # Points for having key fields
        if mappings.get("name") or (mappings.get("first_name") and mappings.get("last_name")):
            score += 2
        if mappings.get("email"):
            score += 2
        if mappings.get("company"):
            score += 1
        if mappings.get("phone"):
            score += 1
        
        # Points for data quality
        for field, quality in data_quality.items():
            null_pct = quality.get("null_percentage", 100)
            if null_pct < 25:  # Less than 25% null
                score += 1
        
        return min(score, 10)

    def analyze_directory(self, directory_path: str):
        """Analyze all CSV files in a directory"""
        print(f"🔍 Analyzing all CSV files in: {directory_path}")
        print("=" * 60)
        
        csv_files = list(Path(directory_path).glob("*.csv"))
        
        if not csv_files:
            print("❌ No CSV files found in directory")
            print("💡 Make sure you've copied your CSV files to this directory")
            return
        
        all_analyses = []
        
        for csv_file in csv_files:
            analysis = self.analyze_csv(str(csv_file))
            all_analyses.append(analysis)
            self.print_analysis(analysis)
        
        # Summary across all files
        self.print_summary(all_analyses)

    def print_summary(self, analyses: list):
        """Print summary across all analyzed files"""
        if not analyses:
            return
        
        print(f"\n📋 SUMMARY ACROSS ALL FILES")
        print("=" * 60)
        
        valid_analyses = [a for a in analyses if "error" not in a]
        total_leads = sum(a.get("total_rows", 0) for a in valid_analyses)
        
        print(f"📁 Files analyzed: {len(analyses)}")
        print(f"✅ Successfully parsed: {len(valid_analyses)}")
        print(f"👥 Total leads across all files: {total_leads:,}")
        
        if not valid_analyses:
            print("❌ No files were successfully analyzed")
            return
        
        # Calculate completeness scores and rank files
        file_scores = []
        for analysis in valid_analyses:
            score = self.calculate_completeness_score(analysis)
            file_scores.append((
                analysis["file_name"], 
                score, 
                analysis["total_rows"],
                len([r for r in analysis["recommendations"] if "🔴" in r])  # Critical issues
            ))
        
        # Sort by score, then by row count
        file_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        print(f"\n🏆 File Quality Ranking:")
        for i, (filename, score, rows, critical_issues) in enumerate(file_scores, 1):
            status = "🔥 Excellent" if score >= 8 else "✅ Good" if score >= 6 else "⚠️ Needs work" if score >= 4 else "🔴 Poor"
            critical_text = f" ({critical_issues} critical issues)" if critical_issues > 0 else ""
            print(f"   {i}. {filename}")
            print(f"      Score: {score}/10 {status} | {rows:,} leads{critical_text}")
        
        # Overall recommendations
        print(f"\n🎯 Overall Recommendations:")
        
        # Find most common issues
        all_recommendations = []
        for analysis in valid_analyses:
            all_recommendations.extend(analysis.get("recommendations", []))
        
        if all_recommendations:
            rec_counter = Counter(all_recommendations)
            top_issues = rec_counter.most_common(3)
            
            print("   Most common issues across files:")
            for issue, count in top_issues:
                print(f"     • {issue} (affects {count} files)")
        
        print(f"\n🚀 Ready to process? Your best files are at the top of the ranking!")
        print(f"   Next step: python clickup_setup.py")

def main():
    """Main function"""
    analyzer = CSVAnalyzer()
    
    # Check if we're analyzing a specific file or directory
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path) and path.endswith('.csv'):
            analysis = analyzer.analyze_csv(path)
            analyzer.print_analysis(analysis)
        elif os.path.isdir(path):
            analyzer.analyze_directory(path)
        else:
            print(f"❌ Invalid path: {path}")
            print("💡 Usage: python csv_analyzer.py [file.csv|directory]")
    else:
        # Analyze current directory
        print("🔍 No specific file provided, analyzing current directory...")
        analyzer.analyze_directory(".")

if __name__ == "__main__":
    main()
