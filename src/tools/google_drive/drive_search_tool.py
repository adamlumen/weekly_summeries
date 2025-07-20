from typing import Dict, Any, Optional, List
import asyncio
import logging
import io
import mimetypes
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..base_tool import BaseTool, ToolCapability, ToolResult, ToolResultStatus

logger = logging.getLogger(__name__)

class GoogleDriveTool(BaseTool):
    """
    Google Drive tool for searching and retrieving documents.
    Provides access to documentation, guidelines, templates, and other files.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.credentials_file = config.get("credentials_file") if config else None
        self.token_file = config.get("token_file") if config else None
        self.scopes = config.get("scopes", ["https://www.googleapis.com/auth/drive.readonly"]) if config else ["https://www.googleapis.com/auth/drive.readonly"]
        
        self.service = None
        self.credentials = None
    
    @property
    def capabilities(self) -> ToolCapability:
        return ToolCapability(
            name="drive_search",
            description="Search and retrieve documents from Google Drive",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query for finding documents",
                    "required": True
                },
                "doc_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Document types to search for (e.g., 'pdf', 'doc', 'txt')",
                    "default": ["pdf", "doc", "docx", "txt"]
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Whether to include document content in results",
                    "default": True
                }
            },
            use_cases=[
                "documentation", "guidelines", "templates", "policies", 
                "procedures", "manuals", "examples", "references"
            ],
            data_sources=["google_drive"],
            prerequisites=["google_auth"],
            confidence_keywords=[
                "document", "guide", "guideline", "template", "policy", 
                "procedure", "manual", "example", "reference", "documentation",
                "format", "standard", "specification"
            ]
        )
    
    async def initialize(self) -> bool:
        """Initialize Google Drive API connection."""
        try:
            # Load or refresh credentials
            self.credentials = await self._get_credentials()
            
            if not self.credentials or not self.credentials.valid:
                logger.error("Failed to obtain valid Google Drive credentials")
                return False
            
            # Build the Drive service
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            # Test the connection
            about = self.service.about().get(fields="user").execute()
            logger.info(f"Connected to Google Drive for user: {about.get('user', {}).get('emailAddress', 'Unknown')}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive tool: {e}")
            return False
    
    async def _get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials for Google Drive API."""
        credentials = None
        
        # Load existing token if available
        if self.token_file and Path(self.token_file).exists():
            try:
                credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
        
        # Refresh credentials if they exist but are invalid
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                credentials = None
        
        # If no valid credentials, initiate OAuth flow
        if not credentials or not credentials.valid:
            if not self.credentials_file or not Path(self.credentials_file).exists():
                logger.error("No credentials file found for Google Drive authentication")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                credentials = flow.run_local_server(port=0)
                
                # Save the credentials for next time
                if self.token_file:
                    with open(self.token_file, 'w') as token_file:
                        token_file.write(credentials.to_json())
                        
            except Exception as e:
                logger.error(f"Failed to complete OAuth flow: {e}")
                return None
        
        return credentials
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute Google Drive search and document retrieval."""
        if not self._initialized:
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                error="Tool not initialized"
            )
        
        try:
            # Extract parameters
            query = kwargs.get("query", "")
            doc_types = kwargs.get("doc_types", ["pdf", "doc", "docx", "txt"])
            max_results = kwargs.get("max_results", 10)
            include_content = kwargs.get("include_content", True)
            
            if not query:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    error="Query parameter is required"
                )
            
            # Search for files
            search_results = await self._search_files(query, doc_types, max_results)
            
            if not search_results:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.SUCCESS,
                    data={
                        "query": query,
                        "results": [],
                        "total_found": 0,
                        "message": "No documents found matching your query"
                    }
                )
            
            # Process results and optionally include content
            processed_results = []
            for file_info in search_results:
                result_item = {
                    "id": file_info["id"],
                    "name": file_info["name"],
                    "mimeType": file_info.get("mimeType", ""),
                    "size": file_info.get("size", "0"),
                    "modifiedTime": file_info.get("modifiedTime", ""),
                    "webViewLink": file_info.get("webViewLink", ""),
                    "owners": file_info.get("owners", [])
                }
                
                # Include content if requested and possible
                if include_content:
                    content = await self._extract_file_content(file_info)
                    if content:
                        result_item["content"] = content
                        result_item["content_preview"] = content[:500] + "..." if len(content) > 500 else content
                
                processed_results.append(result_item)
            
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.SUCCESS,
                data={
                    "query": query,
                    "results": processed_results,
                    "total_found": len(processed_results),
                    "search_parameters": {
                        "doc_types": doc_types,
                        "max_results": max_results,
                        "include_content": include_content
                    }
                },
                metadata={
                    "search_query": query,
                    "files_found": len(processed_results)
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing Google Drive search: {e}")
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    async def _search_files(self, 
                           query: str, 
                           doc_types: List[str], 
                           max_results: int) -> List[Dict[str, Any]]:
        """Search for files in Google Drive."""
        try:
            # Build the search query
            mime_types = self._get_mime_types_for_extensions(doc_types)
            
            # Create the Drive API query
            drive_query_parts = [f"name contains '{query}'"]
            
            if mime_types:
                mime_query = " or ".join([f"mimeType='{mime}'" for mime in mime_types])
                drive_query_parts.append(f"({mime_query})")
            
            drive_query = " and ".join(drive_query_parts)
            
            # Execute the search
            results = self.service.files().list(
                q=drive_query,
                pageSize=max_results,
                fields="files(id,name,mimeType,size,modifiedTime,webViewLink,owners)"
            ).execute()
            
            return results.get('files', [])
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching Google Drive: {e}")
            raise
    
    def _get_mime_types_for_extensions(self, extensions: List[str]) -> List[str]:
        """Convert file extensions to MIME types."""
        mime_types = []
        
        extension_to_mime = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        for ext in extensions:
            mime_type = extension_to_mime.get(ext.lower())
            if mime_type:
                mime_types.append(mime_type)
        
        return mime_types
    
    async def _extract_file_content(self, file_info: Dict[str, Any]) -> Optional[str]:
        """Extract text content from a file."""
        try:
            file_id = file_info["id"]
            mime_type = file_info.get("mimeType", "")
            
            # Handle different file types
            if mime_type == "application/pdf":
                return await self._extract_pdf_content(file_id)
            elif "document" in mime_type or mime_type == "text/plain":
                return await self._extract_text_content(file_id)
            else:
                logger.debug(f"Unsupported file type for content extraction: {mime_type}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to extract content from file {file_info.get('name', 'unknown')}: {e}")
            return None
    
    async def _extract_text_content(self, file_id: str) -> Optional[str]:
        """Extract text content from text-based files."""
        try:
            # Export as plain text
            content = self.service.files().export(
                fileId=file_id,
                mimeType='text/plain'
            ).execute()
            
            return content.decode('utf-8')
            
        except Exception as e:
            logger.warning(f"Failed to extract text content: {e}")
            return None
    
    async def _extract_pdf_content(self, file_id: str) -> Optional[str]:
        """Extract text content from PDF files."""
        try:
            # Download the PDF file
            file_content = self.service.files().get_media(fileId=file_id).execute()
            
            # Use PyPDF2 to extract text
            from PyPDF2 import PdfReader
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.warning(f"Failed to extract PDF content: {e}")
            return None
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate and clean parameters before execution."""
        validated = {}
        
        # Validate query
        query = kwargs.get("query", "").strip()
        if query:
            validated["query"] = query
        else:
            raise ValueError("Query parameter is required and cannot be empty")
        
        # Validate doc_types
        doc_types = kwargs.get("doc_types", ["pdf", "doc", "docx", "txt"])
        if isinstance(doc_types, str):
            doc_types = [doc_types]
        
        valid_types = ["pdf", "doc", "docx", "txt", "md", "csv", "xlsx", "pptx"]
        validated_types = [dt.lower() for dt in doc_types if dt.lower() in valid_types]
        validated["doc_types"] = validated_types or ["pdf", "doc", "docx", "txt"]
        
        # Validate max_results
        max_results = kwargs.get("max_results", 10)
        try:
            max_results = int(max_results)
            validated["max_results"] = max(1, min(50, max_results))
        except (ValueError, TypeError):
            validated["max_results"] = 10
        
        # Validate include_content
        validated["include_content"] = bool(kwargs.get("include_content", True))
        
        return validated
    
    def should_use(self, intent: str, context: Dict[str, Any]) -> float:
        """Determine if this tool should be used based on intent and context."""
        base_confidence = super().should_use(intent, context)
        
        # Boost confidence for documentation-related requests
        doc_keywords = [
            "document", "guide", "guideline", "template", "policy", 
            "manual", "example", "format", "standard", "documentation"
        ]
        intent_lower = intent.lower()
        
        keyword_matches = sum(1 for keyword in doc_keywords if keyword in intent_lower)
        if keyword_matches > 0:
            base_confidence += (keyword_matches / len(doc_keywords)) * 0.3
        
        # Reduce confidence if this looks like a data query
        data_keywords = ["user_id", "database", "activity", "metrics"]
        data_matches = sum(1 for keyword in data_keywords if keyword in intent_lower)
        if data_matches > 0:
            base_confidence -= 0.2
        
        return max(0.0, min(1.0, base_confidence))
    
    async def cleanup(self) -> None:
        """Cleanup Google Drive service."""
        self.service = None
        self.credentials = None
        logger.info("Google Drive tool cleaned up")
