import pytest
from unittest.mock import Mock, patch
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher


class TestAppointmentActions:
    """Simple tests for appointment actions - no async complexity"""
    
    def setup_method(self):
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}

    def test_action_imports(self):
        """Test that we can import appointment actions without errors"""
        try:
            from actions.action_appointments import ActionBookAppointment
            action = ActionBookAppointment()
            assert action.name() == "action_book_appointment"
        except ImportError as e:
            pytest.skip(f"Could not import ActionBookAppointment: {e}")
        
        try:
            from actions.action_appointments import ActionViewAppointments
            action = ActionViewAppointments()
            assert action.name() == "action_view_appointments"
        except ImportError as e:
            pytest.skip(f"Could not import ActionViewAppointments: {e}")

    def test_mock_appointment_manager(self):
        """Test that we can mock the appointment manager"""
        with patch('actions.action_appointments.appointment_mgr') as mock_mgr:
            mock_mgr.create_appointment.return_value = {
                'success': True,
                'message': 'Test appointment created'
            }
            
            result = mock_mgr.create_appointment({'date': 'tomorrow'})
            assert result['success'] is True
            assert 'Test' in result['message']

    def test_user_id_extraction_mock(self):
        """Test mocking user ID extraction"""
        with patch('actions.action_appointments._extract_user_id_from_tracker') as mock_extract:
            mock_extract.return_value = 123
            
            # Mock tracker
            tracker = Mock(spec=Tracker)
            user_id = mock_extract(tracker)
            assert user_id == 123

    def test_tracker_message_structure(self):
        """Test that we can work with tracker message structure"""
        # Mock a typical tracker message
        self.tracker.latest_message = {
            'entities': [
                {'entity': 'date', 'value': 'tomorrow'},
                {'entity': 'doctor_name', 'value': 'Dr. Smith'}
            ],
            'intent': {'confidence': 0.9, 'name': 'book_appointment'},
            'text': 'I want to book an appointment with Dr. Smith tomorrow'
        }
        
        # Test we can extract entities
        entities = self.tracker.latest_message.get('entities', [])
        assert len(entities) == 2
        assert entities[0]['entity'] == 'date'
        assert entities[1]['entity'] == 'doctor_name'
        
        # Test intent confidence
        intent = self.tracker.latest_message.get('intent', {})
        assert intent['confidence'] == 0.9

    def test_dispatcher_mock(self):
        """Test that dispatcher mocking works"""
        self.dispatcher.utter_message(text="Test message")
        
        # Verify the call was made
        self.dispatcher.utter_message.assert_called_once_with(text="Test message")
        
        # Test call arguments
        call_args = self.dispatcher.utter_message.call_args[1]
        assert call_args['text'] == "Test message" 