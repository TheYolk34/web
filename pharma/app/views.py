from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from .models import Illness, Drug, DrugIllness

def add_illness_to_drug(request, illness_id):
    illness = get_object_or_404(Illness, id=illness_id)
    user = request.user

    with connection.cursor() as cursor:
        # Попробуем получить drug, создаём если его нет
        cursor.execute("SELECT id FROM app_drug WHERE creator_id = %s AND status = 'dr'", [user.id])
        drug = cursor.fetchone()
        
        if drug is None:
            cursor.execute("INSERT INTO app_drug (creator_id, status) VALUES (%s, 'dr') RETURNING id", [user.id])
            drug_id = cursor.fetchone()[0]
        else:
            drug_id = drug[0]
        
        # Получаем или создаем связь drug-illness
        cursor.execute("SELECT id FROM app_drugillness WHERE drug_id = %s AND illness_id = %s", [drug_id, illness.id])
        drug_illness = cursor.fetchone()
        
        if drug_illness is None:
            cursor.execute("INSERT INTO app_drugillness (drug_id, illness_id) VALUES (%s, %s)", [drug_id, illness.id])

    return redirect('index')

def delete_drug(request, drug_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_drug SET status = 'del' WHERE id = %s", [drug_id])
    
    return redirect('index')

def index(request):
    user = request.user
    illness_name = request.GET.get('illness')
    first_drug = None
    count_illnesses = 0
    curr_drug = None
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM app_drug WHERE creator_id = %s AND status = 'dr' LIMIT 1", [user.id])
        curr_drug = cursor.fetchone()

        if curr_drug:
            drug_id = curr_drug[0]
            cursor.execute("SELECT COUNT(*) FROM app_drugillness WHERE drug_id = %s", [drug_id])
            count_illnesses = cursor.fetchone()[0]
        
        if illness_name:
            cursor.execute("SELECT * FROM app_illness WHERE spread ILIKE %s", ['%' + illness_name + '%'])
            illnesses = cursor.fetchall()
            return render(request, 'index.html', {
                "illnesses": illnesses,
                'query': illness_name,
                "drug": {
                    'id': drug_id,
                    'count': count_illnesses
                } if curr_drug else None
            })
        else:
            cursor.execute("SELECT * FROM app_illness")
            illnesses = cursor.fetchall()
            return render(request, 'index.html', {
                "illnesses": illnesses,
                "drug": {
                    'id': drug_id,
                    'count': count_illnesses
                } if curr_drug else None
            })

def illness(request, illness_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM app_illness WHERE id = %s", [illness_id])
        illness_data = cursor.fetchone()

        if not illness_data:
            return render(request, '404.html', status=404)

    return render(request, 'illness.html', {"illness": illness_data})

def drug(request, drug_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM app_drug WHERE id = %s", [drug_id])
        curr_drug = cursor.fetchone()

        if curr_drug is None or curr_drug[status] == 'del':
            return render(request, 'drug.html', {"error_message": "Нельзя просмотреть лекарство."})

        # Данные о лекарстве
        drug_data = curr_drug
        
        cursor.execute("SELECT * FROM app_illness WHERE id IN (SELECT illness_id FROM app_drugillness WHERE drug_id = %s)", [drug_id])
        selected_illnesses = cursor.fetchall()

        trials = {}
        cursor.execute("SELECT illness_id, trial FROM app_drugillness WHERE drug_id = %s", [drug_id])
        drug_illnesses = cursor.fetchall()
        for drug_illness in drug_illnesses:
            trials[drug_illness[0]] = drug_illness[1]

        context = {
            'drug': drug_data,
            'drug_name': drug_data.name,
            'drug_description': drug_data.description,
            'selected_illnesses': selected_illnesses,
            'illness_result': trials
        }

    return render(request, 'drug.html', context)