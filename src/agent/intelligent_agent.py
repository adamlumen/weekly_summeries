from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from .tool_selector import ToolSelector
from .context_manager import ContextManager
from ..core.json_utils import serialize_tool_results
from ..tools.registry import tool_registry
from ..tools.base_tool import ToolResult, ToolResultStatus, ToolAction

logger = logging.getLogger(__name__)

class IntelligentAgent:
    """
    Main intelligent agent that makes decisions about tool usage and orchestrates
    the execution of tasks based on user requests.
    """
    
    def __init__(self, 
                 api_key: str,
                 model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 4000,
                 temperature: float = 0.1):
        """
        Initialize the intelligent agent.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            max_tokens: Maximum tokens for responses
            temperature: Temperature for response generation
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        self.tool_selector = ToolSelector()
        self.context_manager = ContextManager()
        
        # System prompt for the agent
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return """You are an intelligent agent that helps users by deciding which tools to use and executing them.

Your capabilities:
1. Analyze user requests to understand their intent
2. Select appropriate tools based on the request
3. Execute tools in the correct order with proper parameters
4. Process and synthesize results from multiple tools
5. Provide comprehensive, tailored responses

Available tool categories:
- Database tools: Retrieve user data, activity logs, preferences
- Google Drive tools: Search and access documentation, guidelines, templates
- Data processing tools: Analyze and transform data
- Summary tools: Generate personalized summaries and insights

Decision-making guidelines:
1. If the user asks for data about a specific user and date, use database tools
2. If they need documentation or guidelines, search Google Drive
3. Always process raw data before presenting it to users
4. Chain tools when one tool's output feeds into another
5. Provide context for your decisions and explain what you found

Be concise but thorough in your responses. Always validate parameters before tool execution."""
    
    async def process_request(self, 
                             user_request: str, 
                             user_id: Optional[str] = None,
                             additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user request and return a comprehensive response.
        
        Args:
            user_request: The user's request/question
            user_id: Optional user ID for context
            additional_context: Optional additional context
            
        Returns:
            Dictionary with response data, tool results, and metadata
        """
        logger.info(f"Processing request: {user_request}")
        
        # Build context for the request
        context = self.context_manager.build_context(
            user_request=user_request,
            user_id=user_id,
            additional_context=additional_context or {}
        )
        
        try:
            # Step 1: Check if this is a conversational request that doesn't need tools
            if self._is_conversational_request(user_request):
                response = await self._generate_conversational_response(user_request, context)
                return {
                    "response": response,
                    "status": "conversational",
                    "tool_results": [],
                    "tool_actions": [],
                    "context": context,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Analyze intent and select tools - iterative approach
            all_tool_results = []
            all_tool_actions = []
            max_iterations = 3  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Tool execution iteration {iteration}")
                
                # Analyze current request with accumulated context
                current_context = {**context, "previous_results": [{"tool": r.tool_name, "status": r.status.value, "has_data": bool(r.data)} for r in all_tool_results]}
                tool_actions = await self._analyze_and_select_tools(user_request, current_context)
                
                if not tool_actions:
                    break  # No more tools needed
                
                # Execute tools in this iteration
                tool_results = await self._execute_tools(tool_actions, current_context)
                all_tool_results.extend(tool_results)
                all_tool_actions.extend(tool_actions)
                
                # Check if we have sufficient information to answer
                if await self._has_sufficient_information(user_request, all_tool_results, current_context):
                    break
                
                # Update context for next iteration
                self.context_manager.update_context(context, tool_results)
            
            # If no tools were used at all, provide a conversational fallback
            if not all_tool_results:
                response = await self._generate_conversational_response(user_request, context)
                return {
                    "response": response,
                    "status": "conversational_fallback",
                    "tool_results": [],
                    "tool_actions": [],
                    "context": context,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 3: Generate final response
            final_response = await self._generate_response(
                user_request, all_tool_results, context
            )
            
            # Step 4: Update context with all results
            self.context_manager.update_context(context, all_tool_results)
            
            return {
                "response": final_response,
                "status": "success",
                "tool_results": serialize_tool_results(all_tool_results),
                "tool_actions": [action.__dict__ for action in all_tool_actions],
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "status": "error",
                "error": str(e),
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_and_select_tools(self, 
                                       user_request: str, 
                                       context: Dict[str, Any]) -> List[ToolAction]:
        """
        Analyze the user request and select appropriate tools.
        """
        # Get tool recommendations from the tool selector
        recommended_tools = self.tool_selector.select_tools(user_request, context)
        
        if not recommended_tools:
            return []
        
        # Use OpenAI to determine specific tool actions and parameters
        tool_actions = await self._get_tool_actions_from_llm(
            user_request, recommended_tools, context
        )
        
        return tool_actions
    
    async def _get_tool_actions_from_llm(self,
                                        user_request: str,
                                        recommended_tools: List[tuple],
                                        context: Dict[str, Any]) -> List[ToolAction]:
        """
        Use the LLM to determine specific tool actions and parameters.
        """
        # Build prompt for tool selection
        tools_info = []
        for tool, confidence in recommended_tools:
            capabilities = tool.capabilities
            tools_info.append({
                "name": capabilities.name,
                "description": capabilities.description,
                "parameters": capabilities.parameters,
                "confidence": confidence
            })
        
        prompt = f"""
        User request: "{user_request}"
        
        Available tools: {json.dumps(tools_info, indent=2)}
        
        Context: {json.dumps(context, indent=2)}
        
        Determine which tools to use and with what parameters. Consider:
        1. What information is needed to answer the request?
        2. Which tools can provide that information?
        3. What parameters are required for each tool?
        4. What is the optimal order of execution?
        
        Return a JSON list of tool actions with this format:
        [
            {{
                "tool_name": "tool_name",
                "parameters": {{"param1": "value1", "param2": "value2"}},
                "priority": 1,
                "reasoning": "why this tool is needed"
            }}
        ]
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse the response to extract tool actions
            response_text = response.choices[0].message.content
            
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                actions_data = json.loads(json_match.group())
                
                tool_actions = []
                for action_data in actions_data:
                    action = ToolAction(
                        tool_name=action_data["tool_name"],
                        parameters=action_data["parameters"],
                        priority=action_data.get("priority", 1)
                    )
                    tool_actions.append(action)
                
                return tool_actions
            
        except Exception as e:
            logger.error(f"Error getting tool actions from LLM: {e}")
        
        # Fallback: create simple actions for recommended tools
        tool_actions = []
        for i, (tool, confidence) in enumerate(recommended_tools[:3]):  # Limit to top 3
            action = ToolAction(
                tool_name=tool.capabilities.name,
                parameters=self._extract_basic_parameters(user_request, context),
                priority=i + 1
            )
            tool_actions.append(action)
        
        return tool_actions
    
    def _extract_basic_parameters(self, user_request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic parameters from the user request and context.
        This is a fallback when LLM parsing fails.
        """
        parameters = {}
        
        # Extract user_id from context or request
        if "user_id" in context:
            parameters["user_id"] = context["user_id"]
        
        # Extract date from context or request
        if "date" in context:
            parameters["date"] = context["date"]
        
        # Add the user request as a query parameter
        parameters["query"] = user_request
        
        return parameters
    
    async def _execute_tools(self, 
                            tool_actions: List[ToolAction], 
                            context: Dict[str, Any]) -> List[ToolResult]:
        """
        Execute the selected tools in the appropriate order.
        """
        results = []
        
        # Sort actions by priority
        sorted_actions = sorted(tool_actions, key=lambda x: x.priority)
        
        for action in sorted_actions:
            tool = tool_registry.get_tool(action.tool_name)
            if not tool:
                logger.warning(f"Tool {action.tool_name} not found in registry")
                continue
            
            try:
                # Validate parameters
                validated_params = tool.validate_parameters(**action.parameters)
                
                # Execute the tool
                logger.info(f"Executing tool: {action.tool_name} with params: {validated_params}")
                result = await tool.execute(**validated_params)
                
                results.append(result)
                
                # Add result to context for subsequent tools
                context[f"tool_result_{action.tool_name}"] = result.data
                
            except Exception as e:
                logger.error(f"Error executing tool {action.tool_name}: {e}")
                error_result = ToolResult(
                    tool_name=action.tool_name,
                    status=ToolResultStatus.ERROR,
                    error=str(e)
                )
                results.append(error_result)
        
        return results
    
    async def _generate_response(self,
                                user_request: str,
                                tool_results: List[ToolResult],
                                context: Dict[str, Any]) -> str:
        """
        Generate a final response based on tool results.
        """
        # Prepare tool results summary for the LLM
        results_summary = []
        for result in tool_results:
            summary = {
                "tool": result.tool_name,
                "status": result.status.value,
                "data": result.data if result.status == ToolResultStatus.SUCCESS else None,
                "error": result.error if result.status == ToolResultStatus.ERROR else None
            }
            results_summary.append(summary)
        
        prompt = f"""
        User request: "{user_request}"
        
        Tool execution results: {json.dumps(results_summary, indent=2)}
        
        Context: {json.dumps(context, indent=2)}
        
        Based on the tool results, provide a comprehensive, helpful response to the user.
        
        Guidelines:
        1. Synthesize information from multiple tools if available
        2. Provide specific insights and actionable information
        3. If data processing was involved, highlight key findings
        4. If errors occurred, acknowledge them and suggest alternatives
        5. Be conversational but informative
        6. Tailor the response to the user's specific request
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I processed your request using {len(tool_results)} tools, but encountered an error generating the final response. The tools executed successfully and gathered the requested information."

    def _is_conversational_request(self, user_request: str) -> bool:
        """
        Determine if this is a conversational request that doesn't need tools.
        """
        conversational_patterns = [
            "hi", "hello", "hey", "what model are you", "who are you", "what are you",
            "how are you", "what can you do", "what do you do", "help", "thank you",
            "thanks", "bye", "goodbye", "what's your name", "introduce yourself",
            "tell me about yourself", "what are your capabilities", "how do you work"
        ]
        
        request_lower = user_request.lower().strip()
        
        # Check for exact matches or partial matches
        for pattern in conversational_patterns:
            if pattern in request_lower:
                return True
        
        # Check if it's a very short request (likely conversational)
        if len(request_lower.split()) <= 3 and not any(keyword in request_lower for keyword in 
            ["table", "data", "query", "search", "find", "show", "get", "list", "database", "snowflake"]):
            return True
            
        return False

    async def _generate_conversational_response(self, user_request: str, context: Dict[str, Any]) -> str:
        """
        Generate a conversational response without using tools.
        """
        prompt = f"""
        User request: "{user_request}"
        
        This appears to be a conversational request that doesn't require using any tools.
        Please provide a helpful, friendly response as an AI assistant.
        
        You are an intelligent assistant that can help with:
        - Snowflake database queries and analysis
        - Notion document searches
        - Slack message sending
        - Data analysis and processing
        - Generating summaries and insights
        
        Be conversational, helpful, and explain what you can do if the user is asking about your capabilities.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant with access to various tools for data analysis, database queries, and productivity tasks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return "Hello! I'm an AI assistant that can help you with database queries, document searches, data analysis, and more. How can I assist you today?"

    async def _has_sufficient_information(self, user_request: str, tool_results: List[ToolResult], context: Dict[str, Any]) -> bool:
        """
        Determine if we have sufficient information to answer the user's request.
        """
        if not tool_results:
            return False
        
        # Check if any tools succeeded
        successful_results = [r for r in tool_results if r.status == ToolResultStatus.SUCCESS]
        if not successful_results:
            return False
        
        # Use LLM to determine if we have enough information
        results_summary = []
        for result in successful_results:
            results_summary.append({
                "tool": result.tool_name,
                "status": "success",
                "data_available": bool(result.data)
            })
        
        prompt = f"""
        User request: "{user_request}"
        
        Available information from tools: {json.dumps(results_summary, indent=2)}
        
        Based on the user's request and the information gathered from tools, do we have sufficient information to provide a complete and helpful answer?
        
        Respond with only "YES" if we have enough information, or "NO" if we need more information or different tools.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are helping determine if enough information has been gathered to answer a user's question."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return answer.startswith("YES")
            
        except Exception as e:
            logger.error(f"Error checking if sufficient information: {e}")
            # Default to having sufficient info if we have successful results
            return len(successful_results) > 0
