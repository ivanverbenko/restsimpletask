import re

from rest_framework import serializers

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



