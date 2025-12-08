from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db.models import Q, Value, CharField
from django.db.models.functions import Coalesce, Concat, Trim
from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import List, Subscriber, CustomField, CustomValue
from .serializers import ListSerializer, SubscriberSerializer
from campaigns.models import Campaign
import csv
import json
from openpyxl import load_workbook
from datetime import datetime

@login_required
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_list_create(request):
    """List all subscriber lists or create a new one."""
    if request.method == 'GET':
        lists = List.objects.filter(user=request.user)
        serializer = ListSerializer(lists, many=True)
        return Response(serializer.data)
    
    serializer = ListSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        list_obj = serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@login_required
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def list_detail(request, pk):
    """Retrieve, update or delete a subscriber list."""
    list_obj = get_object_or_404(List, id=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = ListSerializer(list_obj)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ListSerializer(list_obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        list_obj.delete()
        return Response(status=204)

@login_required
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def subscriber_list_create(request):
    """List all subscribers or create a new one."""
    if request.method == 'GET':
        list_id = request.query_params.get('list_id')
        if list_id:
            list_obj = get_object_or_404(List, id=list_id, user=request.user)
            subscribers = list_obj.subscribers.all()
        else:
            subscribers = Subscriber.objects.filter(lists__user=request.user).distinct()
        
        serializer = SubscriberSerializer(subscribers, many=True)
        return Response(serializer.data)
    
    list_id = request.data.get('list_id') or None
    list_obj = None

    if list_id:
        try:
            list_obj = List.objects.get(id=list_id, user=request.user)
        except List.DoesNotExist:
            return Response({'list_id': _('Selected list does not exist.')}, status=404)
 
    serializer = SubscriberSerializer(
        data=request.data,
        context={'request': request, 'list_obj': list_obj, 'list_id': list_id}
    )
    if serializer.is_valid():
        try:
            subscriber = serializer.save()
            # Update the serializer instance with the saved object to get the response data
            serializer.instance = subscriber
            return Response(serializer.data, status=201)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return Response({
                'error': str(e),
                'traceback': error_trace if settings.DEBUG else None
            }, status=500)
    return Response(serializer.errors, status=400)

@login_required
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def subscriber_detail(request, pk):
    """Retrieve, update or delete a subscriber."""
    subscriber = get_object_or_404(Subscriber, id=pk, lists__user=request.user)
    
    if request.method == 'GET':
        serializer = SubscriberSerializer(subscriber)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = SubscriberSerializer(subscriber, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        subscriber.delete()
        return Response(status=204)

@login_required
def import_subscribers(request):
    """Render subscriber import page."""
    campaigns = Campaign.objects.filter(user=request.user)
    lists = List.objects.filter(user=request.user)
    context = {
        'campaigns': campaigns,
        'lists': lists
    }
    return render(request, 'subscribers/import.html', context)

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_import(request):
    """Process the uploaded file and import subscribers."""
    file = request.FILES.get('file')
    list_id = request.data.get('list_id')
    campaign_id = request.data.get('campaign_id')
    mappings = json.loads(request.data.get('mappings', '{}'))
    
    if not file or not list_id:
        return Response({
            'error': _('Please provide both a file and select a list')
        }, status=400)
    
    try:
        # Read file based on extension
        if file.name.endswith('.csv'):
            # Read CSV file
            file.seek(0)  # Reset file pointer
            decoded_file = file.read().decode('utf-8-sig')  # Handle BOM
            reader = csv.DictReader(decoded_file.splitlines())
            rows = list(reader)
            columns = reader.fieldnames or []
        elif file.name.endswith(('.xls', '.xlsx')):
            # Read Excel file
            workbook = load_workbook(filename=file, read_only=True, data_only=True)
            worksheet = workbook.active
            rows = []
            columns = None
            for idx, row in enumerate(worksheet.iter_rows(values_only=True)):
                if idx == 0:
                    # First row is headers
                    columns = [str(cell) if cell else f'Column_{i+1}' for i, cell in enumerate(row)]
                else:
                    # Convert row to dict
                    row_dict = {}
                    for i, cell in enumerate(row):
                        if i < len(columns):
                            row_dict[columns[i]] = cell
                    rows.append(row_dict)
            workbook.close()
        else:
            return Response({
                'error': _('Unsupported file format')
            }, status=400)
        
        subscriber_list = List.objects.get(id=list_id, user=request.user)
        campaign = None
        if campaign_id:
            campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        
        imported_count = 0
        skipped_count = 0
        
        # Process each row
        for row in rows:
            email_column = mappings.get('email', 'email')
            if email_column not in row:
                continue
                
            email = row[email_column]
            if not email or not str(email).strip():
                skipped_count += 1
                continue
            
            # Get mapped fields
            first_name = row.get(mappings.get('first_name', 'first_name'), '') or ''
            last_name = row.get(mappings.get('last_name', 'last_name'), '') or ''
            
            subscriber, created = Subscriber.objects.get_or_create(
                email=str(email).strip(),
                defaults={
                    'first_name': str(first_name).strip() if first_name else '',
                    'last_name': str(last_name).strip() if last_name else '',
                    'is_active': True
                }
            )
            
            # Add to list if not already in it
            if subscriber_list not in subscriber.lists.all():
                subscriber.lists.add(subscriber_list)
            
            # Handle custom fields
            for column in columns or row.keys():
                if column not in [email_column, mappings.get('first_name'), mappings.get('last_name')]:
                    value = row.get(column)
                    if not value or not str(value).strip():
                        continue
                        
                    field, field_created = CustomField.objects.get_or_create(
                        user=request.user,
                        key=column.lower().replace(' ', '_'),
                        defaults={'name': column}
                    )
                    
                    CustomValue.objects.update_or_create(
                        subscriber=subscriber,
                        field=field,
                        defaults={'value': str(value).strip()}
                    )
            
            imported_count += 1
        
        return Response({
            'message': _('Successfully imported %(imported)d subscribers (%(skipped)d skipped)') % {
                'imported': imported_count,
                'skipped': skipped_count
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=400)

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_file(request):
    """Validate the uploaded file and return column names."""
    file = request.FILES.get('file')
    if not file:
        return Response({'error': _('No file provided')}, status=400)
    
    try:
        # Read first few rows to get columns
        if file.name.endswith('.csv'):
            file.seek(0)  # Reset file pointer
            decoded_file = file.read().decode('utf-8-sig')
            reader = csv.DictReader(decoded_file.splitlines())
            columns = list(reader.fieldnames or [])
            # Get first 5 rows for preview
            preview = []
            for i, row in enumerate(reader):
                if i >= 5:
                    break
                preview.append(row)
        elif file.name.endswith(('.xls', '.xlsx')):
            workbook = load_workbook(filename=file, read_only=True, data_only=True)
            worksheet = workbook.active
            columns = []
            preview = []
            
            for idx, row in enumerate(worksheet.iter_rows(values_only=True)):
                if idx == 0:
                    columns = [str(cell) if cell else f'Column_{i+1}' for i, cell in enumerate(row)]
                elif idx <= 5:
                    row_dict = {}
                    for i, cell in enumerate(row):
                        if i < len(columns):
                            row_dict[columns[i]] = cell
                    preview.append(row_dict)
                else:
                    break
            workbook.close()
        else:
            return Response({'error': _('Unsupported file format')}, status=400)
        
        return Response({
            'columns': columns,
            'preview': preview
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@login_required
def subscriber_directory(request):
    """Display the subscribers for the authenticated user with search and pagination."""
    query = request.GET.get('q', '').strip()

    subscribers = (
        Subscriber.objects.filter(lists__user=request.user)
        .distinct()
        .prefetch_related('lists', 'lists__campaigns')
        .annotate(
            annotated_full_name=Trim(
                Concat(
                    Coalesce('first_name', Value('')),
                    Value(' '),
                    Coalesce('last_name', Value('')),
                    output_field=CharField(),
                )
            )
        )
        .order_by('-created_at')
    )

    if query:
        subscribers = subscribers.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(annotated_full_name__icontains=query)
        )

    paginator = Paginator(subscribers, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_count': paginator.count,
    }
    return render(request, 'subscribers/list.html', context)


@login_required
def add_subscriber(request):
    """Render the add subscriber page with list and campaign data."""
    from django.urls import reverse
    
    lists = List.objects.filter(user=request.user).order_by('name')
    campaigns = Campaign.objects.filter(user=request.user).prefetch_related('emails').order_by('name')

    campaign_data = [
        {
            'id': str(campaign.id),
            'name': campaign.name,
            'emails': [
                {
                    'id': str(email.id),
                    'subject': email.subject,
                }
                for email in campaign.emails.all()
            ],
        }
        for campaign in campaigns
    ]

    # Build absolute URLs for API endpoints to avoid language prefix issues
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    api_subscriber_create_path = reverse('api-subscriber-create')
    api_send_email_path = reverse('api-send-email')
    api_subscriber_create_url = f"{scheme}://{host}{api_subscriber_create_path}"
    api_send_email_url = f"{scheme}://{host}{api_send_email_path}"

    context = {
        'lists': lists,
        'campaigns': campaigns,
        'campaign_data_json': json.dumps(campaign_data),
        'api_subscriber_create_url': api_subscriber_create_url,
        'api_send_email_url': api_send_email_url,
    }
    return render(request, 'subscribers/add.html', context)


@login_required
def export_subscribers_csv(request):
    """Export all subscribers to CSV file."""
    # Get all subscribers for the user
    subscribers = (
        Subscriber.objects.filter(lists__user=request.user)
        .distinct()
        .prefetch_related('lists')
        .order_by('-created_at')
    )
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="subscribers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Email',
        'First Name',
        'Last Name',
        'Full Name',
        'Lists',
        'Campaigns',
        'Status',
        'Confirmed',
        'Joined Date'
    ])
    
    # Write subscriber data
    for subscriber in subscribers:
        # Get lists as comma-separated string
        lists = ', '.join([list_obj.name for list_obj in subscriber.lists.all()])
        
        # Get campaigns from all lists
        campaign_names = []
        for list_obj in subscriber.lists.all():
            for campaign in list_obj.campaigns.filter(user=request.user):
                if campaign.name not in campaign_names:
                    campaign_names.append(campaign.name)
        campaigns = ', '.join(campaign_names)
        
        # Write row
        writer.writerow([
            subscriber.email,
            subscriber.first_name or '',
            subscriber.last_name or '',
            subscriber.full_name or '',
            lists,
            campaigns,
            'Active' if subscriber.is_active else 'Inactive',
            'Yes' if subscriber.confirmed else 'No',
            subscriber.created_at.strftime('%Y-%m-%d %H:%M:%S') if subscriber.created_at else ''
        ])
    
    return response