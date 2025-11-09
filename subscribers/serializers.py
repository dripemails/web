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
 
        # Check if subscriber already exists
        email = validated_data.get('email')
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults=validated_data
        )
 
        if not created:
            updated_fields = []
            for attr in ['first_name', 'last_name', 'is_active', 'confirmed']:
                value = validated_data.get(attr)
                if value is not None and getattr(subscriber, attr) != value:
                    setattr(subscriber, attr, value)
                    updated_fields.append(attr)

            if updated_fields:
                subscriber.save(update_fields=updated_fields)

        # Link subscriber to the list if provided
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