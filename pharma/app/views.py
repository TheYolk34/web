from django.shortcuts import render, get_object_or_404, redirect
from .models import Illness, Drug, DrugIllness
from django.db import connection

def add_illness_to_drug(request, illness_id):
    illness = get_object_or_404(Illness, id=illness_id)
    user = request.user

    try:
        drug = Drug.objects.get(creator=user, status='dr')
    except Drug.DoesNotExist:
        drug = Drug.objects.create(creator=user, status='dr')

    drug_illness, created = DrugIllness.objects.get_or_create(drug=drug, illness=illness)
    drug_illness.save()

    return redirect('index')

def delete_drug(request, drug_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_drug SET status = 'del' WHERE id = %s", [drug_id])
    
    return redirect('index')

def index(request):
    user = request.user
    illness_name = request.GET.get('illness')
    first_drug = Drug.objects.first()
    count_illnesses = DrugIllness.objects.filter(drug=first_drug).count() if first_drug else 0
    curr_drug = Drug.objects.filter(creator=user, status='dr').first()
    if curr_drug:
        drug_info = {
            'id': curr_drug.id,
            'count': Drug.objects.get_total_illnesses(curr_drug)
        }
    else:
        drug_info = None

    if illness_name:
        illnesses = Illness.objects.filter(spread__icontains=illness_name)
        return render(request, 'index.html', {
            "illnesses": illnesses,
            'query': illness_name,
            "drug": drug_info
        })
    else:
        illnesses = Illness.objects.all()
        return render(request, 'index.html', {"illnesses": illnesses, "drug": drug_info})
    
def illness(request, illness_id):
    illness = get_object_or_404(Illness, id=illness_id)
    return render(request, 'illness.html', {"illness": illness})

def drug(request, drug_id):
    try:
        curr_drug = Drug.objects.get(id=drug_id)
        if curr_drug.status == 'del':
            raise Drug.DoesNotExist 
    except Drug.DoesNotExist:
        return render(request, 'drug.html', {"error_message": "Нельзя просмотреть лекарство."})

    drug_data = get_object_or_404(Drug, id=drug_id)

    selected_illnesses = Illness.objects.filter(drugillness__drug=drug_data)

    trials = {}
    for drug_illness in DrugIllness.objects.filter(drug=drug_data):
        trials[drug_illness.illness.id] = drug_illness.trial

    context = {
        'drug': drug_data,
        'drug_name': drug_data.name,
        'drug_description': drug_data.description,
        'selected_illnesses': selected_illnesses,
        'illness_result': trials
    }

    return render(request, 'drug.html', context)