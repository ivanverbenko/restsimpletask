import re

from rest_framework import serializers

class DataSerializer(serializers.Serializer):
    name = serializers.CharField()
    message_template = serializers.CharField()
    type = serializers.CharField()
    scopes = serializers.ListField(child=serializers.DictField())

    def validate(self, attrs):
        message_template = attrs['message_template']
        pattern = r'\[([^\]]+)\]'
        variable_list = re.findall(pattern, message_template)
        variable_dict = self.process_data(variable_list)
        for scope in attrs['scopes']:
            if (result := self.find_key_difference(variable_dict, scope)) and result is not None:
                raise serializers.ValidationError([f"Scope: {scope}",f"Error: Отсутствуют ключи {','.join(result)}"])

        self.check_empty_values(attrs)
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

    def check_empty_values(self, attrs):
        for key, value in attrs.items():
            if isinstance(value, str) and not value.strip():
                raise serializers.ValidationError(
                    f"Значение для поля '{key}' не может быть пустым или состоять только из пробелов.")
            elif isinstance(value, list):
                for item in value:
                    self.check_empty_values(item)
            elif isinstance(value, dict):
                self.check_empty_values(value)

    def validate_type(self, value):
        """
        Проверка, что поле Type содержит только "WhatsApp" или "email".
        """
        valid_types = ["WhatsApp", "email"]
        if value not in valid_types:
            raise serializers.ValidationError(f"Поле Type может принимать только значения: {', '.join(valid_types)}.")
        return value

