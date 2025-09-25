from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Campaign, Email
from .serializers import CampaignSerializer, EmailSerializer
from subscribers.models import List
import pandas as pd
import io

@login_required
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def campaign_list_create(request):
    """List all campaigns or create a new one."""
    if request.method == 'GET':
        campaigns = Campaign.objects.filter(user=request.user)
        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data)
    
    serializer = CampaignSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        campaign = serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@login_required
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def campaign_detail(request, campaign_id):
    """Get, update or delete a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if request.method == 'GET':
        serializer = CampaignSerializer(campaign)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CampaignSerializer(campaign, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        campaign.delete()
        return Response(status=204)

@login_required
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def email_list_create(request, campaign_id):
    """List all emails in a campaign or create a new one."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if request.method == 'GET':
        emails = campaign.emails.all().order_by('order')
        serializer = EmailSerializer(emails, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Set the order to be the next available number
        data = request.data.copy()
        data['order'] = campaign.emails.count()
        # Remove data['campaign'] = campaign.id
        serializer = EmailSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            email = serializer.save(campaign=campaign)
            return Response(serializer.data, status=201)
        return Response({'error': 'Validation failed', 'details': serializer.errors}, status=400)

@login_required
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def email_detail(request, campaign_id, email_id):
    """Get, update or delete an email."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    email = get_object_or_404(Email, id=email_id, campaign=campaign)
    
    if request.method == 'GET':
        serializer = EmailSerializer(email)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = EmailSerializer(email, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'error': 'Validation failed', 'details': serializer.errors}, status=400)
    
    elif request.method == 'DELETE':
        email.delete()
        return Response(status=204)

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_email(request, campaign_id, email_id):
    """Send a test email."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    email = get_object_or_404(Email, id=email_id, campaign=campaign)
    
    test_email = request.data.get('email')
    if not test_email:
        return Response({'error': _('Email address is required')}, status=400)
    
    variables = request.data.get('variables', {})
    
    # Send test email
    from .tasks import send_test_email
    send_test_email.delay(str(email.id), test_email, variables)
    
    return Response({'message': _('Test email sent successfully')})

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email(request, campaign_id, email_id):
    """Send an email to a specific subscriber."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    email = get_object_or_404(Email, id=email_id, campaign=campaign)
    
    subscriber_email = request.data.get('email')
    if not subscriber_email:
        return Response({'error': _('Email address is required')}, status=400)
    
    variables = request.data.get('variables', {})
    
    # Send email
    from .tasks import send_single_email
    send_single_email.delay(str(email.id), subscriber_email, variables)
    
    return Response({'message': _('Email sent successfully')})

@login_required
def campaign_edit(request, campaign_id):
    """Edit campaign and its templates."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    emails = campaign.emails.all().order_by('order')
    lists = List.objects.filter(user=request.user)
    return render(request, 'campaigns/edit.html', {
        'campaign': campaign,
        'emails': emails,
        'lists': lists
    })

@login_required
def campaign_template(request, campaign_id=None):
    """Render template creation/edit page."""
    campaign = None
    template = None
    if campaign_id:
        campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
        template_id = request.GET.get('template_id')
        if template_id:
            template = get_object_or_404(Email, id=template_id, campaign=campaign)
    
    # Get user's footers
    from analytics.models import EmailFooter
    user_footers = EmailFooter.objects.filter(user=request.user)
    
    context = {
        'campaign': campaign,
        'template': template,
        'user_footers': user_footers,
        'wait_units': [
            ('minutes', _('Minutes')),
            ('hours', _('Hours')),
            ('days', _('Days')),
            ('weeks', _('Weeks')),
            ('months', _('Months'))
        ],
        'first_name': '{{first_name}}',
        'last_name': '{{last_name}}',
        'full_name': '{{full_name}}',
        'email': '{{email}}'
    }
    return render(request, 'campaigns/template.html', context)

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_campaign(request, campaign_id):
    """Activate a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if campaign.emails.count() == 0:
        return Response({
            'error': _('Cannot activate a campaign with no emails')
        }, status=400)
    
    campaign.is_active = True
    campaign.save()
    
    return Response({
        'message': _('Campaign activated successfully')
    })

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_campaign(request, campaign_id):
    """Deactivate a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    campaign.is_active = False
    campaign.save()
    
    return Response({
        'message': _('Campaign deactivated successfully')
    })

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reorder_emails(request, campaign_id):
    """Reorder emails in a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    email_id = request.data.get('email_id')
    direction = request.data.get('direction')  # 'up' or 'down'
    
    if not email_id or not direction:
        return Response({'error': _('Email ID and direction are required')}, status=400)
    
    try:
        email = Email.objects.get(id=email_id, campaign=campaign)
    except Email.DoesNotExist:
        return Response({'error': _('Email not found')}, status=404)
    
    emails = list(campaign.emails.all().order_by('order'))
    current_index = None
    
    # Find current email index
    for i, e in enumerate(emails):
        if e.id == email.id:
            current_index = i
            break
    
    if current_index is None:
        return Response({'error': _('Email not found in campaign')}, status=404)
    
    # Determine new index
    if direction == 'up' and current_index > 0:
        new_index = current_index - 1
    elif direction == 'down' and current_index < len(emails) - 1:
        new_index = current_index + 1
    else:
        return Response({'error': _('Cannot move email in that direction')}, status=400)
    
    # Swap orders
    emails[current_index], emails[new_index] = emails[new_index], emails[current_index]
    
    # Update orders
    for i, e in enumerate(emails):
        e.order = i
        e.save(update_fields=['order'])
    
    return Response({'message': _('Email order updated successfully')})

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_contacts(request):
    """Upload contacts from a CSV or Excel file."""
    if 'file' not in request.FILES:
        return Response({'error': _('No file uploaded')}, status=400)
    
    file = request.FILES['file']
    if not file.name.endswith(('.csv', '.xls', '.xlsx')):
        return Response({'error': _('Invalid file format. Please upload a CSV or Excel file.')}, status=400)
    
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = ['email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({
                'error': _('Missing required columns: {}').format(', '.join(missing_columns))
            }, status=400)
        
        # Process the data
        contacts = []
        for _, row in df.iterrows():
            contact = {
                'email': row['email'],
                'first_name': row.get('first_name', ''),
                'last_name': row.get('last_name', ''),
                'full_name': row.get('full_name', '')
            }
            contacts.append(contact)
        
        return Response({
            'message': _('File processed successfully'),
            'contacts': contacts
        })
        
    except Exception as e:
        return Response({
            'error': _('Error processing file: {}').format(str(e))
        }, status=400)

@login_required
def campaign_create(request):
    """Render campaign creation page."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        subscriber_list_id = request.POST.get('subscriber_list')
        
        if name:
            subscriber_list = None
            if subscriber_list_id:
                subscriber_list = get_object_or_404(List, id=subscriber_list_id, user=request.user)
            
            campaign = Campaign.objects.create(
                user=request.user,
                name=name,
                description=description or '',
                subscriber_list=subscriber_list
            )
            
            messages.success(request, _('Campaign created successfully!'))
            return redirect('campaigns:edit', campaign_id=campaign.id)
        else:
            messages.error(request, _('Please provide a campaign name.'))
    
    return render(request, 'campaigns/create.html', {
        'subscriber_lists': List.objects.filter(user=request.user)
    })