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
    
    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'uuid', 'first_name', 'last_name', 
                 'is_active', 'confirmed', 'created_at', 'updated_at', 
                 'custom_values']
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        """Create subscriber and associate with the list."""
        custom_values_data = validated_data.pop('custom_values', None)
        
        # Get the list from context
        list_id = self.context.get('list_id')
        if not list_id:
            raise serializers.ValidationError("List ID is required")
        
        try:
            list_obj = List.objects.get(id=list_id)
        except List.DoesNotExist:
            raise serializers.ValidationError("List does not exist")
        
        # Check if subscriber already exists
        email = validated_data.get('email')
        try:
            subscriber = Subscriber.objects.get(email=email)
            # Add to this list if not already in it
            if list_obj not in subscriber.lists.all():
                subscriber.lists.add(list_obj)
        except Subscriber.DoesNotExist:
            # Create new subscriber
            subscriber = Subscriber.objects.create(**validated_data)
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