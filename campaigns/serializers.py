from rest_framework import serializers
from .models import Campaign, Email, EmailEvent
from subscribers.models import List

class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ['id', 'subject', 'body_html', 'body_text', 'wait_time', 'wait_unit', 'order']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate_order(self, value):
        """Ensure order starts from 0."""
        if value < 0:
            raise serializers.ValidationError("Order must be a non-negative integer.")
        return value


class CampaignSerializer(serializers.ModelSerializer):
    emails = EmailSerializer(many=True, read_only=True)
    emails_count = serializers.ReadOnlyField()
    open_rate = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()
    subscriber_list = serializers.PrimaryKeyRelatedField(
        queryset=List.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Campaign
        fields = ['id', 'name', 'description', 'slug', 'subscriber_list', 
                 'is_active', 'created_at', 'updated_at', 'emails', 
                 'emails_count', 'sent_count', 'open_count', 'click_count',
                 'open_rate', 'click_rate']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 
                          'sent_count', 'open_count', 'click_count']
        
    def create(self, validated_data):
        user = self.context['request'].user
        return Campaign.objects.create(user=user, **validated_data)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EmailEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailEvent
        fields = ['id', 'email', 'subscriber_email', 'event_type', 
                 'link_clicked', 'user_agent', 'ip_address', 'created_at']
        read_only_fields = ['id', 'created_at']