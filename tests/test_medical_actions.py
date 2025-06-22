import pytest
from unittest.mock import Mock, patch, MagicMock
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.medical_actions import ActionListDoctors, ActionSelectDoctor, ActionListDoctorsBySpecialty


class TestActionListDoctors:
    """Test the ActionListDoctors action"""
    
    def setup_method(self):
        self.action = ActionListDoctors()
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}

    @patch('actions.medical_actions.db_manager')
    def test_list_doctors_success(self, mock_db_manager):
        """Test successful doctor listing"""
        # Mock database response
        mock_db_manager.execute_query.return_value = [
            {'name': 'Dr. Smith', 'specialty': 'Adult Cardiology'},
            {'name': 'Dr. Johnson', 'specialty': 'Adult Cardiology'},
            {'name': 'Dr. Williams', 'specialty': 'Pediatric Cardiology'}
        ]
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        # Verify database was queried
        mock_db_manager.execute_query.assert_called_once()
        
        # Verify response was sent
        self.dispatcher.utter_message.assert_called_once()
        call_args = self.dispatcher.utter_message.call_args[1]
        assert 'Dr. Smith' in call_args['text']
        assert 'Adult Cardiology' in call_args['text']
        
        # Verify return value
        assert result == []

    @patch('actions.medical_actions.db_manager')
    def test_list_doctors_empty_result(self, mock_db_manager):
        """Test when no doctors are found"""
        mock_db_manager.execute_query.return_value = []
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        self.dispatcher.utter_message.assert_called_once_with(
            text="No doctors found in the database."
        )
        assert result == []

    @patch('actions.medical_actions.db_manager')
    def test_list_doctors_database_error(self, mock_db_manager):
        """Test database error handling"""
        mock_db_manager.execute_query.side_effect = Exception("Database connection failed")
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        self.dispatcher.utter_message.assert_called_once()
        call_args = self.dispatcher.utter_message.call_args[1]
        assert 'error' in call_args['text'].lower()
        assert result == []


class TestActionSelectDoctor:
    """Test the ActionSelectDoctor action"""
    
    def setup_method(self):
        self.action = ActionSelectDoctor()
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}

    @patch('actions.medical_actions.db_manager')
    def test_select_doctor_found(self, mock_db_manager):
        """Test successful doctor selection"""
        # Mock tracker message with entity
        self.tracker.latest_message = {
            'entities': [{'entity': 'doctor_name', 'value': 'Dr. Smith'}],
            'text': 'I want to see Dr. Smith'
        }
        
        # Mock database response
        mock_db_manager.execute_query.return_value = [
            {'name': 'Dr. Smith', 'specialty': 'Adult Cardiology'}
        ]
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        # Verify response contains doctor info
        self.dispatcher.utter_message.assert_called_once()
        call_args = self.dispatcher.utter_message.call_args[1]
        assert 'Dr. Smith' in call_args['text']
        assert 'Adult Cardiology' in call_args['text']
        
        # Verify slot is set
        assert len(result) == 1
        assert result[0]['event'] == 'slot'
        assert result[0]['name'] == 'doctor_name'
        assert result[0]['value'] == 'Dr. Smith'

    @patch('actions.medical_actions.db_manager')
    def test_select_doctor_not_found(self, mock_db_manager):
        """Test when doctor is not found"""
        self.tracker.latest_message = {
            'entities': [{'entity': 'doctor_name', 'value': 'Dr. Unknown'}],
            'text': 'I want to see Dr. Unknown'
        }
        
        # Mock database responses
        mock_db_manager.execute_query.side_effect = [
            [],  # First query returns no results
            [{'name': 'Dr. Smith', 'specialty': 'Adult Cardiology'}]  # Second query for all doctors
        ]
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        # Verify two calls to dispatcher (not found message + doctor list)
        assert self.dispatcher.utter_message.call_count == 2
        assert result == []


class TestActionListDoctorsBySpecialty:
    """Test the ActionListDoctorsBySpecialty action"""
    
    def setup_method(self):
        self.action = ActionListDoctorsBySpecialty()
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}

    @patch('actions.medical_actions.db_manager')
    def test_list_doctors_by_specialty_success(self, mock_db_manager):
        """Test successful specialty-based doctor listing"""
        # Mock tracker with specialty slot
        self.tracker.get_slot.return_value = 'Adult Cardiology'
        self.tracker.latest_message = {'text': 'show me adult cardiologists'}
        
        # Mock database response
        mock_db_manager.execute_query.return_value = [
            {'name': 'Dr. Smith'},
            {'name': 'Dr. Johnson'}
        ]
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        # Verify database was queried with correct specialty
        mock_db_manager.execute_query.assert_called_once()
        call_args = mock_db_manager.execute_query.call_args[0]
        assert 'Adult Cardiology' in call_args[1]
        
        # Verify response
        self.dispatcher.utter_message.assert_called_once()
        call_args = self.dispatcher.utter_message.call_args[1]
        assert 'Dr. Smith' in call_args['text']
        assert result == []

    def test_list_doctors_no_specialty_provided(self):
        """Test when no specialty is provided"""
        self.tracker.get_slot.return_value = None
        self.tracker.latest_message = {'text': 'show me doctors'}
        
        result = self.action.run(self.dispatcher, self.tracker, self.domain)
        
        # Verify error message is sent
        self.dispatcher.utter_message.assert_called_once()
        call_args = self.dispatcher.utter_message.call_args[1]
        assert 'specify which specialty' in call_args['text'].lower()
        assert result == []

    @patch('actions.medical_actions.db_manager')
    def test_specialty_mapping(self, mock_db_manager):
        """Test specialty name mapping functionality"""
        # Test various specialty inputs
        test_cases = [
            ('Adult', 'Adult Cardiology'),
            ('Pediatric', 'Pediatric Cardiology'),
            ('Surgery', 'Cardiovascular Surgery'),
            ('adult cardiologist', 'Adult Cardiology')
        ]
        
        for input_specialty, expected_specialty in test_cases:
            self.tracker.get_slot.return_value = input_specialty
            self.tracker.latest_message = {'text': f'show me {input_specialty}'}
            mock_db_manager.execute_query.return_value = [{'name': 'Dr. Test'}]
            
            result = self.action.run(self.dispatcher, self.tracker, self.domain)
            
            # Verify correct specialty was used in query
            call_args = mock_db_manager.execute_query.call_args[0]
            assert expected_specialty in call_args[1] 