from typing import Dict, Any, Optional, List
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..base_tool import BaseTool, ToolCapability, ToolResult, ToolResultStatus

logger = logging.getLogger(__name__)

class DataAnalysisTool(BaseTool):
    """
    Data processing and analysis tool for user data.
    Transforms raw data into insights and actionable information.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    @property
    def capabilities(self) -> ToolCapability:
        return ToolCapability(
            name="data_analysis",
            description="Process and analyze user data to generate insights",
            parameters={
                "data": {
                    "type": "object",
                    "description": "Raw data to analyze (typically from database tool)",
                    "required": True
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "enum": ["summary", "trends", "patterns", "comparison", "recommendations"],
                    "default": "summary"
                },
                "time_period": {
                    "type": "string",
                    "description": "Time period for analysis",
                    "enum": ["daily", "weekly", "monthly"],
                    "default": "weekly"
                },
                "include_predictions": {
                    "type": "boolean",
                    "description": "Whether to include predictive insights",
                    "default": False
                }
            },
            use_cases=[
                "data_processing", "insights", "trends", "patterns", 
                "analysis", "metrics", "statistics", "recommendations"
            ],
            data_sources=["processed_data"],
            prerequisites=["raw_data"],
            confidence_keywords=[
                "analyze", "process", "insights", "trends", "patterns",
                "statistics", "metrics", "summary", "analysis"
            ]
        )
    
    def initialize(self) -> bool:
        """Initialize the data analysis tool."""
        self._initialized = True
        logger.info("Data analysis tool initialized")
        return True
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute data analysis on the provided data."""
        try:
            # Extract parameters
            data = kwargs.get("data")
            analysis_type = kwargs.get("analysis_type", "summary")
            time_period = kwargs.get("time_period", "weekly")
            include_predictions = kwargs.get("include_predictions", False)
            
            if not data:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    error="Data parameter is required"
                )
            
            # Process the data based on analysis type
            if analysis_type == "summary":
                result_data = await self._generate_summary(data, time_period)
            elif analysis_type == "trends":
                result_data = await self._analyze_trends(data, time_period)
            elif analysis_type == "patterns":
                result_data = await self._identify_patterns(data, time_period)
            elif analysis_type == "comparison":
                result_data = await self._generate_comparison(data, time_period)
            elif analysis_type == "recommendations":
                result_data = await self._generate_recommendations(data, time_period)
            else:
                result_data = await self._generate_summary(data, time_period)
            
            # Add predictions if requested
            if include_predictions:
                predictions = await self._generate_predictions(data, time_period)
                result_data["predictions"] = predictions
            
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.SUCCESS,
                data=result_data,
                metadata={
                    "analysis_type": analysis_type,
                    "time_period": time_period,
                    "include_predictions": include_predictions,
                    "processed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing data analysis: {e}")
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    async def _generate_summary(self, data: Dict[str, Any], time_period: str) -> Dict[str, Any]:
        """Generate a summary of the user data."""
        try:
            # Extract results from database query
            results = data.get("results", [])
            if not results:
                return {
                    "summary_type": "empty",
                    "message": "No data available for analysis",
                    "metrics": {}
                }
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(results)
            
            summary = {
                "summary_type": time_period,
                "total_records": len(results),
                "date_range": self._get_date_range(df),
                "metrics": {}
            }
            
            # Activity analysis
            if "activity_type" in df.columns:
                activity_summary = self._analyze_activities(df)
                summary["metrics"]["activities"] = activity_summary
            
            # Duration analysis
            if "duration_minutes" in df.columns:
                duration_summary = self._analyze_duration(df)
                summary["metrics"]["duration"] = duration_summary
            
            # Frequency analysis
            frequency_summary = self._analyze_frequency(df)
            summary["metrics"]["frequency"] = frequency_summary
            
            # Key insights
            summary["key_insights"] = self._generate_key_insights(df, time_period)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    async def _analyze_trends(self, data: Dict[str, Any], time_period: str) -> Dict[str, Any]:
        """Analyze trends in the user data."""
        try:
            results = data.get("results", [])
            if not results:
                return {"trends": [], "message": "No data available for trend analysis"}
            
            df = pd.DataFrame(results)
            
            trends = {
                "trend_analysis": time_period,
                "trends": [],
                "summary": {}
            }
            
            # Activity trends
            if "activity_date" in df.columns and "activity_count" in df.columns:
                activity_trends = self._calculate_activity_trends(df)
                trends["trends"].append({
                    "metric": "activity_count",
                    "trend": activity_trends["trend"],
                    "change_percentage": activity_trends["change_percentage"],
                    "direction": activity_trends["direction"]
                })
            
            # Duration trends
            if "duration_minutes" in df.columns:
                duration_trends = self._calculate_duration_trends(df)
                trends["trends"].append({
                    "metric": "duration",
                    "trend": duration_trends["trend"],
                    "change_percentage": duration_trends["change_percentage"],
                    "direction": duration_trends["direction"]
                })
            
            # Generate trend summary
            trends["summary"] = self._summarize_trends(trends["trends"])
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise
    
    async def _identify_patterns(self, data: Dict[str, Any], time_period: str) -> Dict[str, Any]:
        """Identify patterns in user behavior."""
        try:
            results = data.get("results", [])
            if not results:
                return {"patterns": [], "message": "No data available for pattern analysis"}
            
            df = pd.DataFrame(results)
            
            patterns = {
                "pattern_analysis": time_period,
                "patterns": [],
                "insights": []
            }
            
            # Day of week patterns
            if "activity_date" in df.columns:
                day_patterns = self._analyze_day_patterns(df)
                patterns["patterns"].append({
                    "type": "day_of_week",
                    "description": "Activity patterns by day of week",
                    "data": day_patterns
                })
            
            # Activity type patterns
            if "activity_type" in df.columns:
                type_patterns = self._analyze_activity_type_patterns(df)
                patterns["patterns"].append({
                    "type": "activity_types",
                    "description": "Most common activity types",
                    "data": type_patterns
                })
            
            # Generate insights from patterns
            patterns["insights"] = self._generate_pattern_insights(patterns["patterns"])
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            raise
    
    async def _generate_comparison(self, data: Dict[str, Any], time_period: str) -> Dict[str, Any]:
        """Generate comparison with previous periods."""
        try:
            results = data.get("results", [])
            if not results:
                return {"comparison": {}, "message": "No data available for comparison"}
            
            df = pd.DataFrame(results)
            
            comparison = {
                "comparison_type": time_period,
                "current_period": {},
                "previous_period": {},
                "changes": {}
            }
            
            # Split data into current and previous periods
            if "activity_date" in df.columns:
                df["activity_date"] = pd.to_datetime(df["activity_date"])
                current_data, previous_data = self._split_time_periods(df, time_period)
                
                if not current_data.empty and not previous_data.empty:
                    # Compare metrics
                    comparison["current_period"] = self._calculate_period_metrics(current_data)
                    comparison["previous_period"] = self._calculate_period_metrics(previous_data)
                    comparison["changes"] = self._calculate_changes(
                        comparison["current_period"], 
                        comparison["previous_period"]
                    )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error generating comparison: {e}")
            raise
    
    async def _generate_recommendations(self, data: Dict[str, Any], time_period: str) -> Dict[str, Any]:
        """Generate recommendations based on data analysis."""
        try:
            results = data.get("results", [])
            if not results:
                return {"recommendations": [], "message": "No data available for recommendations"}
            
            df = pd.DataFrame(results)
            
            recommendations = {
                "recommendation_type": time_period,
                "recommendations": [],
                "priority": "medium"
            }
            
            # Analyze current performance
            if "activity_count" in df.columns:
                avg_activity = df["activity_count"].mean()
                if avg_activity < 5:  # Low activity threshold
                    recommendations["recommendations"].append({
                        "type": "activity_increase",
                        "title": "Increase Daily Activity",
                        "description": "Your activity levels are below average. Consider setting daily goals.",
                        "priority": "high",
                        "actionable_steps": [
                            "Set a daily activity target",
                            "Enable activity reminders",
                            "Track progress weekly"
                        ]
                    })
            
            # Duration recommendations
            if "duration_minutes" in df.columns:
                avg_duration = df["duration_minutes"].mean()
                if avg_duration < 30:  # Low duration threshold
                    recommendations["recommendations"].append({
                        "type": "duration_optimization",
                        "title": "Optimize Activity Duration",
                        "description": "Consider longer, more focused activity sessions.",
                        "priority": "medium",
                        "actionable_steps": [
                            "Plan longer activity blocks",
                            "Reduce interruptions",
                            "Track time more effectively"
                        ]
                    })
            
            # Set overall priority
            high_priority_count = sum(1 for rec in recommendations["recommendations"] if rec.get("priority") == "high")
            if high_priority_count > 0:
                recommendations["priority"] = "high"
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
    
    async def _generate_predictions(self, data: Dict[str, Any], time_period: str) -> Dict[str, Any]:
        """Generate predictive insights."""
        try:
            results = data.get("results", [])
            if len(results) < 3:  # Need minimum data for predictions
                return {"message": "Insufficient data for predictions"}
            
            df = pd.DataFrame(results)
            
            predictions = {
                "prediction_type": time_period,
                "forecasts": [],
                "confidence": "medium"
            }
            
            # Activity count prediction
            if "activity_count" in df.columns and "activity_date" in df.columns:
                activity_forecast = self._predict_activity(df)
                predictions["forecasts"].append({
                    "metric": "activity_count",
                    "forecast": activity_forecast,
                    "confidence": "medium"
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {"error": str(e)}
    
    # Helper methods for analysis
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, str]:
        """Get the date range from the data."""
        if "activity_date" in df.columns:
            dates = pd.to_datetime(df["activity_date"])
            return {
                "start_date": dates.min().strftime("%Y-%m-%d"),
                "end_date": dates.max().strftime("%Y-%m-%d"),
                "total_days": (dates.max() - dates.min()).days + 1
            }
        return {}
    
    def _analyze_activities(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze activity-related metrics."""
        activity_summary = {}
        
        if "activity_count" in df.columns:
            activity_summary["total_activities"] = int(df["activity_count"].sum())
            activity_summary["average_daily"] = round(df["activity_count"].mean(), 2)
            activity_summary["max_daily"] = int(df["activity_count"].max())
            activity_summary["min_daily"] = int(df["activity_count"].min())
        
        if "activity_type" in df.columns:
            type_counts = df["activity_type"].value_counts()
            activity_summary["most_common_type"] = type_counts.index[0] if not type_counts.empty else None
            activity_summary["activity_types"] = type_counts.to_dict()
        
        return activity_summary
    
    def _analyze_duration(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze duration-related metrics."""
        duration_summary = {}
        
        duration_col = df["duration_minutes"]
        duration_summary["total_minutes"] = int(duration_col.sum())
        duration_summary["average_duration"] = round(duration_col.mean(), 2)
        duration_summary["max_duration"] = int(duration_col.max())
        duration_summary["min_duration"] = int(duration_col.min())
        
        # Convert to hours for readability
        total_hours = duration_summary["total_minutes"] / 60
        duration_summary["total_hours"] = round(total_hours, 2)
        
        return duration_summary
    
    def _analyze_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze frequency patterns."""
        frequency_summary = {}
        
        if "activity_date" in df.columns:
            unique_dates = df["activity_date"].nunique()
            total_records = len(df)
            
            frequency_summary["unique_days"] = unique_dates
            frequency_summary["total_entries"] = total_records
            frequency_summary["average_entries_per_day"] = round(total_records / max(unique_dates, 1), 2)
        
        return frequency_summary
    
    def _generate_key_insights(self, df: pd.DataFrame, time_period: str) -> List[str]:
        """Generate key insights from the data."""
        insights = []
        
        # Activity insights
        if "activity_count" in df.columns:
            avg_activity = df["activity_count"].mean()
            if avg_activity > 10:
                insights.append("High activity levels maintained consistently")
            elif avg_activity < 3:
                insights.append("Activity levels are below recommended thresholds")
        
        # Duration insights
        if "duration_minutes" in df.columns:
            avg_duration = df["duration_minutes"].mean()
            if avg_duration > 60:
                insights.append("Good session durations indicate focused engagement")
            elif avg_duration < 15:
                insights.append("Short session durations suggest potential for improvement")
        
        # Consistency insights
        if "activity_date" in df.columns:
            date_range = self._get_date_range(df)
            if date_range.get("total_days", 0) > 7:
                insights.append(f"Data covers {date_range['total_days']} days showing good tracking consistency")
        
        return insights
    
    def _calculate_activity_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trends in activity data."""
        # Simple trend calculation using linear regression
        df_sorted = df.sort_values("activity_date")
        y = df_sorted["activity_count"].values
        x = range(len(y))
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            change_percentage = (slope / max(y.mean(), 1)) * 100
            
            return {
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "change_percentage": round(change_percentage, 2),
                "direction": "up" if slope > 0 else "down" if slope < 0 else "stable"
            }
        
        return {"trend": "insufficient_data", "change_percentage": 0, "direction": "stable"}
    
    def _calculate_duration_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trends in duration data."""
        df_sorted = df.sort_values("activity_date")
        y = df_sorted["duration_minutes"].values
        x = range(len(y))
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            change_percentage = (slope / max(y.mean(), 1)) * 100
            
            return {
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "change_percentage": round(change_percentage, 2),
                "direction": "up" if slope > 0 else "down" if slope < 0 else "stable"
            }
        
        return {"trend": "insufficient_data", "change_percentage": 0, "direction": "stable"}
    
    def _summarize_trends(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize all trends."""
        if not trends:
            return {"overall": "no_data"}
        
        positive_trends = sum(1 for trend in trends if trend.get("direction") == "up")
        negative_trends = sum(1 for trend in trends if trend.get("direction") == "down")
        
        if positive_trends > negative_trends:
            overall = "improving"
        elif negative_trends > positive_trends:
            overall = "declining"
        else:
            overall = "stable"
        
        return {
            "overall": overall,
            "positive_trends": positive_trends,
            "negative_trends": negative_trends,
            "stable_trends": len(trends) - positive_trends - negative_trends
        }
    
    def _analyze_day_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns by day of week."""
        df["day_of_week"] = pd.to_datetime(df["activity_date"]).dt.day_name()
        
        day_counts = df.groupby("day_of_week").size()
        most_active_day = day_counts.idxmax() if not day_counts.empty else None
        
        return {
            "most_active_day": most_active_day,
            "day_distribution": day_counts.to_dict(),
            "weekday_vs_weekend": self._compare_weekday_weekend(df)
        }
    
    def _compare_weekday_weekend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare weekday vs weekend activity."""
        df["is_weekend"] = pd.to_datetime(df["activity_date"]).dt.dayofweek >= 5
        
        weekend_avg = df[df["is_weekend"]]["activity_count"].mean() if "activity_count" in df.columns else 0
        weekday_avg = df[~df["is_weekend"]]["activity_count"].mean() if "activity_count" in df.columns else 0
        
        return {
            "weekend_average": round(weekend_avg, 2),
            "weekday_average": round(weekday_avg, 2),
            "preference": "weekend" if weekend_avg > weekday_avg else "weekday"
        }
    
    def _analyze_activity_type_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in activity types."""
        type_counts = df["activity_type"].value_counts()
        
        return {
            "most_common": type_counts.index[0] if not type_counts.empty else None,
            "type_distribution": type_counts.to_dict(),
            "diversity_score": len(type_counts) / max(len(df), 1)
        }
    
    def _generate_pattern_insights(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from identified patterns."""
        insights = []
        
        for pattern in patterns:
            if pattern["type"] == "day_of_week":
                most_active = pattern["data"].get("most_active_day")
                if most_active:
                    insights.append(f"Most active on {most_active}")
                
                preference = pattern["data"].get("weekday_vs_weekend", {}).get("preference")
                if preference:
                    insights.append(f"Prefers {preference} activities")
            
            elif pattern["type"] == "activity_types":
                most_common = pattern["data"].get("most_common")
                if most_common:
                    insights.append(f"Primary activity type: {most_common}")
                
                diversity = pattern["data"].get("diversity_score", 0)
                if diversity > 0.7:
                    insights.append("Good variety in activity types")
                elif diversity < 0.3:
                    insights.append("Limited variety in activity types")
        
        return insights
    
    def _split_time_periods(self, df: pd.DataFrame, time_period: str) -> tuple:
        """Split data into current and previous periods."""
        df_sorted = df.sort_values("activity_date")
        total_days = (df_sorted["activity_date"].max() - df_sorted["activity_date"].min()).days + 1
        
        if time_period == "weekly":
            split_days = 7
        elif time_period == "monthly":
            split_days = 30
        else:  # daily
            split_days = 1
        
        if total_days >= split_days * 2:
            mid_date = df_sorted["activity_date"].max() - timedelta(days=split_days)
            current = df_sorted[df_sorted["activity_date"] > mid_date]
            previous = df_sorted[df_sorted["activity_date"] <= mid_date].tail(len(current))
            return current, previous
        
        return df_sorted, pd.DataFrame()
    
    def _calculate_period_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate metrics for a period."""
        metrics = {}
        
        if "activity_count" in df.columns:
            metrics["total_activities"] = int(df["activity_count"].sum())
            metrics["average_activities"] = round(df["activity_count"].mean(), 2)
        
        if "duration_minutes" in df.columns:
            metrics["total_duration"] = int(df["duration_minutes"].sum())
            metrics["average_duration"] = round(df["duration_minutes"].mean(), 2)
        
        return metrics
    
    def _calculate_changes(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between periods."""
        changes = {}
        
        for metric in current:
            if metric in previous and previous[metric] != 0:
                change = ((current[metric] - previous[metric]) / previous[metric]) * 100
                changes[f"{metric}_change"] = round(change, 2)
                changes[f"{metric}_direction"] = "increase" if change > 0 else "decrease" if change < 0 else "stable"
        
        return changes
    
    def _predict_activity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Simple activity prediction based on trends."""
        df_sorted = df.sort_values("activity_date")
        recent_data = df_sorted.tail(7)  # Last 7 days
        
        if len(recent_data) >= 3:
            trend = recent_data["activity_count"].diff().mean()
            current_avg = recent_data["activity_count"].mean()
            predicted_next = max(0, current_avg + trend)
            
            return {
                "next_period_prediction": round(predicted_next, 2),
                "trend_direction": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
                "confidence_level": "medium"
            }
        
        return {"message": "Insufficient data for prediction"}
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate parameters before execution."""
        validated = {}
        
        # Validate data parameter
        data = kwargs.get("data")
        if not data:
            raise ValueError("Data parameter is required")
        
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        validated["data"] = data
        
        # Validate analysis_type
        analysis_type = kwargs.get("analysis_type", "summary")
        valid_types = ["summary", "trends", "patterns", "comparison", "recommendations"]
        if analysis_type not in valid_types:
            raise ValueError(f"Invalid analysis_type. Must be one of: {valid_types}")
        validated["analysis_type"] = analysis_type
        
        # Validate time_period
        time_period = kwargs.get("time_period", "weekly")
        valid_periods = ["daily", "weekly", "monthly"]
        if time_period not in valid_periods:
            raise ValueError(f"Invalid time_period. Must be one of: {valid_periods}")
        validated["time_period"] = time_period
        
        # Validate include_predictions
        validated["include_predictions"] = bool(kwargs.get("include_predictions", False))
        
        return validated
    
    def should_use(self, intent: str, context: Dict[str, Any]) -> float:
        """Determine if this tool should be used based on intent and context."""
        base_confidence = super().should_use(intent, context)
        
        # Boost confidence if we have raw data to process
        if context.get("tool_result_database_query") or "data" in context:
            base_confidence += 0.4
        
        # Boost for analysis-related keywords
        analysis_keywords = ["analyze", "process", "insights", "trends", "summary"]
        intent_lower = intent.lower()
        keyword_matches = sum(1 for keyword in analysis_keywords if keyword in intent_lower)
        
        if keyword_matches > 0:
            base_confidence += (keyword_matches / len(analysis_keywords)) * 0.2
        
        return min(1.0, base_confidence)
    
    async def cleanup(self) -> None:
        """Cleanup data analysis tool."""
        logger.info("Data analysis tool cleaned up")
