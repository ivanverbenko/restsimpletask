import re

from django.db.models import Q
from jinja2 import Template
from rest_framework import serializers

from firsttask.models import Dispatch


class DataSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=False)
    message_template = serializers.CharField(allow_null=False)
    type = serializers.CharField()
    scopes = serializers.ListField(child=serializers.DictField())
    broker = serializers.DictField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validation_errors = []

    def validate_type(self, value):
        """
        Проверка, что поле Type содержит только "WhatsApp" или "email".
        """
        valid_types = ["WhatsApp", "email"]
        if value not in valid_types:
            raise serializers.ValidationError(f"Поле Type может принимать только значения: {', '.join(valid_types)}.")
        return value

    def validate_broker(self,value):
        self.validate_constants(value, ['id',],'broker.', \
                                        validation_functions=[self.is_field_null, self.is_field_integer])
        self.validate_constants(value, ['id', ], 'broker.', \
                                validation_functions=[self.is_field_null, self.is_field_integer])
        return value

    def validate(self, attrs):
        failed_scopes = []
        successful_scopes = []

        if self.validation_errors:
            raise MissingValidationError(self.validation_errors)
        required_fields = [
            'retail',
            'retail.personid',
            'estate',
            'estate.id',]
        integer_fields = [
            'estate.id',
            'retail.personid',
        ]
        message_template = attrs['message_template']
        pattern = r'\[([^\]]+)\]'
        variable_list = re.findall(pattern, message_template)
        variable_dict = self.process_data(variable_list)
        for scope in attrs['scopes']:
            self.validate_constants(scope,required_fields,'scopes.',\
                                        validation_functions=[self.is_field_null])
            if self.validation_errors:
                scope['errors'] = self.validation_errors
                failed_scopes.append(scope)
                self.validation_errors = []  # Сбрасываем список ошибок для следующего скопа
                continue
            self.validate_constants(scope, integer_fields, 'scopes.', \
                                    validation_functions=[self.is_field_integer])
            if self.validation_errors:
                #scope["errors"]: self.validation_errors}
                scope['errors'] = self.validation_errors
                failed_scopes.append(scope)
                self.validation_errors = []
                continue
            #проверка contacts

            if attrs['type'] == "email":
                self.validate_constants(scope, ['retail.contact.email'],'scopes.', \
                                        validation_functions=[self.is_field_present,self.is_field_null])

            elif attrs['type'] == 'WhatsApp':
                self.validate_constants(scope, ['retail.contact.phone'], 'scopes.',\
                                        validation_functions=[self.is_field_null])

            if (result := self.find_key_difference(variable_dict, scope)) and result is not None:
                for field in result:
                    missing_error = {
                        "error": "Field shoud be present",
                        "field": field,
                        "description": f"Поле {field} не прошло валидацию: не представлено."
                    }
                    self.validation_errors.append(missing_error)
            if self.validation_errors:
                scope['errors'] = self.validation_errors
                failed_scopes.append(scope)
                self.validation_errors = []
                continue
            ##переделать
            scope['errors']=""
            successful_scopes.append(scope)
        attrs['scopes'] = successful_scopes
        attrs['scopes_erros'] = failed_scopes
        return attrs

    def find_key_difference(self,dict1, dict2):
        missing_keys = set()
        for key in dict1.keys():
            if key not in dict2:
                missing_keys.add(key)
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                nested_missing_keys = self.find_key_difference(dict1[key], dict2[key])
                missing_keys.update({f"{key}.{nested_key}" for nested_key in nested_missing_keys})

        return missing_keys

    def process_data(self,variable_list):
        variable_dict = {}
        for variable in variable_list:
            keys = variable.split('.')
            current_dict = variable_dict
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current_dict[key] = True
                else:
                    current_dict = current_dict.setdefault(key, {})
        return variable_dict

    def validate_constants(self, data, required_fields, error_pre_field, validation_functions):
        """В этот метод передаем список функций валидации и поля"""
        for field in required_fields:
            for validation_function in validation_functions:
                if validation_function(data, field):
                    missing_field = f"{error_pre_field}{field}"
                    missing_error = {
                        "error": validation_function.__doc__,
                        "field": missing_field,
                        "description": f"Поле {missing_field} не прошло валидацию: {self.__val_type}."
                    }
                    self.validation_errors.append(missing_error)

    def is_field_present(self, data, field_path):
        """field not present"""
        self.__val_type = "не представлено"
        fields = field_path.split('.')
        current_data = data
        for field in fields:
            if field not in current_data:
                return True
            current_data = current_data[field]
        return False

    def is_field_null(self, data, field_path):
        """field is null"""
        self.__val_type = "Пустое"
        fields = field_path.split('.')
        current_data = data
        for field in fields:
            if field not in current_data:
                return False
            current_data = current_data[field]
            if current_data == "":
                return True
        return current_data is None

    def is_field_integer(self, data, field_path):
        """field not integer"""
        self.__val_type = 'должно быть числом'
        fields = field_path.split('.')
        current_data = data
        for field in fields:
            if field not in current_data:
                return True
            current_data = current_data[field]

        return not(isinstance(current_data, int))

    def create(self, validated_data):
        name = validated_data['name']
        message_template = validated_data['message_template'].replace('[', '{{').replace(']', '}}')
        scopes = validated_data['scopes']
        dispatches_to_create = []
        sent_messages = []  # To track sent messages
        sucsessfull_scopes = []
        failed_scopes = []
        for scope in scopes:
            type = validated_data['type']
            contact = scope['retail']['contact']['email'] if type == "email" \
                else scope['retail']['contact']['phone']

            # Check if the same estate.id and contact have been sent before
            filter_query = Q(estate_id=scope['estate']['id']) & (Q(email=contact) | Q(phone=contact))
            existing_sent_message = Dispatch.objects.filter(filter_query).first()

            if existing_sent_message:
                error_message = f"{type} уже был в рассылке estate: {scope['estate']['id']}"
                scope['errors']=[{
                    'error': error_message,
                    'field': type,
                    'entityId': existing_sent_message.id
                }]
                failed_scopes.append({
                    'scope': scope,
                    'errors': error_message,
                    'entityId': existing_sent_message.id
                })
            else:
                template = Template(message_template)
                formatted_message = template.render(**scope)
                print(scope)
                dispatch_dict = {
                    'name': name,
                    'message': formatted_message,
                    'retail_id': scope['retail']['personid'],
                    'broker_id': validated_data['broker']['id'],
                    'estate_id': scope['estate']['id'],
                    'type': type,
                    'email': contact if type == "email" else None,
                    'phone': contact if type == "WhatsApp" else None
                }
                dispatches_to_create.append(dispatch_dict)
                sucsessfull_scopes.append(scope)
        dispatch_objects_to_create = [Dispatch(**dispatch_dict) for dispatch_dict in dispatches_to_create]
        Dispatch.objects.bulk_create(dispatch_objects_to_create)
        return  dispatch_objects_to_create, sucsessfull_scopes, failed_scopes
class MissingValidationError(serializers.ValidationError):
    """передаем список ошибок"""
    def __init__(self, error_list):
        formatted_errors = []
        for error in error_list:
            formatted_error = {
                "field": error["field"],
                "description": error["description"],
                "error": error["error"]
            }
            if "scopes" in error:
                formatted_error["scopes"] = error["scopes"]
            formatted_errors.append(formatted_error)
        super().__init__(detail={"errors": formatted_errors})



