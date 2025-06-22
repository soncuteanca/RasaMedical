from typing import Dict, Text, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from actions.db_connect import db_manager


class ActionListDoctors(Action):
    def name(self) -> Text:
        return "action_list_doctors"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            query = """
                SELECT name, specialty 
                FROM doctors 
                ORDER BY specialty, name
            """
            results = db_manager.execute_query(query)

            if results:
                response_lines = []
                current_specialty = None
                for doctor in results:
                    if doctor['specialty'] != current_specialty:
                        current_specialty = doctor['specialty']
                        if len(response_lines) > 0:
                            response_lines.append("")
                        response_lines.append(f"{current_specialty}:")
                    response_lines.append(f"• {doctor['name']}")
                response = "\n".join(response_lines).strip()
            else:
                response = "No doctors found in the database."

            dispatcher.utter_message(text=response)

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while fetching doctors: {str(e)}")

        return []


class ActionSelectDoctor(Action):
    def name(self) -> Text:
        return "action_select_doctor"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get doctor name from entity or message text
            doctor_name = None
            entities = tracker.latest_message.get("entities", [])
            
            # Look for doctor_name entity
            for entity in entities:
                if entity["entity"] == "doctor_name":
                    doctor_name = entity["value"]
                    break
            
            # If no entity, try to extract from message text
            if not doctor_name:
                message_text = tracker.latest_message.get("text", "").strip()
                doctor_name = message_text
            
            print(f"DEBUG: Looking for doctor: '{doctor_name}'")
            
            if doctor_name:
                # Try to find the doctor in database
                query = """
                    SELECT name, specialty
                    FROM doctors
                    WHERE name LIKE %s OR name LIKE %s
                    ORDER BY name
                """
                
                # Try both with and without Dr. prefix
                search_patterns = [f"%{doctor_name}%", f"%Dr. {doctor_name}%"]
                results = db_manager.execute_query(query, search_patterns)
                
                if results:
                    doctor = results[0]  # Take the first match
                    response = f"You selected {doctor['name']} from {doctor['specialty']}.\n\nWould you like to book an appointment?"
                    dispatcher.utter_message(text=response)
                    # Set the doctor slot for potential appointment booking
                    return [SlotSet("doctor_name", doctor['name'])]
                else:
                    # Doctor not found, show available doctors
                    dispatcher.utter_message(text=f"I couldn't find a doctor named '{doctor_name}'. Here are our available doctors:")
                    # Fall back to listing all doctors
                    all_doctors_query = "SELECT name, specialty FROM doctors ORDER BY specialty, name"
                    all_results = db_manager.execute_query(all_doctors_query)
                    
                    if all_results:
                        response_lines = []
                        current_specialty = None
                        for doc in all_results:
                            if doc['specialty'] != current_specialty:
                                current_specialty = doc['specialty']
                                if len(response_lines) > 0:
                                    response_lines.append("")
                                response_lines.append(f"{current_specialty}:")
                            response_lines.append(f"• {doc['name']}")
                        response = "\n".join(response_lines)
                        dispatcher.utter_message(text=response)
            else:
                dispatcher.utter_message(text="Please specify which doctor you'd like to see.")
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error: {str(e)}")
        
        return []


class ActionListDoctorsBySpecialty(Action):
    def name(self) -> Text:
        return "action_list_doctors_by_specialty"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get specialty from slot
            specialty = tracker.get_slot("specialty")
            print(f"DEBUG: Extracted specialty slot = '{specialty}'")

            # Create comprehensive mapping (handles both slot values AND message parsing)
            specialty_mapping = {
                # Direct mappings for database values
                'Adult Cardiology': 'Adult Cardiology',
                'Pediatric Cardiology': 'Pediatric Cardiology',
                'Cardiovascular Surgery': 'Cardiovascular Surgery',

                # Single word mappings
                'Adult': 'Adult Cardiology',
                'adult': 'Adult Cardiology',
                'Pediatric': 'Pediatric Cardiology',
                'pediatric': 'Pediatric Cardiology',
                'Cardiovascular': 'Cardiovascular Surgery',
                'cardiovascular': 'Cardiovascular Surgery',
                
                # Surgery mappings (the key fix!)
                'Surgery': 'Cardiovascular Surgery',
                'surgery': 'Cardiovascular Surgery', 
                'Surgeons': 'Cardiovascular Surgery',
                'surgeons': 'Cardiovascular Surgery',
                'Surgeon': 'Cardiovascular Surgery',
                'surgeon': 'Cardiovascular Surgery',

                # Full phrase mappings (the key fix!)
                'adult cardiologist': 'Adult Cardiology',
                'Adult cardiologist': 'Adult Cardiology',
                'Adult Cardiologist': 'Adult Cardiology',
                'adult cardiologists': 'Adult Cardiology',
                'Adult cardiologists': 'Adult Cardiology',
                'Adult Cardiologists': 'Adult Cardiology',

                'pediatric cardiologist': 'Pediatric Cardiology',
                'Pediatric cardiologist': 'Pediatric Cardiology',
                'Pediatric Cardiologist': 'Pediatric Cardiology',
                'pediatric cardiologists': 'Pediatric Cardiology',
                'Pediatric cardiologists': 'Pediatric Cardiology',
                'Pediatric Cardiologists': 'Pediatric Cardiology',

                'cardiovascular surgeon': 'Cardiovascular Surgery',
                'Cardiovascular surgeon': 'Cardiovascular Surgery',
                'Cardiovascular Surgeon': 'Cardiovascular Surgery',
                'cardiovascular surgeons': 'Cardiovascular Surgery',
                'Cardiovascular surgeons': 'Cardiovascular Surgery',
                'Cardiovascular Surgeons': 'Cardiovascular Surgery'
            }

            # First, try to map the extracted specialty
            if specialty and specialty in specialty_mapping:
                mapped_specialty = specialty_mapping[specialty]
                print(f"DEBUG: Mapped '{specialty}' to '{mapped_specialty}'")
                specialty = mapped_specialty

            # If no specialty extracted or not in mapping, try parsing the message
            elif not specialty:
                latest_message = tracker.latest_message.get('text', '').lower()
                print(f"DEBUG: No specialty extracted, checking message: '{latest_message}'")

                # Find matching specialty in message
                for key, value in specialty_mapping.items():
                    if key.lower() in latest_message:
                        specialty = value
                        print(f"DEBUG: Found '{key}' in message, mapped to '{value}'")
                        break

            if not specialty:
                dispatcher.utter_message(
                    text="Please specify which specialty you're interested in: Adult Cardiology, Pediatric Cardiology, or Cardiovascular Surgery.")
                return []

            print(f"DEBUG: Final specialty for database query: '{specialty}'")

            # Query database
            query = """
                SELECT name 
                FROM doctors 
                WHERE specialty = %s 
                ORDER BY name
            """
            results = db_manager.execute_query(query, (specialty,))

            if results:
                response_lines = [f"{specialty} Doctors:"]
                for doctor in results:
                    response_lines.append(f"• {doctor['name']}")
                response = "\n".join(response_lines)
            else:
                response = f"No {specialty} doctors found in the database."

            dispatcher.utter_message(text=response)

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while fetching doctors: {str(e)}")

        return []


class ActionListProcedures(Action):
    def name(self) -> Text:
        return "action_list_procedures"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = """📋 Consultation & Control
• Initial Consultation - comprehensive cardiac evaluation
• Follow-up Visit - monitoring and treatment adjustment
• Control Visit - routine check-up


🩺 Diagnostic Procedures
• ECG/EKG - measures electrical activity of the heart
• Echocardiogram - ultrasound imaging of the heart
• Stress Test - evaluates heart function under stress
• Nuclear Stress Test - advanced stress imaging
• Holter Monitor - continuous heart rhythm monitoring
• Cardiac MRI - detailed heart structure imaging
• CT Coronary Angiogram - non-invasive artery imaging
• Coronary Angiography - detailed artery examination


🛠️ Interventional Procedures
• Coronary Angioplasty (PCI) - opens blocked arteries
• Stent Placement - keeps arteries open
• Pacemaker Implantation - regulates heart rhythm
• ICD Implantation - prevents sudden cardiac arrest
• Catheter Ablation - treats abnormal heart rhythms
• Valve Replacement - repairs or replaces heart valves
• CABG Surgery - creates alternate blood flow path

For additional details you can reach us at:
📞 Phone: +1 (555) 123-4567
📧 Email: info@cardiologyclinic.com"""

        dispatcher.utter_message(text=response)
        return []


class ActionListTests(Action):
    def name(self) -> Text:
        return "action_list_tests"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = """🔬 CARDIAC BLOOD TESTS & ANALYSES

❤️ Heart-Specific Markers
• Troponin I/T - heart muscle injury test
• CK-MB - myocardial infarction marker
• BNP/NT-proBNP - heart failure indicator

🧪 Cholesterol & Lipid Panel
• Total Cholesterol - overall cholesterol levels
• LDL - "bad" cholesterol
• HDL - "good" cholesterol
• Triglycerides - blood fat levels

🩸 Inflammation & Risk Markers
• hs-CRP - inflammation marker
• Homocysteine - vascular damage indicator
• Fibrinogen - clotting factor

🧬 Metabolic Tests
• Glucose - blood sugar levels
• HbA1c - long-term blood sugar control
• Insulin - blood sugar hormone

🧫 Other Tests
• Electrolytes - heart rhythm function
• Thyroid panel - affects heart rate
• Kidney function - medication baseline

For additional details you can reach us at:
📞 Phone: +1 (555) 123-4567
📧 Email: info@cardiologyclinic.com"""

        dispatcher.utter_message(text=response)
        return []


class ActionListPrices(Action):
    def name(self) -> Text:
        return "action_list_prices"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = """💰 CARDIOLOGY PRICING LIST
        
📋 CONSULTATION & CONTROL
• Initial Consultation   →                     150 - 250 RON
• Follow-up Visit    →                           120 - 180 RON
• Control Visit    →                             100 - 150 RON

🩺 DIAGNOSTIC PROCEDURES
• ECG/EKG                  →                     50 - 100 RON
• Echocardiogram            →                  300 - 600 RON
• Stress Test                  →               400 - 700 RON
• Nuclear Stress Test          →               800 - 1.200 RON
• Holter Monitor (24-48h)      →               250 - 450 RON
• Cardiac MRI                 →              1.500 - 2.500 RON
• CT Coronary Angiogram        →               800 - 1.500 RON
• Coronary Angiography         →             3.000 - 6.000 RON

🛠️ INTERVENTIONAL PROCEDURES
• Coronary Angioplasty (PCI)     →           8.000 - 15.000 RON
• Stent Placement      →                    10.000 - 20.000 RON
• Pacemaker Implantation   →                15.000 - 25.000 RON
• ICD Implantation          →               25.000 - 40.000 RON
• Catheter Ablation           →             12.000 - 20.000 RON
• Valve Replacement           →             30.000 - 60.000 RON
• CABG Surgery                →             25.000 - 50.000 RON

🔬 BLOOD TESTS
• Basic Cardiac Panel            →              80 - 150 RON
• Comprehensive Lipid Panel      →              60 - 120 RON
• Troponin Test                  →             40 - 80 RON
• BNP/NT-proBNP                 →              80 - 150 RON
• Complete Metabolic Panel      →               50 - 100 RON

For additional details you can reach us at:
📞 Phone: +1 (555) 123-4567
📧 Email: info@cardiologyclinic.com"""

        dispatcher.utter_message(text=response)
        return []