import re

from rest_framework import serializers

class DataSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=False)
    message_template = serializers.CharField(allow_null=False)
    type = serializers.CharField()
    scopes = serializers.ListField(child=serializers.DictField())
    broker = serializers.DictField()
    def validate_type(self, value):
        """
        Проверка, что поле Type содержит только "WhatsApp" или "email".
        """
        valid_types = ["WhatsApp", "email"]
        if value not in valid_types:
            raise serializers.ValidationError(f"Поле Type может принимать только значения: {', '.join(valid_types)}.")
        return value

    def validate_broker(self,value):
        self.validate_constants(value, ['id',],'broker.')


    def validate(self, attrs):
        required_fields = [
            'retail',
            'retail.personid',
            'estate',
            'estate.id',]
        message_template = attrs['message_template']
        pattern = r'\[([^\]]+)\]'
        variable_list = re.findall(pattern, message_template)
        variable_dict = self.process_data(variable_list)
        type = attrs['type']
        for scope in attrs['scopes']:
            self.validate_constants(scope,required_fields,'scopes.')
            #проверка contacts
            if attrs['type'] == 'phone':
                self.validate_constants(scope, ['retail.contact.phone'],'scopes.')
            elif attrs['type'] == 'WhatsApp':
                self.validate_constants(scope, ['retail.contact.WhatsApp'], 'scopes.')
            if (result := self.find_key_difference(variable_dict, scope)) and result is not None:
                raise serializers.ValidationError([f"Scope: {scope}",f"Error: Отсутствуют ключи {','.join(result)}"])
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


    def validate_constants(self, data, required_fields, error_pre_field):

        for field in required_fields:
            if not self.is_field_present(data, field):
                error_message = f"Поле {error_pre_field}{field} должно быть представлено."
                raise serializers.ValidationError(error_message)

            if self.is_field_null(data, field):
                error_message = f"Поле {error_pre_field}{field} не может быть нулевым."
                raise serializers.ValidationError(error_message)

    def is_field_present(self, data, field_path):
        #вспомогательный метод
        fields = field_path.split('.')
        current_data = data
        for field in fields:
            if field not in current_data:
                return False
            current_data = current_data[field]
        return True

    def is_field_null(self, data, field_path):
        fields = field_path.split('.')
        current_data = data
        for field in fields:
            if field not in current_data:
                return False
            current_data = current_data[field]
            if current_data == "":
                return True
        return current_data is None


