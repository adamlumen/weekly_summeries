from typing import Dict, Any, Optional
import logging
from datetime import datetime
from ..base_tool import BaseTool, ToolCapability, ToolResult, ToolResultStatus

logger = logging.getLogger(__name__)

class SummaryTool(BaseTool):
    """
    Summary generation tool that creates personalized summaries based on
    processed data and analysis results.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    @property
    def capabilities(self) -> ToolCapability:
        return ToolCapability(
            name="summary_generation",
            description="Generate personalized summaries and reports",
            parameters={
                "processed_data": {
                    "type": "object",
                    "description": "Processed data from analysis tools",
                    "required": True
                },
                "summary_type": {
                    "type": "string",
                    "description": "Type of summary to generate",
                    "enum": ["weekly_report", "daily_digest", "monthly_overview", "custom"],
                    "default": "weekly_report"
                },
                "user_preferences": {
                    "type": "object",
                    "description": "User preferences for summary format",
                    "default": {}
                },
                "include_recommendations": {
                    "type": "boolean",
                    "description": "Whether to include recommendations",
                    "default": True
                },
                "format": {
                    "type": "string",
                    "description": "Output format for the summary",
                    "enum": ["narrative", "bullet_points", "structured", "mixed"],
                    "default": "mixed"
                }
            },
            use_cases=[
                "summary", "report", "digest", "overview", "recap",
                "personalized_content", "insights_presentation"
            ],
            data_sources=["processed_data", "analysis_results"],
            prerequisites=["processed_data"],
            confidence_keywords=[
                "summary", "report", "overview", "digest", "recap",
                "generate", "create", "personalized", "weekly", "daily"
            ]
        )
    
    def initialize(self) -> bool:
        """Initialize the summary tool."""
        self._initialized = True
        logger.info("Summary tool initialized")
        return True
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute summary generation."""
        try:
            # Extract parameters
            processed_data = kwargs.get("processed_data")
            summary_type = kwargs.get("summary_type", "weekly_report")
            user_preferences = kwargs.get("user_preferences", {})
            include_recommendations = kwargs.get("include_recommendations", True)
            output_format = kwargs.get("format", "mixed")
            
            if not processed_data:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    error="Processed data is required for summary generation"
                )
            
            # Generate summary based on type
            if summary_type == "weekly_report":
                summary_content = self._generate_weekly_report(
                    processed_data, user_preferences, include_recommendations, output_format
                )
            elif summary_type == "daily_digest":
                summary_content = self._generate_daily_digest(
                    processed_data, user_preferences, include_recommendations, output_format
                )
            elif summary_type == "monthly_overview":
                summary_content = self._generate_monthly_overview(
                    processed_data, user_preferences, include_recommendations, output_format
                )
            else:  # custom
                summary_content = self._generate_custom_summary(
                    processed_data, user_preferences, include_recommendations, output_format
                )
            
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.SUCCESS,
                data={
                    "summary": summary_content,
                    "summary_type": summary_type,
                    "format": output_format,
                    "generated_at": datetime.now().isoformat(),
                    "word_count": len(summary_content.split()) if isinstance(summary_content, str) else 0
                },
                metadata={
                    "summary_type": summary_type,
                    "include_recommendations": include_recommendations,
                    "output_format": output_format
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    def _generate_weekly_report(self, 
                               processed_data: Dict[str, Any], 
                               user_preferences: Dict[str, Any],
                               include_recommendations: bool,
                               output_format: str) -> str:
        """Generate a weekly activity report."""
        
        # Extract key metrics from processed data
        metrics = processed_data.get("metrics", {})
        key_insights = processed_data.get("key_insights", [])
        trends = processed_data.get("trends", [])
        
        # Build the summary
        summary_parts = []
        
        # Header
        summary_parts.append("# Weekly Activity Report")
        summary_parts.append(f"Report generated on {datetime.now().strftime('%B %d, %Y')}")
        summary_parts.append("")
        
        # Overview section
        summary_parts.append("## Overview")
        
        if "activities" in metrics:
            activities = metrics["activities"]
            total_activities = activities.get("total_activities", 0)
            avg_daily = activities.get("average_daily", 0)
            
            summary_parts.append(f"This week you completed **{total_activities} activities** with an average of **{avg_daily} activities per day**.")
            
            if activities.get("most_common_type"):
                summary_parts.append(f"Your most frequent activity type was **{activities['most_common_type']}**.")
        
        if "duration" in metrics:
            duration = metrics["duration"]
            total_hours = duration.get("total_hours", 0)
            avg_duration = duration.get("average_duration", 0)
            
            summary_parts.append(f"You spent a total of **{total_hours} hours** in activities, averaging **{avg_duration} minutes** per session.")
        
        summary_parts.append("")
        
        # Key insights section
        if key_insights:
            summary_parts.append("## Key Insights")
            for insight in key_insights:
                summary_parts.append(f"• {insight}")
            summary_parts.append("")
        
        # Trends section
        if trends:
            summary_parts.append("## Trends")
            for trend in trends:
                metric = trend.get("metric", "Unknown")
                direction = trend.get("direction", "stable")
                change = trend.get("change_percentage", 0)
                
                direction_emoji = "📈" if direction == "up" else "📉" if direction == "down" else "➡️"
                summary_parts.append(f"• **{metric.title()}**: {direction_emoji} {direction.title()} ({change:+.1f}%)")
            summary_parts.append("")
        
        # Recommendations section
        if include_recommendations and "recommendations" in processed_data:
            recommendations = processed_data["recommendations"]
            if recommendations:
                summary_parts.append("## Recommendations")
                for rec in recommendations:
                    priority_emoji = "🔥" if rec.get("priority") == "high" else "⚡" if rec.get("priority") == "medium" else "💡"
                    summary_parts.append(f"### {priority_emoji} {rec.get('title', 'Recommendation')}")
                    summary_parts.append(rec.get('description', ''))
                    
                    if rec.get('actionable_steps'):
                        summary_parts.append("**Action steps:**")
                        for step in rec['actionable_steps']:
                            summary_parts.append(f"• {step}")
                    summary_parts.append("")
        
        # Footer
        summary_parts.append("---")
        summary_parts.append("*Keep up the great work! Check back next week for your updated report.*")
        
        return "\n".join(summary_parts)
    
    def _generate_daily_digest(self, 
                              processed_data: Dict[str, Any], 
                              user_preferences: Dict[str, Any],
                              include_recommendations: bool,
                              output_format: str) -> str:
        """Generate a daily activity digest."""
        
        summary_parts = []
        
        # Header
        summary_parts.append("# Daily Activity Digest")
        summary_parts.append(f"Summary for {datetime.now().strftime('%B %d, %Y')}")
        summary_parts.append("")
        
        # Quick stats
        metrics = processed_data.get("metrics", {})
        
        if "activities" in metrics:
            activities = metrics["activities"]
            total_today = activities.get("total_activities", 0)
            
            if total_today > 0:
                summary_parts.append(f"🎯 **{total_today} activities completed today**")
                
                if activities.get("most_common_type"):
                    summary_parts.append(f"🏆 Primary focus: **{activities['most_common_type']}**")
            else:
                summary_parts.append("📝 No activities recorded today")
        
        if "duration" in metrics:
            duration = metrics["duration"]
            total_minutes = duration.get("total_minutes", 0)
            
            if total_minutes > 0:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours > 0:
                    summary_parts.append(f"⏱️ Total time: **{hours}h {minutes}m**")
                else:
                    summary_parts.append(f"⏱️ Total time: **{minutes} minutes**")
        
        summary_parts.append("")
        
        # Key insights
        key_insights = processed_data.get("key_insights", [])
        if key_insights:
            summary_parts.append("## Today's Insights")
            for insight in key_insights[:3]:  # Limit to top 3 for daily digest
                summary_parts.append(f"• {insight}")
            summary_parts.append("")
        
        # Quick recommendations
        if include_recommendations and "recommendations" in processed_data:
            recommendations = processed_data["recommendations"]
            high_priority_recs = [rec for rec in recommendations if rec.get("priority") == "high"]
            
            if high_priority_recs:
                summary_parts.append("## Priority Actions")
                for rec in high_priority_recs[:2]:  # Limit to top 2
                    summary_parts.append(f"🔥 **{rec.get('title', 'Action needed')}**")
                    summary_parts.append(f"   {rec.get('description', '')}")
                summary_parts.append("")
        
        # Footer
        summary_parts.append("*Have a productive day! 🚀*")
        
        return "\n".join(summary_parts)
    
    def _generate_monthly_overview(self, 
                                  processed_data: Dict[str, Any], 
                                  user_preferences: Dict[str, Any],
                                  include_recommendations: bool,
                                  output_format: str) -> str:
        """Generate a monthly overview report."""
        
        summary_parts = []
        
        # Header
        summary_parts.append("# Monthly Overview")
        summary_parts.append(f"Report for {datetime.now().strftime('%B %Y')}")
        summary_parts.append("")
        
        # Executive summary
        summary_parts.append("## Executive Summary")
        
        metrics = processed_data.get("metrics", {})
        
        if "activities" in metrics:
            activities = metrics["activities"]
            total_activities = activities.get("total_activities", 0)
            avg_daily = activities.get("average_daily", 0)
            
            summary_parts.append(f"This month you completed **{total_activities} total activities** with a daily average of **{avg_daily:.1f}**.")
            
            if "duration" in metrics:
                duration = metrics["duration"]
                total_hours = duration.get("total_hours", 0)
                summary_parts.append(f"Total engagement time reached **{total_hours:.1f} hours** this month.")
        
        summary_parts.append("")
        
        # Detailed metrics
        summary_parts.append("## Detailed Metrics")
        
        if "activities" in metrics:
            activities = metrics["activities"]
            summary_parts.append("### Activity Statistics")
            summary_parts.append(f"• Total activities: {activities.get('total_activities', 0)}")
            summary_parts.append(f"• Daily average: {activities.get('average_daily', 0):.1f}")
            summary_parts.append(f"• Peak day: {activities.get('max_daily', 0)} activities")
            summary_parts.append(f"• Lowest day: {activities.get('min_daily', 0)} activities")
            
            if activities.get("activity_types"):
                summary_parts.append("\n### Activity Breakdown")
                for activity_type, count in activities["activity_types"].items():
                    summary_parts.append(f"• {activity_type}: {count}")
            
            summary_parts.append("")
        
        # Trends and patterns
        if "trends" in processed_data:
            trends = processed_data["trends"]
            summary_parts.append("## Trends & Patterns")
            
            for trend in trends:
                metric = trend.get("metric", "Unknown")
                direction = trend.get("direction", "stable")
                change = trend.get("change_percentage", 0)
                
                summary_parts.append(f"• **{metric.title()}**: {direction.title()} trend ({change:+.1f}% change)")
            
            summary_parts.append("")
        
        # Long-term recommendations
        if include_recommendations and "recommendations" in processed_data:
            recommendations = processed_data["recommendations"]
            if recommendations:
                summary_parts.append("## Strategic Recommendations")
                
                for rec in recommendations:
                    summary_parts.append(f"### {rec.get('title', 'Recommendation')}")
                    summary_parts.append(rec.get('description', ''))
                    
                    if rec.get('actionable_steps'):
                        summary_parts.append("**Implementation plan:**")
                        for i, step in enumerate(rec['actionable_steps'], 1):
                            summary_parts.append(f"{i}. {step}")
                    summary_parts.append("")
        
        # Footer
        summary_parts.append("---")
        summary_parts.append("*Thank you for your continued engagement. Here's to an even better next month! 🎉*")
        
        return "\n".join(summary_parts)
    
    def _generate_custom_summary(self, 
                                processed_data: Dict[str, Any], 
                                user_preferences: Dict[str, Any],
                                include_recommendations: bool,
                                output_format: str) -> str:
        """Generate a custom summary based on user preferences."""
        
        # Use weekly report as base template for custom summaries
        # In a full implementation, this would be more sophisticated
        # based on user preferences and customization options
        
        return self._generate_weekly_report(
            processed_data, user_preferences, include_recommendations, output_format
        )
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate parameters before execution."""
        validated = {}
        
        # Validate processed_data
        processed_data = kwargs.get("processed_data")
        if not processed_data:
            raise ValueError("Processed data is required for summary generation")
        
        if not isinstance(processed_data, dict):
            raise ValueError("Processed data must be a dictionary")
        
        validated["processed_data"] = processed_data
        
        # Validate summary_type
        summary_type = kwargs.get("summary_type", "weekly_report")
        valid_types = ["weekly_report", "daily_digest", "monthly_overview", "custom"]
        if summary_type not in valid_types:
            raise ValueError(f"Invalid summary_type. Must be one of: {valid_types}")
        validated["summary_type"] = summary_type
        
        # Validate user_preferences
        user_preferences = kwargs.get("user_preferences", {})
        if not isinstance(user_preferences, dict):
            user_preferences = {}
        validated["user_preferences"] = user_preferences
        
        # Validate include_recommendations
        validated["include_recommendations"] = bool(kwargs.get("include_recommendations", True))
        
        # Validate format
        output_format = kwargs.get("format", "mixed")
        valid_formats = ["narrative", "bullet_points", "structured", "mixed"]
        if output_format not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {valid_formats}")
        validated["format"] = output_format
        
        return validated
    
    def should_use(self, intent: str, context: Dict[str, Any]) -> float:
        """Determine if this tool should be used based on intent and context."""
        base_confidence = super().should_use(intent, context)
        
        # Boost confidence if we have processed data
        if context.get("tool_result_data_analysis") or "processed_data" in context:
            base_confidence += 0.4
        
        # Boost for summary-related keywords
        summary_keywords = ["summary", "report", "overview", "digest", "generate"]
        intent_lower = intent.lower()
        keyword_matches = sum(1 for keyword in summary_keywords if keyword in intent_lower)
        
        if keyword_matches > 0:
            base_confidence += (keyword_matches / len(summary_keywords)) * 0.3
        
        # Additional boost for specific summary types
        if any(term in intent_lower for term in ["weekly", "daily", "monthly"]):
            base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    async def cleanup(self) -> None:
        """Cleanup summary tool."""
        logger.info("Summary tool cleaned up")
