from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import csv
import io

from .models import List, Subscriber, CustomField, CustomValue
from .serializers import ListSerializer, SubscriberSerializer, CustomFieldSerializer

class ListListCreateAPIView(generics.ListCreateAPIView):
    """List and create subscriber lists."""
    serializer_class = ListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only lists belonging to the current user."""
        return List.objects.filter(user=self.request.user).order_by('-created_at')


class ListRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete a subscriber list."""
    serializer_class = ListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only lists belonging to the current user."""
        return List.objects.filter(user=self.request.user)


class SubscriberListCreateAPIView(generics.ListCreateAPIView):
    """List and create subscribers for a list."""
    serializer_class = SubscriberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only subscribers in the specified list."""
        list_id = self.kwargs.get('list_id')
        list_obj = get_object_or_404(List, id=list_id, user=self.request.user)
        return list_obj.subscribers.all().order_by('-created_at')
    
    def get_serializer_context(self):
        """Add list_id to serializer context."""
        context = super().get_serializer_context()
        context['list_id'] = self.kwargs.get('list_id')
        return context


class SubscriberRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete a subscriber."""
    serializer_class = SubscriberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only subscribers in lists belonging to the current user."""
        return Subscriber.objects.filter(lists__user=self.request.user).distinct()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_subscribers(request):
    """
    Import subscribers from CSV file.
    CSV format should have first row as headers.
    """
    list_id = request.data.get('list_id')
    if not list_id:
        return Response({"error": "List ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        list_obj = List.objects.get(id=list_id, user=request.user)
    except List.DoesNotExist:
        return Response({"error": "List does not exist"}, status=status.HTTP_404_NOT_FOUND)
    
    csv_file = request.FILES.get('file')
    if not csv_file:
        return Response({"error": "CSV file is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV file
        csv_content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Get headers
        headers = csv_reader.fieldnames
        if not headers or 'email' not in headers:
            return Response({"error": "CSV file must contain email column"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create custom fields if they don't exist
        custom_fields = {}
        for header in headers:
            if header not in ['email', 'first_name', 'last_name']:
                # Create or get custom field
                field, created = CustomField.objects.get_or_create(
                    user=request.user,
                    key=header.lower().replace(' ', '_'),
                    defaults={'name': header}
                )
                custom_fields[header] = field
        
        # Import subscribers
        imported = 0
        for row in csv_reader:
            email = row.get('email')
            if not email:
                continue
            
            # Create or update subscriber
            subscriber, created = Subscriber.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                    'is_active': True
                }
            )
            
            # Add to list if not already in it
            if list_obj not in subscriber.lists.all():
                subscriber.lists.add(list_obj)
            
            # Add custom fields
            for header, field in custom_fields.items():
                if header in row and row[header]:
                    CustomValue.objects.update_or_create(
                        subscriber=subscriber,
                        field=field,
                        defaults={'value': row[header]}
                    )
            
            imported += 1
        
        return Response(
            {"message": f"Successfully imported {imported} subscribers"},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_subscribers(request, list_id):
    """Export subscribers from a list to CSV."""
    try:
        list_obj = List.objects.get(id=list_id, user=request.user)
    except List.DoesNotExist:
        return Response({"error": "List does not exist"}, status=status.HTTP_404_NOT_FOUND)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{list_obj.name}_subscribers.csv"'
    
    # Get all custom fields for this user
    custom_fields = CustomField.objects.filter(user=request.user)
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write headers
    headers = ['email', 'first_name', 'last_name', 'is_active', 'confirmed', 'created_at']
    for field in custom_fields:
        headers.append(field.name)
    writer.writerow(headers)
    
    # Write subscriber data
    for subscriber in list_obj.subscribers.all():
        row = [
            subscriber.email,
            subscriber.first_name,
            subscriber.last_name,
            subscriber.is_active,
            subscriber.confirmed,
            subscriber.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        # Add custom field values
        for field in custom_fields:
            try:
                custom_value = CustomValue.objects.get(subscriber=subscriber, field=field)
                row.append(custom_value.value)
            except CustomValue.DoesNotExist:
                row.append('')
        
        writer.writerow(row)
    
    return response


@api_view(['GET', 'POST'])
def unsubscribe(request, subscriber_uuid):
    """Unsubscribe a subscriber from all lists."""
    subscriber = get_object_or_404(Subscriber, uuid=subscriber_uuid)
    
    # Handle both GET (show confirmation) and POST (confirm unsubscribe)
    if request.method == 'POST':
        subscriber.is_active = False
        subscriber.save()
        return JsonResponse({
            "message": "You have been unsubscribed successfully."
        })
    
    # For GET requests, just return success to indicate UUID is valid
    return JsonResponse({
        "email": subscriber.email,
        "valid": True
    })


@api_view(['GET', 'POST'])
def confirm_subscription(request, subscriber_uuid):
    """Confirm a subscriber's subscription."""
    subscriber = get_object_or_404(Subscriber, uuid=subscriber_uuid)
    
    # Handle both GET (show confirmation) and POST (confirm subscription)
    if request.method == 'POST':
        subscriber.confirmed = True
        subscriber.confirmed_at = timezone.now()
        subscriber.save()
        return JsonResponse({
            "message": "Your subscription has been confirmed. Thank you!"
        })
    
    # For GET requests, just return success to indicate UUID is valid
    return JsonResponse({
        "email": subscriber.email,
        "valid": True
    })