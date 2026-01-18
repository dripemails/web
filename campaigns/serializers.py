from rest_framework import serializers
from .models import Campaign, Email, EmailEvent
from subscribers.models import List

class EmailSerializer(serializers.ModelSerializer):
    footer_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Email
        fields = ['id', 'subject', 'body_html', 'body_text', 'wait_time', 'wait_unit', 'order', 'footer', 'footer_id']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        footer_id = validated_data.pop('footer_id', None)
        if footer_id and footer_id.strip():
            from analytics.models import EmailFooter
            try:
                footer = EmailFooter.objects.get(id=footer_id, user=self.context['request'].user)
                validated_data['footer'] = footer
            except EmailFooter.DoesNotExist:
                pass
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        footer_id = validated_data.pop('footer_id', None)
        if footer_id and footer_id.strip():
            from analytics.models import EmailFooter
            try:
                footer = EmailFooter.objects.get(id=footer_id, user=self.context['request'].user)
                validated_data['footer'] = footer
            except EmailFooter.DoesNotExist:
                validated_data['footer'] = None
        else:
            validated_data['footer'] = None
            
        return super().update(instance, validated_data)
        
    def validate_order(self, value):
        """Ensure order starts from 0."""
        if value < 0:
            raise serializers.ValidationError("Order must be a non-negative integer.")
        return value
    
    def validate_wait_time(self, value):
        """Ensure wait_time is non-negative (0 is allowed for immediate sending)."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Wait time must be a non-negative integer (0 = send immediately).")
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