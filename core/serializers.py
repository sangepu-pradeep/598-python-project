from rest_framework import serializers  # Importing necessary module

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
        A ModelSerializer that takes an additional `fields` argument that
        controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)  # Extracting 'fields' argument
        excludes = kwargs.pop('excludes', None)  # Extracting 'excludes' argument

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        # Check if both 'fields' and 'excludes' are provided simultaneously
        if fields and excludes:
            raise ValueError("Can not pass fields and excludes parameters at the same time")

        if fields is not None:
            # Remove fields not specified in the `fields` argument
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if excludes is not None:
            # Remove fields specified in the `excludes` argument
            set_excludes = set(excludes)
            for field_name in set_excludes:
                self.fields.pop(field_name)

