from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
import pandas as pd
from .models import List, Subscriber, CustomField, CustomValue
from campaigns.models import Campaign

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
        
        # Get field mappings
        mappings = request.POST.get('mappings', {})
        if not isinstance(mappings, dict):
            mappings = {}
        
        subscriber_list = List.objects.get(id=list_id, user=request.user)
        
        # Process each row
        for _, row in df.iterrows():
            email = row.get(mappings.get('email', 'email'))
            if not email:
                continue
                
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': row.get(mappings.get('first_name', 'first_name'), ''),
                    'last_name': row.get(mappings.get('last_name', 'last_name'), ''),
                    'is_active': True
                }
            )
            
            # Add to list if not already in it
            if subscriber_list not in subscriber.lists.all():
                subscriber.lists.add(subscriber_list)
            
            # Handle custom fields
            for column in df.columns:
                if column not in ['email', 'first_name', 'last_name']:
                    field, _ = CustomField.objects.get_or_create(
                        user=request.user,
                        key=column.lower().replace(' ', '_'),
                        defaults={'name': column}
                    )
                    CustomValue.objects.update_or_create(
                        subscriber=subscriber,
                        field=field,
                        defaults={'value': str(row[column])}
                    )
        
        messages.success(request, _('Subscribers imported successfully'))
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, _('Error importing subscribers: {}').format(str(e)))
        return redirect('subscribers:import')