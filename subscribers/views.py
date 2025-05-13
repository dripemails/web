from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import pandas as pd
from .models import List, Subscriber, CustomField, CustomValue
from campaigns.models import Campaign
import json

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
def process_import(request):
    """Process the uploaded file and import subscribers."""
    if request.method != 'POST':
        return redirect('subscribers:import')
    
    file = request.FILES.get('file')
    list_id = request.POST.get('list_id')
    campaign_id = request.POST.get('campaign_id')
    mappings = json.loads(request.POST.get('mappings', '{}'))
    
    if not file or not list_id:
        messages.error(request, _('Please provide both a file and select a list'))
        return redirect('subscribers:import')
    
    try:
        # Read file based on extension
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            messages.error(request, _('Unsupported file format'))
            return redirect('subscribers:import')
        
        subscriber_list = List.objects.get(id=list_id, user=request.user)
        campaign = None
        if campaign_id:
            campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        
        imported_count = 0
        skipped_count = 0
        
        # Process each row
        for _, row in df.iterrows():
            email_column = mappings.get('email', 'email')
            if email_column not in row:
                continue
                
            email = row[email_column]
            if not email or pd.isna(email):
                skipped_count += 1
                continue
            
            # Get mapped fields
            first_name = row.get(mappings.get('first_name', 'first_name'), '')
            last_name = row.get(mappings.get('last_name', 'last_name'), '')
            
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name if not pd.isna(first_name) else '',
                    'last_name': last_name if not pd.isna(last_name) else '',
                    'is_active': True
                }
            )
            
            # Add to list if not already in it
            if subscriber_list not in subscriber.lists.all():
                subscriber.lists.add(subscriber_list)
            
            # Handle custom fields
            for column in df.columns:
                if column not in [email_column, mappings.get('first_name'), mappings.get('last_name')]:
                    value = row[column]
                    if pd.isna(value):
                        continue
                        
                    field, _ = CustomField.objects.get_or_create(
                        user=request.user,
                        key=column.lower().replace(' ', '_'),
                        defaults={'name': column}
                    )
                    
                    CustomValue.objects.update_or_create(
                        subscriber=subscriber,
                        field=field,
                        defaults={'value': str(value)}
                    )
            
            imported_count += 1
        
        messages.success(
            request,
            _('Successfully imported %(imported)d subscribers (%(skipped)d skipped)') % {
                'imported': imported_count,
                'skipped': skipped_count
            }
        )
        
        # If campaign was selected, redirect to campaign edit page
        if campaign:
            return redirect('campaigns:edit', campaign_id=campaign.id)
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, _('Error importing subscribers: {}').format(str(e)))
        return redirect('subscribers:import')

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
            df = pd.read_csv(file, nrows=5)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file, nrows=5)
        else:
            return Response({'error': _('Unsupported file format')}, status=400)
        
        return Response({
            'columns': list(df.columns),
            'preview': df.head().to_dict('records')
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)