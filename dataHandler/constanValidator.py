class ConstantValidator:

    def is_field_integer(self, data, field_path):
        """ItegerField"""
        self.__val_type = 'должно быть числом'
        current_data = self._get_nested_field(data, field_path)
        if not isinstance(current_data, int):
            return "должно быть числом"
        return None

    def is_field_null(self, data, field_path):
        """NullField"""
        self.__val_type = "Пустое"
        current_data = self._get_nested_field(data, field_path)
        if current_data == "":
            return "Пустое"
        return None

    def is_field_present(self, data, field_path):
        """NullField"""
        self.__val_type = "не представлено"
        if self._get_nested_field(data, field_path) is None:
            return "не представлено"

    def _get_nested_field(self, data, field_path):
        fields = field_path.split('.')
        current_data = data
        for field in fields:
            if field not in current_data:
                return None
            current_data = current_data[field]
        return current_data

    @staticmethod
    def validate_constants(data, required_fields, error_pre_field, validation_functions):
        list_errors = []
        for field in required_fields:
            for validation_function in validation_functions:
                a = validation_function(data, field)
                if validation_function(data, field):
                    missing_field = f"{error_pre_field}{field}"
                    missing_error = {
                        "error": validation_function.__doc__,
                        "field": missing_field,
                        "description": f"Поле {missing_field} не прошло валидацию: {validation_function(data, field)}."
                    }

                    list_errors.append(missing_error)
        return list_errors