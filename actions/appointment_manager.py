import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .db_connect import db_manager


class AppointmentManager:
    def __init__(self):
        self.appointments = {}
        self.next_id = 1
        # Removed hardcoded doctors list - now validating against database
        # For now, we'll use a default user_id. In a real implementation, 
        # this would come from the user session/context
        self.default_user_id = 1
        self.current_user_id = None

    def handle_rasa_intent(self, rasa_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Rasa-parsed appointment intent"""
        intent_name = rasa_data["intent"]["name"]
        entities = rasa_data["entities"]

        # Convert entities to slots
        slots = self._entities_to_slots(entities)

        # Debug: Print extracted entities and slots
        print(f"DEBUG - Intent: {intent_name}")
        print(f"DEBUG - Entities: {entities}")
        print(f"DEBUG - Slots: {slots}")

        if intent_name == "book_appointment":
            return self.create_appointment(slots)
        elif intent_name == "modify_appointment":
            return self.update_appointment(slots.get("appointment_id"), slots)
        elif intent_name == "cancel_appointment":
            return self.cancel_appointment(slots.get("appointment_id"))
        elif intent_name == "view_appointments":
            return self.get_appointments(slots)
        else:
            raise ValueError(f"Unsupported intent: {intent_name}")

    def _entities_to_slots(self, entities: List[Dict]) -> Dict[str, Any]:
        """Convert Rasa entities array to slots dictionary"""
        slots = {}

        for entity in entities:
            slots[entity["entity"]] = entity["value"]

            # Handle additional entity properties
            if "additional_info" in entity:
                slots[f"{entity['entity']}_info"] = entity["additional_info"]

        return slots

    def set_user_id(self, user_id: int):
        """Set the current user ID for appointments"""
        self.current_user_id = user_id

    def _get_user_id(self) -> int:
        """Get the current user ID, fallback to first available user if not set"""
        if self.current_user_id:
            return self.current_user_id
        
        # If no user_id is set, try to get the first available user from database
        try:
            query = "SELECT id FROM users ORDER BY id LIMIT 1"
            result = db_manager.execute_query(query)
            if result:
                return result[0]['id']
            else:
                raise ValueError("No users found in database. Please create a user account first.")
        except Exception as e:
            raise ValueError(f"Error getting user context: {str(e)}")

    def _get_doctor_id(self, doctor_name: str) -> int:
        """Get doctor ID from database by name"""
        try:
            # Remove Dr. prefix if present for database lookup
            clean_name = re.sub(r'^(dr\.?|doctor)\s+', '', doctor_name.strip(), flags=re.IGNORECASE)
            
            query = "SELECT id FROM doctors WHERE name LIKE %s"
            results = db_manager.execute_query(query, (f"%{clean_name}%",))
            
            if results:
                return results[0]['id']
            else:
                raise ValueError(f"Doctor not found in database: {clean_name}")
        except Exception as e:
            raise ValueError(f"Error finding doctor: {str(e)}")

    def _normalize_doctor_name(self, doctor_input: str) -> str:
        """Normalize doctor name with validation against database"""
        if not doctor_input:
            return None

        # Remove any existing prefix
        doctor_name = re.sub(r'^(dr\.?|doctor)\s+', '', doctor_input.strip(), flags=re.IGNORECASE)
        
        # Check if doctor exists in database
        try:
            query = "SELECT name FROM doctors WHERE name LIKE %s"
            results = db_manager.execute_query(query, (f"%{doctor_name}%",))
            
            if results:
                # Return the actual doctor name from database (already includes Dr. prefix)
                doctor_name = results[0]['name']
                if doctor_name.startswith('Dr.'):
                    return doctor_name
                else:
                    return f"Dr. {doctor_name}"
            else:
                raise ValueError(f"Unknown doctor: {doctor_name}")
        except Exception as e:
            raise ValueError(f"Error validating doctor: {str(e)}")

    def _normalize_reason(self, reason: str) -> str:
        """Normalize and validate reason for visit"""
        if not reason:
            return "General"
            
        reason = str(reason).strip()
        if len(reason) < 3:  # Too short to be meaningful
            return "General"
            
        return reason

    def create_appointment(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Create appointment from slots with validation"""
        try:
            # Check if we have all required information
            required_slots = ["date", "time", "doctor_name"]
            missing_slots = [slot for slot in required_slots if not slots.get(slot)]
            
            if missing_slots:
                return {
                    "success": False,
                    "message": f"Missing required information: {', '.join(missing_slots)}",
                    "missing_slots": missing_slots
                }

            # Normalize all inputs
            normalized_date = self._normalize_date(slots.get("date"))
            normalized_time = self._normalize_time(slots.get("time"), normalized_date)
            normalized_doctor = self._normalize_doctor_name(slots.get("doctor_name"))
            
            # Enhanced reason validation
            reason = slots.get("reason", "").strip()
            if not reason or len(reason) < 3:
                return {
                    "success": False,
                    "message": "Please provide a reason for your visit (at least 3 characters)",
                    "missing_slots": ["reason"]
                }
            
            # Check for invalid reason inputs
            invalid_inputs = [".", ",", "?", "!", "...", ".."]
            if reason in invalid_inputs or reason.replace(".", "").strip() == "":
                return {
                    "success": False,
                    "message": "Please provide a meaningful reason for your visit",
                    "missing_slots": ["reason"]
                }

            # Get doctor ID from database
            doctor_id = self._get_doctor_id(normalized_doctor)
            
            # Combine date and time for database storage
            appointment_datetime = f"{normalized_date} {normalized_time}:00"
            
            # Save appointment to database
            query = """
                INSERT INTO appointments (user_id, doctor_id, appointment_date, reason, status) 
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (self._get_user_id(), doctor_id, appointment_datetime, reason, "scheduled")
            db_manager.execute_query(query, params, fetch=False)
            
            # Get the inserted appointment ID
            get_id_query = "SELECT LAST_INSERT_ID() as id"
            result = db_manager.execute_query(get_id_query)
            appointment_id = result[0]['id']

            # Create appointment object for response
            appointment = {
                "id": appointment_id,
                "date": normalized_date,
                "time": normalized_time,
                "doctor": normalized_doctor,
                "reason": reason,
                "status": "scheduled",
                "created_at": datetime.now().isoformat()
            }

            # Also store in memory for backward compatibility
            self.appointments[appointment_id] = appointment

            # Format confirmation message
            message = (
                f"✅ Appointment confirmed!\n"
                f"📅 {appointment['date']} at {appointment['time']}\n"
                f"👨‍⚕️ {appointment['doctor']}\n"
                f"📝 Reason: {appointment['reason'].capitalize()}"
            )

            return {
                "success": True,
                "appointment": appointment,
                "message": message
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating appointment: {str(e)}"
            }

    def create_appointment_from_slots(self, tracker_slots: Dict[str, Any]) -> Dict[str, Any]:
        """Create appointment using all slots from tracker (for form completion)"""
        # This method is called after form completion
        return self.create_appointment(tracker_slots)

    def update_appointment(self, appointment_id: Optional[str], slots: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing appointment"""
        if not appointment_id:
            # Try to get the most recent appointment
            if self.appointments:
                appointment_id = max(self.appointments.keys())
            else:
                raise ValueError("No appointment ID provided and no appointments found")

        appt_id = int(appointment_id)
        appointment = self.appointments.get(appt_id)

        if not appointment:
            raise ValueError(f"Appointment with ID {appt_id} not found")

        # Update only provided slots
        updatable_fields = ["date", "time", "duration", "doctor", "reason", "location"]
        updates = {}

        for field in updatable_fields:
            if slots.get(field) is not None:
                if field == "date":
                    updates[field] = self._normalize_date(slots[field])
                elif field == "time":
                    updates[field] = self._normalize_time(slots[field])
                else:
                    updates[field] = slots[field]

        # Apply updates
        appointment.update(updates)
        appointment["metadata"]["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "appointment": appointment,
            "message": f"✅ Appointment {appt_id} updated!\n📅 {appointment['date']} at {appointment['time']}",
            "db_string": self._serialize_for_database(appointment)
        }

    def cancel_appointment(self, appointment_id: Optional[str]) -> Dict[str, Any]:
        """Cancel appointment in database"""
        try:
            if not appointment_id:
                return {
                    "success": False,
                    "message": "No appointment ID provided"
                }

            appt_id = int(appointment_id)
            
            # Get the appointment from database first
            query = """
                SELECT a.*, d.name as doctor_name 
                FROM appointments a 
                LEFT JOIN doctors d ON a.doctor_id = d.id 
                WHERE a.id = %s AND a.user_id = %s
            """
            results = db_manager.execute_query(query, (appt_id, self._get_user_id()))
            
            if not results:
                return {
                    "success": False,
                    "message": f"Appointment with ID {appt_id} not found or you don't have permission to cancel it."
                }
            
            appointment = results[0]
            
            # Update the appointment status to cancelled
            update_query = """
                UPDATE appointments 
                SET status = 'cancelled'
                WHERE id = %s AND user_id = %s
            """
            db_manager.execute_query(update_query, (appt_id, self._get_user_id()), fetch=False)
            
            # Format the response
            date_str = appointment["appointment_date"].strftime("%Y-%m-%d") if appointment["appointment_date"] else "Unknown date"
            time_str = appointment["appointment_date"].strftime("%H:%M") if appointment["appointment_date"] else "Unknown time"
            doctor_name = appointment["doctor_name"] if appointment["doctor_name"] else "Unknown doctor"
            
            # Remove "Dr." if it's already in the doctor name
            if doctor_name.startswith("Dr. "):
                display_doctor = doctor_name
            else:
                display_doctor = f"Dr. {doctor_name}"
            
            return {
                "success": True,
                "message": f"✅ Appointment cancelled successfully!\n📅 Was: {date_str} at {time_str}\n👨‍⚕️ {display_doctor}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cancelling appointment: {str(e)}"
            }

    def get_appointments(self, slots: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get appointments from database with optional filters"""
        if slots is None:
            slots = {}

        try:
            # Base query to get appointments with doctor names
            query = """
                SELECT a.*, d.name as doctor_name 
                FROM appointments a 
                LEFT JOIN doctors d ON a.doctor_id = d.id 
                WHERE a.user_id = %s
            """
            params = [self._get_user_id()]

            # Apply filters based on slots
            if slots.get("date"):
                filter_date = self._normalize_date(slots["date"])
                query += " AND DATE(a.appointment_date) = %s"
                params.append(filter_date)

            if slots.get("doctor_name"):
                query += " AND d.name LIKE %s"
                params.append(f"%{slots['doctor_name']}%")

            if slots.get("status"):
                query += " AND a.status = %s"
                params.append(slots["status"])

            query += " ORDER BY a.appointment_date DESC"

            results = db_manager.execute_query(query, params)

            # Convert database results to appointment format
            appointments = []
            for row in results:
                appointment = {
                    "id": row["id"],
                    "date": row["appointment_date"].strftime("%Y-%m-%d") if row["appointment_date"] else None,
                    "time": row["appointment_date"].strftime("%H:%M") if row["appointment_date"] else None,
                    "doctor": row['doctor_name'] if row["doctor_name"] and row['doctor_name'].startswith('Dr.') else f"Dr. {row['doctor_name']}" if row["doctor_name"] else "Unknown Doctor",
                    "reason": row["reason"],
                    "status": row["status"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                }
                appointments.append(appointment)

            return {
                "success": True,
                "appointments": appointments,
                "count": len(appointments),
                "message": f"Found {len(appointments)} appointment(s)"
            }

        except Exception as e:
            return {
                "success": False,
                "appointments": [],
                "count": 0,
                "message": f"Error retrieving appointments: {str(e)}"
            }

    def _serialize_for_database(self, appointment: Dict[str, Any]) -> str:
        """Serialize appointment for database storage"""
        db_data = {
            "id": appointment["id"],
            "title": appointment["title"],
            "datetime": f"{appointment['date']} {appointment['time']}",
            "duration": appointment["duration"],
            "doctor": appointment["doctor"],
            "patient": appointment["patient"],
            "reason": appointment["reason"],
            "location": appointment["location"],
            "phone": appointment["phone"],
            "status": appointment["status"],
            "metadata": appointment["metadata"]
        }

        return json.dumps(db_data)

    def _normalize_date(self, date_input: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        if not date_input:
            return None

        date_lower = date_input.lower().strip()
        today = datetime.now().date()
        
        # Handle relative dates
        if date_lower == "today":
            target_date = today
        elif date_lower == "tomorrow":
            target_date = today + timedelta(days=1)
        elif date_lower in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            # Handle weekday names
            weekdays = {
                "monday": 0, "tuesday": 1, "wednesday": 2,
                "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
            }
            
            # Check if Sunday
            if date_lower == "sunday":
                raise ValueError("Sorry, we're closed on Sundays. Please choose Monday through Saturday.")
            
            days_ahead = weekdays[date_lower] - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
        else:
            # Try parsing as YYYY-MM-DD
            try:
                target_date = datetime.strptime(date_input, "%Y-%m-%d").date()
                if target_date < today:
                    raise ValueError("Please choose a future date.")
            except ValueError:
                raise ValueError("Please enter a valid date (like 'tomorrow', 'Friday'').")
        
        # Check if the target date is a Sunday
        if target_date.weekday() == 6:  # Sunday
            raise ValueError("Sorry, we're closed on Sundays. Please choose Monday through Saturday.")
            
        return target_date.isoformat()

    def _check_working_hours(self, date_str: str, time_str: str) -> bool:
        """Check if the appointment time is within working hours"""
        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time_str, "%H:%M").time()
            
            # Get day of week (0=Monday, 6=Sunday)
            day_of_week = appointment_date.weekday()
            
            # Working hours
            if day_of_week == 6:  # Sunday
                raise ValueError("Sorry, we're closed on Sundays. Please choose Monday through Saturday.")
            elif day_of_week == 5:  # Saturday
                # Saturday appointments: 9:00 AM - 1:30 PM (clinic closes at 2:00 PM)
                start_time = datetime.strptime("09:00", "%H:%M").time()
                end_time = datetime.strptime("13:30", "%H:%M").time()
                if not (start_time <= appointment_time <= end_time):
                    raise ValueError("Saturday appointments are available from 9:00 AM to 1:30 PM. Please choose a time within these hours.")
            else:  # Monday-Friday
                # Weekday appointments: 8:00 AM - 5:30 PM (clinic closes at 6:00 PM)
                start_time = datetime.strptime("08:00", "%H:%M").time()
                end_time = datetime.strptime("17:30", "%H:%M").time()
                if not (start_time <= appointment_time <= end_time):
                    raise ValueError("Weekday appointments are available from 8:00 AM to 5:30 PM. Please choose a time within these hours.")
            
            return True
            
        except ValueError:
            raise  # Re-raise ValueError for working hours violations
        except Exception as e:
            raise ValueError(f"Error checking working hours: {str(e)}")

    def _normalize_time(self, time_input: str, date_str: str = None) -> str:
        """Normalize time to HH:MM format and validate working hours"""
        if not time_input:
            return None

        time_input = time_input.strip().lower()
        
        try:
            # Pattern 1: "3 PM", "3PM", "3 am", "3am", "8:am", "8:pm", "3", "8" 
            match = re.match(r'^(\d{1,2}):?\s*(pm|am)?$', time_input)
            if match:
                hours = int(match.group(1))
                period = match.group(2) or "am"  # Default to AM if not specified
                
                if period == "pm" and hours != 12:
                    hours += 12
                elif period == "am" and hours == 12:
                    hours = 0
                
                if not (0 <= hours <= 23):
                    raise ValueError("Please enter a valid hour (like 8 AM, 2 PM, or 14:00).")
                
                normalized_time = f"{hours:02d}:00"
                
                # Check working hours if date is provided
                if date_str:
                    self._check_working_hours(date_str, normalized_time)
                
                return normalized_time
            
            # Pattern 2: "3:30 PM", "3:30PM"
            match = re.match(r'^(\d{1,2}):(\d{2})\s*(pm|am)?$', time_input)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                period = match.group(3) or "am"
                
                if period == "pm" and hours != 12:
                    hours += 12
                elif period == "am" and hours == 12:
                    hours = 0
                
                if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
                    raise ValueError("Please enter a valid time (like 2:30 PM or 14:30).")
                
                normalized_time = f"{hours:02d}:{minutes:02d}"
                
                # Check working hours if date is provided
                if date_str:
                    self._check_working_hours(date_str, normalized_time)
                
                return normalized_time
            
            # Pattern 3: "14:30", "16:00"
            match = re.match(r'^(\d{1,2}):(\d{2})$', time_input)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                
                if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
                    raise ValueError("Please enter a valid time (like 2:30 PM or 14:30).")
                
                normalized_time = f"{hours:02d}:{minutes:02d}"
                
                # Check working hours if date is provided
                if date_str:
                    self._check_working_hours(date_str, normalized_time)
                
                return normalized_time
            
            raise ValueError("Please enter a valid time format (like 2 PM, 14:00, or 2:30 PM).")
            
        except ValueError:
            raise  # Re-raise ValueError with user-friendly message
        except Exception as e:
            raise ValueError("Please enter a valid time format (like 2 PM, 14:00, or 2:30 PM).")

    def modify_appointment(self, appointment_id: int, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing appointment"""
        try:
            # Get the appointment from database
            query = """
                SELECT a.*, d.name as doctor_name 
                FROM appointments a 
                LEFT JOIN doctors d ON a.doctor_id = d.id 
                WHERE a.id = %s AND a.user_id = %s
            """
            results = db_manager.execute_query(query, (appointment_id, self._get_user_id()))
            
            if not results:
                return {
                    "success": False,
                    "message": "Appointment not found or you don't have permission to modify it."
                }
            
            appointment = results[0]
            update_fields = []
            update_params = []
            
            # Handle date modification
            if "date" in modifications:
                try:
                    new_date = self._normalize_date(modifications["date"])
                    # Get existing time or new time if it was also modified
                    if "time" in modifications:
                        target_time = self._normalize_time(modifications["time"], new_date)
                    else:
                        existing_time = appointment["appointment_date"].strftime("%H:%M") if appointment["appointment_date"] else "09:00"
                        # Validate existing time with new date
                        self._check_working_hours(new_date, existing_time)
                        target_time = existing_time
                    
                    new_datetime = f"{new_date} {target_time}"
                    update_fields.append("appointment_date = %s")
                    update_params.append(new_datetime)
                except ValueError as e:
                    return {"success": False, "message": f"Invalid date: {str(e)}"}
            
            # Handle time modification
            if "time" in modifications:
                try:
                    # Get the existing date or use the new date if it was also modified
                    if "date" in modifications:
                        target_date = self._normalize_date(modifications["date"])
                    else:
                        target_date = appointment["appointment_date"].strftime("%Y-%m-%d") if appointment["appointment_date"] else self._normalize_date("tomorrow")
                    
                    new_time = self._normalize_time(modifications["time"], target_date)
                    new_datetime = f"{target_date} {new_time}"
                    update_fields.append("appointment_date = %s")
                    update_params.append(new_datetime)
                except ValueError as e:
                    return {"success": False, "message": f"Invalid time: {str(e)}"}
            
            # Handle doctor modification
            if "doctor_name" in modifications:
                try:
                    normalized_doctor = self._normalize_doctor_name(modifications["doctor_name"])
                    doctor_id = self._get_doctor_id(normalized_doctor)
                    update_fields.append("doctor_id = %s")
                    update_params.append(doctor_id)
                except ValueError as e:
                    return {"success": False, "message": f"Invalid doctor: {str(e)}"}
            
            # Handle reason modification
            if "reason" in modifications:
                normalized_reason = self._normalize_reason(modifications["reason"])
                update_fields.append("reason = %s")
                update_params.append(normalized_reason)
            
            if not update_fields:
                return {"success": False, "message": "No valid modifications provided."}
            
            # Update the appointment
            update_query = f"""
                UPDATE appointments 
                SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """
            update_params.extend([appointment_id, self._get_user_id()])
            
            db_manager.execute_query(update_query, update_params, fetch=False)
            
            # Get the updated appointment
            updated_results = db_manager.execute_query(query, (appointment_id, self._get_user_id()))
            updated_appointment = updated_results[0]
            
            # Format response message
            date_str = updated_appointment["appointment_date"].strftime("%Y-%m-%d") if updated_appointment["appointment_date"] else "Unknown date"
            time_str = updated_appointment["appointment_date"].strftime("%H:%M") if updated_appointment["appointment_date"] else "Unknown time"
            doctor_name = updated_appointment["doctor_name"] if updated_appointment["doctor_name"] else "Unknown doctor"
            
            # Remove "Dr." if it's already in the doctor name
            if doctor_name.startswith("Dr. "):
                display_doctor = doctor_name
            else:
                display_doctor = f"Dr. {doctor_name}"
            
            return {
                "success": True,
                "message": f"✅ Appointment updated successfully!\n📅 {date_str} at {time_str}\n👨‍⚕️ {display_doctor}\n📝 Reason: {updated_appointment['reason']}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error modifying appointment: {str(e)}"
            }

    def get_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """Get appointment by ID"""
        return self.appointments.get(appointment_id)

    def list_appointments(self) -> List[Dict[str, Any]]:
        """List all appointments"""
        return list(self.appointments.values()) 