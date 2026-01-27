from rest_framework import serializers
from .models import List, Subscriber, CustomField, CustomValue

class ListSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.ReadOnlyField()
    active_subscribers_count = serializers.ReadOnlyField()
    
    class Meta:
        model = List
        fields = ['id', 'name', 'description', 'slug', 'created_at', 
                 'updated_at', 'subscribers_count', 'active_subscribers_count']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        """Create list and associate with the current user."""
        user = self.context['request'].user
        # Remove user from validated_data if it exists to avoid duplicate keyword argument
        validated_data.pop('user', None)
        list_obj = List.objects.create(user=user, **validated_data)
        return list_obj


class CustomValueSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source='field.name', read_only=True)
    
    class Meta:
        model = CustomValue
        fields = ['id', 'field', 'field_name', 'value']
        read_only_fields = ['id']


class SubscriberSerializer(serializers.ModelSerializer):
    custom_values = CustomValueSerializer(many=True, required=False)
    lists = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=List.objects.none(),  # Will be set in __init__
        required=False,
        allow_empty=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter lists queryset by user if request is available
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['lists'].queryset = List.objects.filter(user=request.user)
        else:
            self.fields['lists'].queryset = List.objects.all()
    
    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'uuid', 'first_name', 'last_name', 
                 'is_active', 'confirmed', 'created_at', 'updated_at', 
                 'custom_values', 'lists']
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        """Create subscriber and associate with the list(s)."""
        custom_values_data = validated_data.pop('custom_values', None)
        lists_data = validated_data.pop('lists', [])
        
        # Get the list from context (for backward compatibility)
        list_obj = self.context.get('list_obj')
        if list_obj is None:
            list_id = self.context.get('list_id')
            if list_id:
                request = self.context.get('request')
                list_queryset = List.objects.all()
                if request and getattr(request, 'user', None):
                    list_queryset = list_queryset.filter(user=request.user)
                try:
                    list_obj = list_queryset.get(id=list_id)
                except List.DoesNotExist:
                    raise serializers.ValidationError("List does not exist")
        
        # Validate that all lists in lists_data belong to the user
        request = self.context.get('request')
        if lists_data and request and getattr(request, 'user', None):
            user_lists = List.objects.filter(user=request.user)
            for list_item in lists_data:
                if list_item not in user_lists:
                    raise serializers.ValidationError(
                        f"List '{list_item.name}' does not belong to you or does not exist."
                    )
 
        # Ensure is_active has a default value if not provided
        if 'is_active' not in validated_data:
            validated_data['is_active'] = True
        
        # Check if subscriber already exists
        email = validated_data.get('email')
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults=validated_data
        )

        if not created:
            # Update fields if subscriber already exists
            updated_fields = []
            for attr in ['first_name', 'last_name', 'is_active', 'confirmed']:
                if attr in validated_data:
                    value = validated_data[attr]
                    # Get current value directly from the model instance
                    current_value = getattr(subscriber, attr)
                    # Only update if the value has changed
                    if current_value != value:
                        setattr(subscriber, attr, value)
                        updated_fields.append(attr)

            if updated_fields:
                subscriber.save(update_fields=updated_fields)

        # Link subscriber to the lists
        # First, add lists from the lists_data (if provided in request)
        if lists_data:
            for list_item in lists_data:
                if list_item not in subscriber.lists.all():
                    subscriber.lists.add(list_item)
        
        # Also add list from context (for backward compatibility)
        if list_obj and list_obj not in subscriber.lists.all():
            subscriber.lists.add(list_obj)
 
        # Create custom values if provided
        if custom_values_data:
            for value_data in custom_values_data:
                field = value_data.get('field')
                value = value_data.get('value')
                
                # Update or create custom value
                CustomValue.objects.update_or_create(
                    field=field, 
                    subscriber=subscriber,
                    defaults={'value': value}
                )
        
        return subscriber
    
    def update(self, instance, validated_data):
        """Update subscriber and handle lists."""
        custom_values_data = validated_data.pop('custom_values', None)
        lists_data = validated_data.pop('lists', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update lists if provided
        if lists_data is not None:
            # Filter lists to only include those belonging to the user
            request = self.context.get('request')
            if request and getattr(request, 'user', None):
                user_lists = List.objects.filter(user=request.user)
                valid_list_ids = [l.id for l in lists_data if l in user_lists]
                instance.lists.set(valid_list_ids)
            else:
                instance.lists.set(lists_data)
        
        # Update custom values if provided
        if custom_values_data is not None:
            # Delete existing custom values
            instance.custom_values.all().delete()
            # Create new custom values
            for value_data in custom_values_data:
                field = value_data.get('field')
                value = value_data.get('value')
                CustomValue.objects.create(
                    field=field,
                    subscriber=instance,
                    value=value
                )
        
        return instance


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = ['id', 'name', 'key']
        read_only_fields = ['id', 'key']
        
    def create(self, validated_data):
        """Create custom field and associate with the current user."""
        user = self.context['request'].user
        custom_field = CustomField.objects.create(user=user, **validated_data)
        return custom_field