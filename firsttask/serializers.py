import re

from rest_framework import serializers

class DataSerializer(serializers.Serializer):
    name = serializers.CharField()
    message_template = serializers.CharField()
    scopes = serializers.ListField(child=serializers.DictField())

    def validate(self, attrs):
        message_template = attrs['message_template']
        pattern = r'\[([^\]]+)\]'
        variable_list = re.findall(pattern, message_template)
        variable_dict = {}
        try:
            for variable in variable_list:
                key, value = variable.split('.') if '.' in variable else (variable, None)
                variable_dict.setdefault(key, {})[value] = True
        except:
            raise serializers.ValidationError(f"Неверный формат scopes")

        for scope in attrs['scopes']:
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


