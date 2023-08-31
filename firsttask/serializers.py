import re

from django.db.models import Q
from jinja2 import Template
from rest_framework import serializers

from firsttask.constanValidator import ConstantValidator
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
        constant_validator = ConstantValidator()
        required_fields = ['id']
        error_pre_field = 'broker.'
        validation_functions = [constant_validator.is_field_null, constant_validator.is_field_integer]

        errors = constant_validator.validate_constants(value, required_fields, error_pre_field, validation_functions)
        if errors:
            raise serializers.ValidationError(errors)
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
        constant_validator = ConstantValidator()
        for scope in attrs['scopes']:
            all_errors = []
            scope['errors'] = ""
            errors = constant_validator.validate_constants(scope, required_fields, 'scopes.',
                                                           validation_functions=[constant_validator.is_field_null])
            if errors:
                scope['errors'] = errors
                failed_scopes.append(scope)
                continue
            errors = constant_validator.validate_constants(scope, integer_fields, 'scopes.',
                                                           validation_functions=[constant_validator.is_field_integer])
            if errors:
                all_errors.append(errors)
            # if errors:
            #     #scope["errors"]: self.validation_errors}
            #     scope['errors'] = errors
            #     failed_scopes.append(scope)
            #     errors = []
            #     continue
            #проверка contacts

            if attrs['type'] == "email":
                errors=[]
                errors = constant_validator.validate_constants(scope, ['retail.contact.email'],'scopes.', \
                                        validation_functions=[constant_validator.is_field_present,constant_validator.is_field_null])
                # if errors:
                #     scope['errors'] = errors
                #     failed_scopes.append(scope)
                #     continue
                if errors:
                    all_errors.append(errors)


            elif attrs['type'] == 'WhatsApp':
                errors = constant_validator.validate_constants(scope, ['retail.contact.phone'], 'scopes.', \
                                                               validation_functions=[
                                                                   constant_validator.is_field_present,
                                                                   constant_validator.is_field_null])
                # if errors:
                #     scope['errors'] = errors
                #     failed_scopes.append(scope)
                #     continue
                if errors:
                    all_errors.append(errors)
            missing_fields_from_msg = self.get_missing_fields_from_templates(message_template,scope)
            # if missing_fields_from_msg:
            #     scope['errors'] = missing_fields_from_msg
            #     failed_scopes.append(scope)
            #     continue
            if missing_fields_from_msg:
                all_errors.append(missing_fields_from_msg)
            if all_errors:
                scope['errors'] = all_errors
                failed_scopes.append(scope)
                continue
            successful_scopes.append(scope)
        attrs['scopes'] = successful_scopes
        attrs['scopes_erros'] = failed_scopes
        return attrs

    def get_missing_fields_from_templates(self, message,scope):
        pattern = r'\[([^\[\]]+)\]'
        matches = re.findall(pattern, message)
        constant_validator = ConstantValidator()
        value = scope
        error_pre_field = 'scopes.'
        required_fields = matches
        validation_functions = [constant_validator.is_field_present]
        errors = constant_validator.validate_constants(value, required_fields, error_pre_field,
                                                       validation_functions)
        return errors


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
                failed_scopes.append({
                    'scope': scope,
                    'errors': error_message,
                    'entityId': existing_sent_message.id
                })
            else:
                template = Template(message_template)
                formatted_message = template.render(**scope)
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
        return  failed_scopes, sucsessfull_scopes


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
        super().__init__(detail={"errors": error_list})



