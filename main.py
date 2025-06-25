#!/usr/bin/env python3
"""
Google Calendar MCP Server using FastMCP
A Model Context Protocol server that provides Google Calendar integration tools.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import os

# FastMCP imports
from mcp.server.fastmcp import FastMCP

# Your existing imports
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scopes required for Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Required environment variables
NANGO_CONNECTION_ID = os.environ.get("NANGO_CONNECTION_ID")
NANGO_INTEGRATION_ID = os.environ.get("NANGO_INTEGRATION_ID")

if not NANGO_CONNECTION_ID:
    raise ValueError("NANGO_CONNECTION_ID environment variable is required")
if not NANGO_INTEGRATION_ID:
    raise ValueError("NANGO_INTEGRATION_ID environment variable is required")

class GoogleCalendarAuth:
    """Handle Google Calendar authentication via Nango"""
    
    @staticmethod
    def get_connection_credentials(connection_id: str, provider_config_key: str) -> Dict[str, Any]:
        """Get credentials from Nango"""
        base_url = os.environ.get("NANGO_NANGO_BASE_URL")
        secret_key = os.environ.get("NANGO_NANGO_SECRET_KEY")
        
        if not base_url or not secret_key:
            raise ValueError("NANGO_NANGO_BASE_URL and NANGO_NANGO_SECRET_KEY must be set")
        
        url = f"{base_url}/connection/{connection_id}"
        params = {
            "provider_config_key": provider_config_key,
            "refresh_token": "true",
        }
        headers = {"Authorization": f"Bearer {secret_key}"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    @staticmethod
    def authenticate_google_calendar(connection_id: str, provider_config_key: str):
        """Authenticate using Nango credentials and return Google Calendar service object"""
        try:
            # Get credentials from Nango
            nango_response = GoogleCalendarAuth.get_connection_credentials(connection_id, provider_config_key)
            
            # Extract credentials from Nango response
            credentials_data = nango_response.get('credentials', {})
            
            # Create Google OAuth2 credentials object
            creds = Credentials(
                token=credentials_data.get('access_token'),
                refresh_token=credentials_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=credentials_data.get('client_id'),
                client_secret=credentials_data.get('client_secret'),
                scopes=SCOPES
            )
            
            # Refresh token if needed
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise Exception("Invalid credentials and no refresh token available")
            
            # Build and return the service
            service = build('calendar', 'v3', credentials=creds)
            return service
            
        except Exception as error:
            logger.error(f'Authentication error: {error}')
            raise

class GoogleCalendarTools:
    """Google Calendar operations"""
    
    @staticmethod
    def get_all_calendars(connection_id: str, provider_config_key: str) -> List[Dict]:
        """Get all calendars with optimized field selection"""
        try:
            service = GoogleCalendarAuth.authenticate_google_calendar(connection_id, provider_config_key)
            
            calendars = []
            page_token = None
            
            fields = "nextPageToken,items(id,summary,description,primary,accessRole,backgroundColor,foregroundColor,timeZone)"
            
            while True:
                request_params = {'fields': fields}
                if page_token:
                    request_params['pageToken'] = page_token
                
                calendar_list = service.calendarList().list(**request_params).execute()
                
                page_calendars = calendar_list.get('items', [])
                calendars.extend(page_calendars)
                
                page_token = calendar_list.get('nextPageToken')
                if not page_token:
                    break
            
            return calendars
        
        except HttpError as error:
            logger.error(f'HTTP error in get_all_calendars: {error}')
            raise
        except Exception as error:
            logger.error(f'Unexpected error in get_all_calendars: {error}')
            raise

    @staticmethod
    def get_calendar_events(connection_id: str, provider_config_key: str, calendar_id: str = "primary", 
                           time_min: Optional[str] = None, time_max: Optional[str] = None,
                           max_results: int = 10) -> Dict:
        """Get events from Google Calendar with flexible filtering"""
        try:
            service = GoogleCalendarAuth.authenticate_google_calendar(connection_id, provider_config_key)
            
            params = {
                'calendarId': calendar_id,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            if time_min:
                params['timeMin'] = time_min
            if time_max:
                params['timeMax'] = time_max
            
            events_result = service.events().list(**params).execute()
            events = events_result.get('items', [])
            
            # Format events for better usability
            formatted_events = []
            for event in events:
                formatted_event = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': event.get('start', {}),
                    'end': event.get('end', {}),
                    'location': event.get('location', ''),
                    'status': event.get('status', ''),
                    'created': event.get('created'),
                    'updated': event.get('updated'),
                    'html_link': event.get('htmlLink'),
                    'calendar_id': calendar_id
                }
                formatted_events.append(formatted_event)
            
            return {
                "success": True,
                "events": formatted_events,
                "total_events": len(formatted_events),
                "calendar_id": calendar_id,
                "message": f"Retrieved {len(formatted_events)} events successfully"
            }
            
        except HttpError as error:
            logger.error(f'HTTP error in get_calendar_events: {error}')
            return {
                "success": False,
                "message": f"HTTP error occurred: {error}",
                "error": f"http_error_{error.resp.status if hasattr(error, 'resp') else 'unknown'}",
                "calendar_id": calendar_id
            }
        except Exception as error:
            logger.error(f'Unexpected error in get_calendar_events: {error}')
            return {
                "success": False,
                "message": f"Unexpected error occurred: {str(error)}",
                "error": "unexpected_error",
                "calendar_id": calendar_id
            }

    @staticmethod
    def create_meet_event(connection_id: str, provider_config_key: str, summary: str, 
                         start_datetime: str, end_datetime: str, description: str = "", 
                         attendees: Optional[List[str]] = None, timezone: str = 'UTC',
                         calendar_id: str = 'primary') -> Optional[Dict]:
        """Create a new event in Google Calendar with Google Meet integration"""
        try:
            service = GoogleCalendarAuth.authenticate_google_calendar(connection_id, provider_config_key)
            
            if not summary:
                raise ValueError("Event summary (title) is required")
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': timezone,
                }
            }
            
            # Add attendees if provided
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Add Google Meet conference
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"meet-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
            
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()
            
            return created_event
            
        except HttpError as error:
            logger.error(f'HTTP error in create_meet_event: {error}')
            return None
        except Exception as error:
            logger.error(f'Unexpected error in create_meet_event: {error}')
            return None

    @staticmethod
    def cancel_calendar_event(connection_id: str, provider_config_key: str, 
                             calendar_id: str, event_id: str) -> Dict:
        """Cancel (delete) a specific event from Google Calendar"""
        try:
            service = GoogleCalendarAuth.authenticate_google_calendar(connection_id, provider_config_key)
            
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return {
                "success": True,
                "message": f"Event {event_id} successfully cancelled",
                "event_id": event_id,
                "calendar_id": calendar_id
            }
            
        except HttpError as error:
            if hasattr(error, 'resp'):
                if error.resp.status == 404:
                    return {
                        "success": False,
                        "message": f"Event not found: {event_id}",
                        "error": "event_not_found",
                        "event_id": event_id
                    }
                elif error.resp.status == 403:
                    return {
                        "success": False,
                        "message": "Insufficient permissions to cancel this event",
                        "error": "permission_denied",
                        "event_id": event_id
                    }
            
            return {
                "success": False,
                "message": f"HTTP error occurred: {error}",
                "error": "http_error",
                "event_id": event_id
            }
        
        except Exception as error:
            logger.error(f'Unexpected error in cancel_calendar_event: {error}')
            return {
                "success": False,
                "message": f"Unexpected error occurred: {str(error)}",
                "error": "unexpected_error",
                "event_id": event_id
            }

# Initialize FastMCP server
mcp = FastMCP("Google Calendar Server")

@mcp.tool()
def get_all_calendars() -> str:
    """Get all Google Calendars accessible to the user"""
    try:
        calendars = GoogleCalendarTools.get_all_calendars(NANGO_CONNECTION_ID, NANGO_INTEGRATION_ID)
        
        result = {
            "success": True,
            "calendars": calendars,
            "total_calendars": len(calendars),
            "message": f"Retrieved {len(calendars)} calendars successfully"
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_all_calendars: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve calendars"
        }, indent=2)

@mcp.tool()
def get_calendar_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    Get events from a specific Google Calendar
    
    Args:
        calendar_id: Calendar ID (default: primary)
        time_min: Lower bound for event start time (ISO format)
        time_max: Upper bound for event start time (ISO format)
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        result = GoogleCalendarTools.get_calendar_events(
            NANGO_CONNECTION_ID, NANGO_INTEGRATION_ID, calendar_id, time_min, time_max, max_results
        )
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_calendar_events: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve calendar events"
        }, indent=2)

@mcp.tool()
def create_meet_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    attendees: Optional[List[str]] = None,
    timezone: str = "UTC",
    calendar_id: str = "primary"
) -> str:
    """
    Create a new Google Calendar event with Google Meet integration
    
    Args:
        summary: Event title/summary
        start_datetime: Start datetime in ISO format (e.g., '2024-12-25T10:00:00')
        end_datetime: End datetime in ISO format (e.g., '2024-12-25T11:00:00')
        description: Event description
        attendees: List of attendee emails
        timezone: Timezone (default: UTC)
        calendar_id: Calendar ID (default: primary)
    """
    try:
        result = GoogleCalendarTools.create_meet_event(
            NANGO_CONNECTION_ID, NANGO_INTEGRATION_ID, summary, start_datetime, end_datetime,
            description, attendees, timezone, calendar_id
        )
        
        if result:
            return json.dumps({
                "success": True,
                "event": result,
                "message": "Event created successfully"
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "message": "Failed to create event"
            }, indent=2)
    except Exception as e:
        logger.error(f"Error in create_meet_event: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to create calendar event"
        }, indent=2)

@mcp.tool()
def cancel_calendar_event(calendar_id: str, event_id: str) -> str:
    """
    Cancel (delete) a specific event from Google Calendar
    
    Args:
        calendar_id: Calendar ID where the event exists
        event_id: The unique identifier of the event to cancel
    """
    try:
        result = GoogleCalendarTools.cancel_calendar_event(
            NANGO_CONNECTION_ID, NANGO_INTEGRATION_ID, calendar_id, event_id
        )
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in cancel_calendar_event: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to cancel calendar event"
        }, indent=2)

@mcp.tool()
def get_today_events(calendar_id: str = "primary") -> str:
    """
    Get today's events from the primary calendar
    
    Args:
        calendar_id: Calendar ID (default: primary)
    """
    try:
        # Get today's date range
        today = datetime.now()
        time_min = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        time_max = today.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        
        result = GoogleCalendarTools.get_calendar_events(
            NANGO_CONNECTION_ID, NANGO_INTEGRATION_ID, calendar_id, time_min, time_max, 50
        )
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_today_events: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve today's events"
        }, indent=2)

@mcp.tool()
def get_upcoming_events(days_ahead: int = 7, calendar_id: str = "primary") -> str:
    """
    Get upcoming events for the next N days
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
        calendar_id: Calendar ID (default: primary)
    """
    try:
        # Calculate date range
        now = datetime.now()
        future = now + timedelta(days=days_ahead)
        time_min = now.isoformat() + 'Z'
        time_max = future.isoformat() + 'Z'
        
        result = GoogleCalendarTools.get_calendar_events(
            NANGO_CONNECTION_ID, NANGO_INTEGRATION_ID, calendar_id, time_min, time_max, 50
        )
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_upcoming_events: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve upcoming events"
        }, indent=2)
    
def run():
    """Run the FastMCP server"""
    logger.info("Starting Google Calendar MCP Server...")
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise