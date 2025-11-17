from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import re


class EventDetails(BaseModel):
    """Structured event details with comprehensive extraction template"""

    title: str = Field(..., description="Event name/title")
    date: Optional[str] = Field(
        None, description="Event date (e.g., 'November 23, 2025' or '2025-11-23')"
    )
    start_time: Optional[str] = Field(
        None, description="Event start time (e.g., '7:00 PM' or '19:00')"
    )
    end_time: Optional[str] = Field(
        None, description="Event end time (e.g., '10:00 PM' or '22:00')"
    )
    timezone: Optional[str] = Field(
        None, description="Event timezone (e.g., 'PST', 'EST', 'UTC-8')"
    )
    location_name: Optional[str] = Field(None, description="Venue or location name")
    location_address: Optional[str] = Field(None, description="Street address")
    location_city: Optional[str] = Field(None, description="City")
    location_state: Optional[str] = Field(None, description="State/Province")
    location_country: Optional[str] = Field(None, description="Country")
    is_online: bool = Field(False, description="Whether event is online/virtual")
    online_link: Optional[str] = Field(
        None, description="Online meeting link if virtual"
    )
    description: Optional[str] = Field(None, description="Full event description")
    organizer: Optional[str] = Field(None, description="Event organizer/host name")
    organizer_profile: Optional[str] = Field(None, description="Organizer profile URL")
    category: Optional[str] = Field(
        None, description="Event category (e.g., 'Music', 'Sports', 'Business')"
    )
    ticket_url: Optional[str] = Field(
        None, description="Ticket purchase URL if applicable"
    )
    price: Optional[str] = Field(None, description="Ticket price or 'Free'")
    capacity: Optional[int] = Field(None, description="Maximum attendees")
    going_count: Optional[int] = Field(
        None, description="Number of people marked as going"
    )
    interested_count: Optional[int] = Field(
        None, description="Number of people interested"
    )
    cover_image_url: Optional[str] = Field(None, description="Event cover image URL")
    url: str = Field(..., description="Original Facebook event URL")

    def get_full_location(self) -> Optional[str]:
        """Get formatted full location string"""
        parts = []
        if self.location_name:
            parts.append(self.location_name)
        if self.location_address:
            parts.append(self.location_address)
        if self.location_city:
            parts.append(self.location_city)
        if self.location_state:
            parts.append(self.location_state)
        if self.location_country:
            parts.append(self.location_country)
        return ", ".join(parts) if parts else None

    def convert_datetime_for_discord(
        self,
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Parse date/time strings into datetime objects for Discord"""
        if not self.date:
            return None, None

        try:
            # Try to parse common date formats
            date_str = self.date

            # Handle formats like "November 23, 2025"
            if re.match(r"^[A-Za-z]+ \d{1,2}, \d{4}$", date_str):
                base_date = datetime.strptime(date_str, "%B %d, %Y")
            # Handle ISO format "2025-11-23"
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                base_date = datetime.strptime(date_str, "%Y-%m-%d")
            # Handle "Nov 23, 2025"
            elif re.match(r"^[A-Za-z]{3} \d{1,2}, \d{4}$", date_str):
                base_date = datetime.strptime(date_str, "%b %d, %Y")
            else:
                return None, None

            # Parse start time
            start_dt = None
            if self.start_time:
                time_match = re.search(
                    r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?", self.start_time
                )
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    meridiem = time_match.group(3)

                    if meridiem and meridiem.upper() == "PM" and hour < 12:
                        hour += 12
                    elif meridiem and meridiem.upper() == "AM" and hour == 12:
                        hour = 0

                    start_dt = base_date.replace(hour=hour, minute=minute)

            # Parse end time
            end_dt = None
            if self.end_time and start_dt:
                time_match = re.search(
                    r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?", self.end_time
                )
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    meridiem = time_match.group(3)

                    if meridiem and meridiem.upper() == "PM" and hour < 12:
                        hour += 12
                    elif meridiem and meridiem.upper() == "AM" and hour == 12:
                        hour = 0

                    end_dt = base_date.replace(hour=hour, minute=minute)

            # If no times provided, set reasonable defaults
            if not start_dt and base_date:
                start_dt = base_date.replace(hour=19, minute=0)  # Default to 7 PM
            if not end_dt and start_dt:
                end_dt = start_dt + timedelta(hours=3)  # Default 3 hour duration

            return start_dt, end_dt

        except Exception as e:
            print(f"Error parsing date/time: {e}")
            return None, None
